"""Partition the blind prompts so no reader ever holds two arms of one triplet.

G1's rule is one prompt per call, because a reader shown two arms of the same
triplet reasons comparatively, hunting for the difference, and would manufacture
both the movement and the non-movement. Forty-five separate calls honour that
rule and cost forty-five dispatches.

A partition gets the same guarantee cheaply. Each group holds one arm from each
of the five triplets, so within a group every prompt is a different scenario in
a different domain and there is nothing to compare. Three groups cover the
fifteen prompts, and three instances of each group give the three independent
readings per arm that the disposition table reads.

The blind ids stay opaque, so a reader cannot tell which triplet a prompt came
from even though it knows the five are distinct.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> int:
    manifest = json.loads((HERE / "blind-manifest.json").read_text(encoding="utf-8"))

    by_triplet: dict[str, list[str]] = defaultdict(list)
    for blind_id, meta in manifest.items():
        by_triplet[str(meta["triplet"])].append(blind_id)

    widths = {len(v) for v in by_triplet.values()}
    if widths != {3}:
        raise SystemExit(f"expected 3 arms per triplet, saw {sorted(widths)}")

    # Rotating the arm index by triplet keeps a group from being all one role,
    # which would make the group itself a label.
    groups: list[list[str]] = [[], [], []]
    for offset, triplet in enumerate(sorted(by_triplet)):
        arms = sorted(by_triplet[triplet])
        for g in range(3):
            groups[g].append(arms[(g + offset) % 3])

    out = {f"group-{g + 1}": sorted(ids) for g, ids in enumerate(groups)}
    (HERE / "g1-groups.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")

    for name, ids in out.items():
        triplets = [manifest[i]["triplet"] for i in ids]
        roles = [manifest[i]["role"] for i in ids]
        assert len(set(triplets)) == len(triplets), f"{name} repeats a triplet"
        print(f"  {name}: {' '.join(ids)}")
        print(f"           {' '.join(str(r) for r in roles)}   (dispatcher only)")

    seen = sorted(i for ids in out.values() for i in ids)
    assert seen == sorted(manifest), "partition does not cover every prompt"
    print(f"\n  {len(seen)} prompts, 3 groups, no group repeats a triplet")
    print("  3 instances per group = 45 readings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
