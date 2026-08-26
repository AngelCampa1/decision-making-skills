"""Where an evolution run keeps its working state, and why it is not a result.

``results/`` holds published runs: ``results/<skill>/<date>-<sha7>/`` with a
README that :mod:`decision_evals.provenance` binds to the records beside it. An
evolution search is not one of those. It is hundreds of candidates, most of them
worse than the seed, scored on training seeds, and publishing that as a run
would put a number nobody should read next to the numbers people should.

So a search writes to ``results/evolution/<run>/``, which is gitignored, and
:data:`~decision_evals.provenance.WORKING_DIRS` keeps the provenance gate out of
it. What *does* get published is the study that reads the frozen winners, and
that is an ordinary run directory with an ordinary README.

Three files per run, and the split is deliberate. ``records.jsonl`` is a
standard checkpoint the ordinary loaders read, so a search's calls can be
re-scored by the same code that re-scores anything else. ``lineage.jsonl`` is
the search itself. ``run.json`` is what was asked for -- venue, caps, seeds,
engine -- written before the first call, so a run that dies still says what it
was trying to do.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any, Final

#: Under ``results/``, and gitignored.
EVOLUTION_ROOT: Final = "results/evolution"

RECORDS: Final = "records.jsonl"
LINEAGE: Final = "lineage.jsonl"
MANIFEST: Final = "run.json"

_SLUG = re.compile(r"[^a-z0-9]+")


class CheckpointError(RuntimeError):
    """A run directory was asked for that cannot be built."""


@dataclass(frozen=True, slots=True)
class RunPaths:
    """The three files one search writes."""

    root: Path
    records: Path
    lineage: Path
    manifest: Path


def run_name(*, engine: str, git_sha: str, on: date | None = None, slug: str = "") -> str:
    """``<date>-<sha7>-<engine>[-<slug>]``.

    The same shape a published run directory uses, so a lineage and the study
    that reads it sort together and a reader can tell at a glance which commit
    a search ran at.

    Raises:
        CheckpointError: A sha too short to identify a commit. Seven characters
            is the repository's convention everywhere else, and a truncated one
            would make two runs collide silently.
    """
    if len(git_sha) < 7:
        raise CheckpointError(f"git_sha {git_sha!r} is shorter than the seven-character convention")
    parts = [(on or date.today()).isoformat(), git_sha[:7], engine]
    if slug:
        parts.append(_SLUG.sub("-", slug.lower()).strip("-"))
    return "-".join(part for part in parts if part)


def paths_for(repo_root: Path, name: str) -> RunPaths:
    """The three paths under one run directory. Does not create anything."""
    root = repo_root / EVOLUTION_ROOT / name
    return RunPaths(
        root=root,
        records=root / RECORDS,
        lineage=root / LINEAGE,
        manifest=root / MANIFEST,
    )


def write_manifest(paths: RunPaths, manifest: Any) -> None:
    """Write what the run was asked to do, before it does any of it.

    Overwrites. A resumed run rewrites the manifest with the caps it resumed
    under, which is the honest record: a search resumed against a raised call
    cap did not run under the original one, and a manifest that kept the first
    number would say it did.
    """
    paths.root.mkdir(parents=True, exist_ok=True)
    payload = manifest if isinstance(manifest, dict) else asdict(manifest)
    paths.manifest.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8"
    )


def read_manifest(paths: RunPaths) -> dict[str, Any]:
    """What a run said it was doing.

    Raises:
        CheckpointError: No manifest. A directory of records with nothing saying
            which venue, which caps and which seeds produced them is not a run,
            and reading it as one is how a number gets attributed to the wrong
            model.
    """
    if not paths.manifest.is_file():
        raise CheckpointError(
            f"{paths.manifest} is missing, so nothing says what this run was. Records with "
            "no manifest cannot be attributed to a venue or a seed pool."
        )
    loaded: dict[str, Any] = json.loads(paths.manifest.read_text(encoding="utf-8"))
    return loaded
