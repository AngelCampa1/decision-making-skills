"""The five-arm study: several bodies, one item set, one placebo to beat.

A search produces a body. This is what says whether the body is worth anything,
and the shape it takes comes from what the surveyed engines do not do. They
report one number per candidate on the split they optimised against. Here the
items come from seeds no search could reach, every arm answers the *same* items
so the comparison is paired, and the arm that matters is not "no skill" but a
document matched to the skill on word count and structure. A gain over nothing is
not evidence that a skill helped; it is evidence that a paragraph helped.

Two item sets rather than one, and this is the part the 2026-08-27 searches
forced. Both winners wrote their training scenarios' decision rules into the
skill, and a rule survives a change of seed intact, so fresh instances of a
*seen* scenario measure memorisation and fresh instances of an *unseen* one
measure transfer. Reporting them pooled would average the two into a number
that answers neither question. They are never pooled.

Three things about how the calls are scheduled, each a correction to the
2026-08-27 run. Every arm writes its own ``records-<label>.jsonl``, which is the
file :func:`~decision_evals.figures.load_readings` reads the arm's name off; the
published run's per-arm files were split by hand from one checkpoint. Items run
in chunks and every arm answers a chunk before the next chunk starts, so no arm
runs as one block against whatever the venue was doing that hour. And a study
can run every arm more than once, each pass into its own checkpoint, so the
arms' repeatability is measured on the arms and not inferred from one repeat of
the control.
"""

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Final

from decision_evals.budget import BudgetLedger
from decision_evals.evolution.checkpoints import RunPaths, paths_for, run_name, write_manifest
from decision_evals.evolution.holdout import POOLS, census
from decision_evals.evolution.lineage import body_sha
from decision_evals.evolution.run import DEFAULT_TEMPLATES_ROOT, items_for
from decision_evals.evolution.solo import Solo
from decision_evals.evolution.venues import Venue, assert_cap_fits, call_fn, context_window
from decision_evals.generators import parse_roots
from decision_evals.generators.audit import corpus_fingerprint
from decision_evals.generators.generate import Item
from decision_evals.runner import CallFn, RunRecord, load_records, run_arm
from decision_evals.solvers.arms import ArmName, ArmPrompt, build_arm
from decision_evals.stats.multiplicity import holm
from decision_evals.stats.paired import mcnemar_exact

#: The arm every arm in the registered family is tested against. Not ``off``:
#: a skill that beats an
#: empty prompt has shown that a document helps, which is a claim about
#: documents.
CONTROL: Final = "placebo"

#: Columns that identify one call here. Wider than the published default because
#: this checkpoint holds several bodies over several seeds, and ``(item_id, arm)``
#: names a set of calls rather than one -- two candidate arms both record
#: ``arm="candidate"`` and are told apart only by ``candidate_sha``.
RESUME_FIELDS: Final = ("item_id", "arm", "candidate_sha", "seed")

#: The A/A's own checkpoint. A second pass into the main one would be skipped by
#: resume -- correctly, since the key is already there -- and report agreement it
#: never measured.
AA_RECORDS: Final = "records-aa.jsonl"

#: How the calls are ordered, written to the manifest so a reader of the
#: records knows the arms interleaved. The 2026-08-27 run has no such line
#: because it ran arm-major.
ORDERING: Final = "item-major"

#: What an arm may be called. The label is a file name, so it is one token, and
#: it may not be ``aa``, which :data:`AA_RECORDS` already spells.
_LABEL: Final = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")


class StudyError(RuntimeError):
    """A study cannot be set up, or its result cannot be trusted."""


@dataclass(frozen=True, slots=True)
class Arm:
    """One arm, as a reader sees it and as the record stores it.

    ``label`` is for people and ``kind`` is what
    :func:`~decision_evals.solvers.arms.build_arm` renders. They differ because
    two arms of this study are both ``candidate``: a body no human wrote reaches
    the model through one code path whichever engine wrote it, on purpose, so
    that authorship is not confounded with delivery.

    The label is also the arm's file name, ``records-<label>.jsonl``, and the
    figures read the arm back off that name. So it is one token, and it is
    never ``aa``.

    Raises:
        StudyError: A label that cannot name a file, or one the A/A already uses.
    """

    label: str
    kind: ArmName
    body: str = ""

    def __post_init__(self) -> None:
        if not _LABEL.match(self.label) or self.label == "aa":
            raise StudyError(
                f"arm label {self.label!r} cannot name a checkpoint. A label is one token of "
                "letters, digits, `_`, `.` or `-`, and `aa` is the A/A pass."
            )

    @property
    def sha(self) -> str | None:
        """The body's hash, which is what separates two candidate arms."""
        return body_sha(self.body) if self.body else None


@dataclass(frozen=True, slots=True)
class ItemSet:
    """One question the study asks, and the items that answer it."""

    label: str
    templates: tuple[str, ...]
    seeds: tuple[int, ...]

    def items(self, root: Path | Sequence[Path] | None = None) -> list[Item]:
        """The set's items, drawn from ``root`` or the published corpus."""
        return items_for(self.seeds, templates=set(self.templates), root=root)


@dataclass(frozen=True, slots=True)
class StudyRequest:
    """Everything the study is told before it starts, written to its manifest."""

    target_model: str
    sets: tuple[ItemSet, ...]
    #: A second pass of the control arm, into its own checkpoint. Two scorings of
    #: one body under identical conditions should not differ, and if they do the
    #: study is measuring the venue rather than the arms.
    run_aa: bool = True
    num_ctx: int = 0
    max_tokens: int = 0
    max_calls: int = 10_000
    max_seconds: float = 86_400.0
    alpha: float = 0.05
    slug: str = ""
    #: How many times every arm answers every item. Pass 1 is the study, and
    #: the registered comparisons read it alone. Later passes measure how far
    #: an arm agrees with itself, each into ``pass-<k>/``.
    passes: int = 1
    #: Items per chunk. Every arm answers a chunk before the next one starts.
    chunk: int = 8
    #: Which corpus the items come from, as the comma-separated list
    #: :func:`~decision_evals.generators.parse_roots` reads, relative to the
    #: repository root and recorded as written.
    templates_root: str = DEFAULT_TEMPLATES_ROOT

    def __post_init__(self) -> None:
        if not self.sets:
            raise StudyError("a study needs at least one item set")
        labels = [item_set.label for item_set in self.sets]
        if len(set(labels)) != len(labels):
            raise StudyError(f"item sets need distinct labels, got {labels}")
        for item_set in self.sets:
            outside = [seed for seed in item_set.seeds if seed not in POOLS["holdout"]]
            if outside:
                raise StudyError(
                    f"{item_set.label} draws seed(s) {outside}, which are not holdout "
                    "seeds. A study scored on anything a search could reach is reporting "
                    "training accuracy, which is the practice this whole design exists "
                    "to test."
                )
        if self.passes < 1:
            raise StudyError(f"a study runs at least one pass, got {self.passes}")
        if self.chunk < 1:
            raise StudyError(f"a chunk holds at least one item, got {self.chunk}")


@dataclass(frozen=True, slots=True)
class Comparison:
    """One arm against the control, on one item set."""

    item_set: str
    arm: str
    n_pairs: int
    accuracy: float
    control_accuracy: float
    arm_only: int
    control_only: int
    p_value: float
    adjusted: float = 1.0
    rejected: bool = False

    @property
    def effect(self) -> float:
        """Accuracy difference, arm minus control."""
        return self.accuracy - self.control_accuracy


@dataclass(frozen=True, slots=True)
class SetResult:
    """Everything the study says about one item set."""

    label: str
    n_items: int
    accuracy: dict[str, float]
    comparisons: tuple[Comparison, ...] = ()


@dataclass(frozen=True, slots=True)
class PassAgreement:
    """Pass 1 of one arm against a later pass of the same arm, on one set.

    Item-level, on correctness. ``identical`` counts the questions both passes
    got right or both got wrong, ``different`` the rest, and the p-value is a
    two-sided exact McNemar over the pairs, which reads whether the second pass
    drifted in one direction and says nothing about how much it flipped.
    """

    pass_index: int
    n_pairs: int
    identical: int
    different: int
    p_value: float


@dataclass(frozen=True, slots=True)
class ArmPasses:
    """One arm's accuracy on each pass, and each later pass against the first."""

    arm: str
    accuracy: tuple[float, ...]
    agreement: tuple[PassAgreement, ...] = ()


@dataclass(frozen=True, slots=True)
class SetPasses:
    """The repeat passes of one item set, arm by arm."""

    label: str
    arms: tuple[ArmPasses, ...]


@dataclass(frozen=True, slots=True)
class StudyResult:
    """What a finished study leaves behind."""

    paths: RunPaths
    sets: tuple[SetResult, ...]
    aa: Comparison | None = None
    stop_reason: str = ""
    records: int = 0
    lineage: list[object] = field(default_factory=list)
    #: Empty for a one-pass study.
    passes: tuple[SetPasses, ...] = ()


def records_path(root: Path, label: str, pass_index: int = 1) -> Path:
    """Where one arm's records go on one pass.

    Pass 1 is ``records-<label>.jsonl`` in the run directory, which is the
    layout the published run has and the figures read. A later pass is the same
    file under ``pass-<k>/``: a separate checkpoint, because resume keys on
    :data:`RESUME_FIELDS` and carries no pass index, so a second pass into the
    first file would be skipped as already done.
    """
    name = f"records-{label}.jsonl"
    return root / name if pass_index == 1 else root / f"pass-{pass_index}" / name


def load_pass(root: Path, arms: Sequence[Arm], pass_index: int = 1) -> list[RunRecord]:
    """Every arm's records from one pass, in arm order. An arm with no file is
    an arm that never ran, and it is left out rather than invented."""
    records: list[RunRecord] = []
    for arm in arms:
        path = records_path(root, arm.label, pass_index)
        if path.is_file():
            records.extend(load_records(path))
    return records


def _key(record: RunRecord) -> tuple[int, str]:
    """What makes two records the same question. Seed first, because ``item_id``
    carries the template and the stratum and *not* the seed, so the same id names
    a different scenario under a different draw."""
    return (record.seed or 0, record.item_id)


def _arm_of(record: RunRecord, arms: Sequence[Arm]) -> str | None:
    """Which arm a record belongs to, resolved through the body's hash.

    Two candidate arms both record ``arm="candidate"``, so the arm name alone
    cannot separate them and a reader that used it would silently pool two
    engines into one number.
    """
    for arm in arms:
        if record.arm == arm.kind and (record.candidate_sha or None) == arm.sha:
            return arm.label
    return None


def by_arm(
    records: Sequence[RunRecord], arms: Sequence[Arm]
) -> dict[str, dict[tuple[int, str], bool]]:
    """Correctness per arm, keyed by the question rather than by position.

    Later records win, which matters only for a checkpoint that was resumed
    across a change: within one study every ``(arm, question)`` is called once,
    and :data:`RESUME_FIELDS` is what makes that true.
    """
    table: dict[str, dict[tuple[int, str], bool]] = {arm.label: {} for arm in arms}
    for record in records:
        label = _arm_of(record, arms)
        if label is not None:
            table[label][_key(record)] = record.correct
    return table


def compare(
    label: str,
    arm: str,
    outcomes: dict[str, dict[tuple[int, str], bool]],
    *,
    control: str = CONTROL,
) -> Comparison:
    """One arm against the control, on the questions both of them answered.

    Paired on the question, never on order. An arm that is missing an item is
    dropped from *that* comparison rather than from the study, and ``n_pairs``
    says how many were left, because a comparison quietly computed over fewer
    items than its neighbour is the difference nobody notices.

    Raises:
        StudyError: The control arm is absent, or the two share no question.
    """
    if not outcomes.get(control):
        raise StudyError(
            f"no {control!r} answers on record, so there is nothing to compare against. "
            "The emptiness matters more than the absence: `by_arm` seeds a key for every "
            "declared arm, so a control that ran zero items is present and empty rather "
            "than missing, and a check for the key alone would pass it through to a "
            "comparison over nothing."
        )
    shared = sorted(set(outcomes[arm]) & set(outcomes[control]))
    if not shared:
        raise StudyError(f"{arm!r} and {control!r} answered no question in common")
    treatment = [outcomes[arm][key] for key in shared]
    baseline = [outcomes[control][key] for key in shared]
    result = mcnemar_exact(baseline, treatment, alternative="greater")
    return Comparison(
        item_set=label,
        arm=arm,
        n_pairs=len(shared),
        accuracy=sum(treatment) / len(shared),
        control_accuracy=sum(baseline) / len(shared),
        arm_only=sum(1 for t, b in zip(treatment, baseline, strict=True) if t and not b),
        control_only=sum(1 for t, b in zip(treatment, baseline, strict=True) if b and not t),
        p_value=result.p_value,
    )


def _in_set(records: Sequence[RunRecord], item_set: ItemSet) -> list[RunRecord]:
    """The records one item set owns: its seeds and its templates, both."""
    seeds = set(item_set.seeds)
    templates = set(item_set.templates)
    return [
        record
        for record in records
        if (record.seed or 0) in seeds and record.template_id in templates
    ]


def _accuracy(outcomes: dict[str, dict[tuple[int, str], bool]]) -> dict[str, float]:
    """Per-arm accuracy, and zero for an arm that answered nothing."""
    return {
        label: (sum(answers.values()) / len(answers) if answers else 0.0)
        for label, answers in outcomes.items()
    }


def analyse(
    records: Sequence[RunRecord],
    arms: Sequence[Arm],
    sets: Sequence[ItemSet],
    *,
    alpha: float = 0.05,
    control: str = CONTROL,
) -> tuple[SetResult, ...]:
    """Per-arm accuracy and the family of paired tests, one item set at a time.

    **The family is per set, and the sets are never pooled.** They ask different
    questions -- transfer to unseen scenarios, and memorisation of seen ones --
    and a correction applied across both would trade power on each for a
    family-wise rate over a family nobody registered.

    **Pass 1 only.** ``records`` is what :func:`run_study` loaded from the first
    pass, and the registered comparisons are computed on it alone. A later pass
    reaches :func:`analyse_passes` and nothing here, so adding passes to a study
    cannot move its registered numbers.
    """
    out: list[SetResult] = []
    for item_set in sets:
        mine = _in_set(records, item_set)
        outcomes = by_arm(mine, arms)
        family = [arm.label for arm in arms if arm.label not in (control, "off")]
        raw = [compare(item_set.label, name, outcomes, control=control) for name in family]
        adjusted = holm([c.p_value for c in raw], alpha=alpha) if raw else None
        comparisons = tuple(
            Comparison(**{**asdict(c), "adjusted": a, "rejected": r})
            for c, a, r in zip(
                raw,
                adjusted.adjusted if adjusted else (),
                adjusted.rejected if adjusted else (),
                strict=True,
            )
        )
        out.append(
            SetResult(
                label=item_set.label,
                n_items=len({_key(record) for record in mine}),
                accuracy=_accuracy(outcomes),
                comparisons=comparisons,
            )
        )
    return tuple(out)


def analyse_passes(
    passes: Sequence[Sequence[RunRecord]],
    arms: Sequence[Arm],
    sets: Sequence[ItemSet],
) -> tuple[SetPasses, ...]:
    """Each arm's accuracy on every pass, and every later pass against the first.

    ``passes[0]`` is pass 1. The agreement is item-level on correctness and is
    paired on the question, so a pass that is missing an item drops that item
    from the pair count and ``n_pairs`` says so. A later pass that shares no
    question with the first gets an accuracy and no agreement row, because a
    McNemar over nothing would print ``1.0`` and read as perfect.

    Descriptive, and outside the registered family on purpose. Whether an arm
    repeats is a question about the instrument, and correcting it alongside the
    hypotheses about skills would spend power on a test nobody registered.
    """
    out: list[SetPasses] = []
    for item_set in sets:
        tables = [by_arm(_in_set(records, item_set), arms) for records in passes]
        rows: list[ArmPasses] = []
        for arm in arms:
            first = tables[0][arm.label]
            agreement: list[PassAgreement] = []
            for index, table in enumerate(tables[1:], start=2):
                later = table[arm.label]
                shared = sorted(set(first) & set(later))
                if not shared:
                    continue
                before = [first[key] for key in shared]
                after = [later[key] for key in shared]
                identical = sum(1 for a, b in zip(before, after, strict=True) if a == b)
                agreement.append(
                    PassAgreement(
                        pass_index=index,
                        n_pairs=len(shared),
                        identical=identical,
                        different=len(shared) - identical,
                        p_value=mcnemar_exact(before, after, alternative="two-sided").p_value,
                    )
                )
            rows.append(
                ArmPasses(
                    arm=arm.label,
                    accuracy=tuple(_accuracy(table)[arm.label] for table in tables),
                    agreement=tuple(agreement),
                )
            )
        out.append(SetPasses(label=item_set.label, arms=tuple(rows)))
    return tuple(out)


def run_study(
    request: StudyRequest,
    arms: Sequence[Arm],
    *,
    venue: Venue,
    repo_root: Path,
    git_sha: str,
    on: date | None = None,
) -> StudyResult:
    """Score every arm over every item set, resuming from the checkpoints.

    Passes run outermost, then item sets, then chunks of ``request.chunk``
    items, and within a chunk every arm answers before the next chunk starts.
    So an interrupted study is missing the same tail of every arm rather than
    whole arms, and what it has of each arm was answered against the same hour
    of the venue as what it has of the others. Each arm writes its own
    ``records-<label>.jsonl`` and resumes from it.

    Raises:
        StudyError: The venue cannot hold the output cap it was given.
    """
    if request.max_tokens:
        try:
            assert_cap_fits(request.num_ctx or context_window(venue), request.max_tokens)
        except Exception as exc:
            raise StudyError(str(exc)) from exc

    paths = paths_for(
        repo_root, run_name(engine="study", git_sha=git_sha, on=on, slug=request.slug)
    )
    paths.root.mkdir(parents=True, exist_ok=True)
    roots = parse_roots(request.templates_root, base=repo_root)
    items = {item_set.label: item_set.items(root=roots) for item_set in request.sets}
    write_manifest(
        paths,
        {
            "request": asdict(request),
            "git_sha": git_sha,
            "ordering": ORDERING,
            "chunk": request.chunk,
            "passes": request.passes,
            "templates_roots": [_relative(root, repo_root) for root in roots],
            "arms": [
                {"label": arm.label, "kind": arm.kind, "candidate_sha": arm.sha} for arm in arms
            ],
            "sets": {
                label: {
                    "items": len(rows),
                    "templates": sorted({row.template_id for row in rows}),
                    "seeds": census([row.seed for row in rows]),
                    # The identity of a *generated* corpus. Item ids are
                    # coordinates and survive a template rewrite unchanged, so a
                    # study that recorded only its seeds and templates could be
                    # re-run against different content under the same
                    # description and nobody would see it.
                    "fingerprint": corpus_fingerprint(rows),
                }
                for label, rows in items.items()
            },
        },
    )

    ledger = BudgetLedger(
        limit_usd=0.0,
        bills=venue.bills,
        limit_calls=request.max_calls,
        limit_seconds=request.max_seconds,
    )
    call = call_fn(venue, max_tokens=request.max_tokens or None, num_ctx=request.num_ctx or None)
    stop_reason = ""
    prompts: dict[str, ArmPrompt] = {
        arm.label: build_arm(
            arm.kind,
            skill_body=arm.body or None,
            placebo_body=arm.body or None,
        )
        for arm in arms
    }

    with Solo(paths.root.parent, venue.model, paths.root.name):
        for pass_index in range(1, request.passes + 1):
            for label, rows in items.items():
                for start in range(0, len(rows), request.chunk):
                    chunk = rows[start : start + request.chunk]
                    print(
                        f"pass {pass_index} {label:8s} items {start + 1}-{start + len(chunk)} "
                        f"of {len(rows)}, {len(arms)} arms",
                        flush=True,
                    )
                    for arm in arms:
                        run_arm(
                            chunk,
                            prompts[arm.label],
                            model=venue.model,
                            checkpoint=records_path(paths.root, arm.label, pass_index),
                            call=call,
                            ledger=ledger,
                            candidate_sha=arm.sha,
                            resume_fields=RESUME_FIELDS,
                        )

        aa = _run_aa(request, arms, paths, venue=venue, call=call, ledger=ledger, items=items)

    records = load_pass(paths.root, arms, 1)
    later = [load_pass(paths.root, arms, index) for index in range(2, request.passes + 1)]
    return StudyResult(
        paths=paths,
        sets=analyse(records, arms, request.sets, alpha=request.alpha),
        aa=aa,
        stop_reason=stop_reason,
        records=len(records) + sum(len(rows) for rows in later),
        passes=analyse_passes([records, *later], arms, request.sets) if later else (),
    )


def _relative(path: Path, repo_root: Path) -> str:
    """A root as the manifest records it: inside the repository, relative to it."""
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return str(path)


def _run_aa(
    request: StudyRequest,
    arms: Sequence[Arm],
    paths: RunPaths,
    *,
    venue: Venue,
    call: CallFn,
    ledger: BudgetLedger,
    items: dict[str, list[Item]],
) -> Comparison | None:
    """Score the control a second time, into a checkpoint of its own.

    An A/A is the only control that reads the *instrument* rather than the arms.
    Two scorings of one body under identical conditions should not differ, and if
    they do then whatever separates the arms was separating them too. It needs a
    separate checkpoint because resume works exactly as designed: the same body on
    the same item under the same key is a call already made, and a second pass
    into the same file would be skipped and report perfect agreement.

    Returned rather than folded into the family. It is not a hypothesis about a
    skill and correcting it alongside three that are would spend power on a test
    nobody registered.
    """
    if not request.run_aa:
        return None
    control = next((arm for arm in arms if arm.label == CONTROL), None)
    if control is None:
        return None
    second = paths.root / AA_RECORDS
    prompt = build_arm(control.kind, skill_body=control.body or None, placebo_body=control.body)
    for label, rows in items.items():
        print(f"{'a/a':12s} {label:8s} {len(rows)} items", flush=True)
        run_arm(
            rows,
            prompt,
            model=venue.model,
            checkpoint=second,
            call=call,
            ledger=ledger,
            candidate_sha=control.sha,
            resume_fields=RESUME_FIELDS,
        )

    first = {
        _key(record): record.correct
        for record in load_records(records_path(paths.root, control.label))
        if record.arm == control.kind
    }
    repeat = {_key(record): record.correct for record in load_records(second)}
    shared = sorted(set(first) & set(repeat))
    if not shared:
        return None
    baseline = [first[key] for key in shared]
    again = [repeat[key] for key in shared]
    result = mcnemar_exact(baseline, again, alternative="two-sided")
    return Comparison(
        item_set="a/a",
        arm=f"{CONTROL} (second pass)",
        n_pairs=len(shared),
        accuracy=sum(again) / len(shared),
        control_accuracy=sum(baseline) / len(shared),
        arm_only=sum(1 for a, b in zip(again, baseline, strict=True) if a and not b),
        control_only=sum(1 for a, b in zip(again, baseline, strict=True) if b and not a),
        p_value=result.p_value,
        adjusted=result.p_value,
        rejected=result.p_value < request.alpha,
    )


def freeze(
    paths: RunPaths,
    sets: Sequence[SetResult],
    aa: Comparison | None = None,
    passes: Sequence[SetPasses] | None = None,
) -> None:
    """Write the study's numbers where a README can read them without rerunning it.

    ``passes`` is written only when a study ran more than one, so a one-pass
    study's ``analysis.json`` has the keys it always had.
    """
    payload: dict[str, object] = {
        "control": CONTROL,
        "sets": [asdict(result) for result in sets],
        "aa": asdict(aa) if aa else None,
    }
    if passes:
        payload["passes"] = [asdict(result) for result in passes]
    paths.root.joinpath("analysis.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )


__all__ = [
    "AA_RECORDS",
    "CONTROL",
    "ORDERING",
    "Arm",
    "ArmPasses",
    "Comparison",
    "ItemSet",
    "PassAgreement",
    "SetPasses",
    "SetResult",
    "StudyError",
    "StudyRequest",
    "StudyResult",
    "analyse",
    "analyse_passes",
    "by_arm",
    "compare",
    "freeze",
    "load_pass",
    "records_path",
    "run_study",
]
