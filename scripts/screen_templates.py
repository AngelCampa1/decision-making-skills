"""Screen the templates a study is about to register, one model, no skill.

A template a model answers at chance measures nothing about a skill, and the
2026-08-27 five-arm study registered ten templates without asking which of them
a 1.7B model could read at all. This runs the ``off`` arm over a fixed number
of items per template and prints, per template, what a study would want to know
before it commits to that template: accuracy, the share of answers the scorer
could parse, and informedness J, which is zero for any constant-answer policy
and is the number that says whether the model discriminates rather than
whether it happens to agree with the key's majority.

J is defined on a two-option key only. A template with more options gets
accuracy and parse rate and a blank where J would go.

Every call goes through :func:`~decision_evals.runner.run_arm` into a
checkpoint under ``results/screens/``, which ``.gitignore`` keeps out of the
tree and ``provenance.WORKING_DIRS`` keeps out of the run gate. What a screen
showed goes in ``notebook/``. Resumable: a second invocation against the same
directory skips what is already answered.

Usage::

    python scripts/screen_templates.py --target ollama/qwen3:1.7b --seed 10007
    python scripts/screen_templates.py --templates-root datasets/templates,datasets/templates-hard
    python scripts/screen_templates.py                     # mock venue, no model
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "evals" / "src"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from decision_evals.budget import BudgetLedger  # noqa: E402
from decision_evals.evolution.run import DEFAULT_TEMPLATES_ROOT, _rotated  # noqa: E402
from decision_evals.evolution.solo import Solo  # noqa: E402
from decision_evals.evolution.venues import MOCK_MODEL, call_fn, venue_for  # noqa: E402
from decision_evals.generators import generate, load_all, parse_roots  # noqa: E402
from decision_evals.generators.generate import Item  # noqa: E402
from decision_evals.runner import RunRecord, load_records, run_arm  # noqa: E402
from decision_evals.solvers.arms import build_arm  # noqa: E402
from decision_evals.stats.signal import DegenerateSignalError, informedness  # noqa: E402

#: Where a screen's checkpoint goes, under the repository root.
SCREENS_ROOT = "results/screens"

#: The study's resume key, for the same reason the study uses it: the checkpoint
#: holds several seeds and ``item_id`` carries none of them.
RESUME_FIELDS = ("item_id", "arm", "candidate_sha", "seed")


@dataclass(frozen=True, slots=True)
class TemplateReading:
    """What one template looked like to one model with no document in front of it."""

    template_id: str
    asked: int
    parsed: int
    correct: int
    #: ``None`` for a template whose key has more than two options, or whose
    #: parsed answers hold one class of the key only.
    informedness: float | None

    @property
    def accuracy(self) -> float:
        """Correct over asked. An unparsed answer is a wrong one here, as it is
        in the study."""
        return self.correct / self.asked if self.asked else 0.0

    @property
    def parse_rate(self) -> float:
        return self.parsed / self.asked if self.asked else 0.0


def items_per_template(roots: tuple[Path, ...], seed: int, count: int) -> dict[str, list[Item]]:
    """``count`` items of every template at ``seed``, spread across its strata.

    The first ``count`` of a template's items in generation order are
    variant-major, so a small count would read one variant across every
    stratum. The rotated order the search uses spreads a prefix across the
    strata instead, and it is reused here so a screen of eight items per
    template is eight strata rather than eight rewordings of one.
    """
    return {
        template.template_id: _rotated([list(generate(template, seed))])[:count]
        for template in load_all(roots)
    }


def read(records: list[RunRecord], items: dict[str, list[Item]]) -> list[TemplateReading]:
    """Per-template numbers from a checkpoint, in template order.

    J is computed over the parsed rows only, because
    :func:`~decision_evals.stats.signal.informedness` reads an unparsed answer
    as a confident negative, and the parse rate beside it says how many rows
    that left out.
    """
    by_template: dict[str, list[RunRecord]] = {template_id: [] for template_id in items}
    for record in records:
        if record.template_id in by_template:
            by_template[record.template_id].append(record)

    readings: list[TemplateReading] = []
    for template_id, rows in by_template.items():
        options = items[template_id][0].options if items[template_id] else []
        parsed = [row for row in rows if row.parse_status == "parsed"]
        signal: float | None = None
        if len(options) == 2 and parsed:
            try:
                signal = informedness(
                    [row.expected for row in parsed],
                    [row.parsed for row in parsed],
                    positive=options[0],
                ).informedness
            except DegenerateSignalError:
                signal = None
        readings.append(
            TemplateReading(
                template_id=template_id,
                asked=len(rows),
                parsed=len(parsed),
                correct=sum(1 for row in rows if row.correct),
                informedness=signal,
            )
        )
    return readings


def render(readings: list[TemplateReading]) -> str:
    """The table a reader compares templates on."""
    lines = [f"{'template':32s} {'asked':>5s} {'acc':>6s} {'parse':>6s} {'J':>7s}"]
    for reading in readings:
        j = "" if reading.informedness is None else f"{reading.informedness:+.3f}"
        lines.append(
            f"{reading.template_id:32s} {reading.asked:5d} {reading.accuracy:6.3f} "
            f"{reading.parse_rate:6.3f} {j:>7s}"
        )
    return "\n".join(lines)


def screen_dir(repo_root: Path, git_sha: str, on: date | None = None) -> Path:
    """``results/screens/<date>-<sha7>-templates``, the shape every run directory has."""
    return repo_root / SCREENS_ROOT / f"{(on or date.today()).isoformat()}-{git_sha[:7]}-templates"


def run(
    *,
    target: str,
    roots: tuple[Path, ...],
    seed: int,
    per_template: int,
    out: Path,
    max_tokens: int = 0,
    num_ctx: int = 0,
    max_calls: int = 10_000,
    max_seconds: float = 86_400.0,
) -> list[TemplateReading]:
    """Answer every item with the ``off`` arm and read the checkpoint back.

    ``out`` is the screen directory. The checkpoint is ``records.jsonl`` inside
    it and the manifest beside it says what was asked, before the first call.
    """
    venue = venue_for(target)
    items = items_per_template(roots, seed, per_template)
    rows = [item for group in items.values() for item in group]
    out.mkdir(parents=True, exist_ok=True)
    (out / "run.json").write_text(
        json.dumps(
            {
                "target_model": target,
                "templates_root": [str(root) for root in roots],
                "seed": seed,
                "items_per_template": per_template,
                "templates": sorted(items),
                "items": len(rows),
                "max_tokens": max_tokens,
                "num_ctx": num_ctx,
                "arm": "off",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    ledger = BudgetLedger(
        limit_usd=0.0, bills=venue.bills, limit_calls=max_calls, limit_seconds=max_seconds
    )
    checkpoint = out / "records.jsonl"
    with Solo(REPO_ROOT / "results" / "evolution", venue.model, out.name):
        run_arm(
            rows,
            build_arm("off"),
            model=venue.model,
            checkpoint=checkpoint,
            call=call_fn(venue, max_tokens=max_tokens or None, num_ctx=num_ctx or None),
            ledger=ledger,
            resume_fields=RESUME_FIELDS,
        )
    readings = read(load_records(checkpoint), items)
    (out / "summary.json").write_text(
        json.dumps(
            [{**asdict(r), "accuracy": r.accuracy, "parse_rate": r.parse_rate} for r in readings],
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return readings


def _head(repo_root: Path) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo_root, capture_output=True, text=True, check=False
    )
    if completed.returncode != 0:
        raise SystemExit("not a git repository, so no commit can name the screen directory")
    return completed.stdout.strip()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--target", default=MOCK_MODEL, help="The model, as the venues name it.")
    parser.add_argument(
        "--templates-root",
        default=DEFAULT_TEMPLATES_ROOT,
        help="Template directory, or a comma-separated list of them.",
    )
    parser.add_argument("--seed", type=int, default=10_000, help="The corpus seed to draw at.")
    parser.add_argument(
        "--items-per-template", type=int, default=28, help="Items asked of every template."
    )
    parser.add_argument("--max-tokens", type=int, default=0, help="Output cap per call.")
    parser.add_argument("--num-ctx", type=int, default=0, help="Context window, Ollama only.")
    parser.add_argument("--max-calls", type=int, default=10_000, help="Call cap.")
    parser.add_argument("--max-seconds", type=float, default=86_400.0, help="Wall-clock cap.")
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help=f"Screen directory. Defaults to {SCREENS_ROOT}/<date>-<sha7>-templates.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.items_per_template < 1:
        raise SystemExit("--items-per-template is at least 1")
    out = args.out or screen_dir(REPO_ROOT, _head(REPO_ROOT))
    readings = run(
        target=args.target,
        roots=parse_roots(args.templates_root, base=REPO_ROOT),
        seed=args.seed,
        per_template=args.items_per_template,
        out=out,
        max_tokens=args.max_tokens,
        num_ctx=args.num_ctx,
        max_calls=args.max_calls,
        max_seconds=args.max_seconds,
    )
    print(render(readings))
    print(f"\nrecords  {out / 'records.jsonl'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
