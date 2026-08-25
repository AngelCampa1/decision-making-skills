"""Cut the model-visible prompts out of a candidate set, shuffled and unlabelled.

G1 instances must not be able to recover the arm. Three things enforce that
here: the ``key`` and ``meta`` blocks never leave this script, the output file
is named by an opaque id rather than by the triplet, and the id-to-arm map goes
to a manifest the dispatcher holds and no instance sees.

The shuffle is seeded so the mapping is reproducible from the seed and the file
list alone. Rerunning after the candidate set changes reshuffles every id, which
is why the manifest and the prompts are written together or not at all.

Usage::

    python results/track-h/candidates/make_blind.py
"""

from __future__ import annotations

import json
import random
from pathlib import Path

import yaml

SEED = 20260825
HERE = Path(__file__).resolve().parent


def main() -> int:
    paths = sorted(HERE.glob("L*-*.yaml"))
    if not paths:
        raise SystemExit("no candidate files found")

    ids = list(range(len(paths)))
    random.Random(SEED).shuffle(ids)

    out_dir = HERE / "blind"
    for stale in out_dir.glob("*.txt"):
        stale.unlink()
    out_dir.mkdir(exist_ok=True)

    manifest: dict[str, dict[str, object]] = {}
    for path, n in zip(paths, ids, strict=True):
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        blind_id = f"b{n:02d}"
        (out_dir / f"{blind_id}.txt").write_text(doc["prompt"], encoding="utf-8")
        manifest[blind_id] = {
            "file": path.name,
            "triplet": doc["triplet"],
            "arm": doc["arm"],
            "role": doc["role"],
            "unit": doc["elicited"]["unit"],
            "expected": doc["key"]["expected_value"],
        }

    ordered = {k: manifest[k] for k in sorted(manifest)}
    (HERE / "blind-manifest.json").write_text(
        json.dumps(ordered, indent=2) + "\n", encoding="utf-8"
    )

    print(f"{len(paths)} prompts cut to {out_dir.relative_to(HERE.parents[2])}")
    by_triplet: dict[str, int] = {}
    for meta in manifest.values():
        by_triplet[str(meta["triplet"])] = by_triplet.get(str(meta["triplet"]), 0) + 1
    for triplet in sorted(by_triplet):
        count = by_triplet[triplet]
        flag = "" if count == 3 else "   <-- incomplete"
        print(f"  {triplet}: {count} arms{flag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
