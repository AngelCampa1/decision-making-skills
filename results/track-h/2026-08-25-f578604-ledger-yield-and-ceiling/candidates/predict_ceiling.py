"""Predict the unaided ceiling from G1's readings, before any generation call.

G1 pays for three blind re-derivations of every arm. Those readings already
answer the question the control arm was going to be run to answer, at no extra
cost: whether an unaided reader moves on the governing fact and holds still on
the matched one.

Two rates, both over triplets rather than over readings, because readings within
a triplet are not independent:

``sensitivity``
    the share of triplets whose governing arm was read, unanimously, as a value
    differing from the base. Movement the instrument would score as a hit.

``specificity``
    the share whose matched arm was read, unanimously, as the base value.
    Non-movement the instrument would score as a correct rejection.

J is their sum less one, which is the same quantity ``stats/track_h.py``
computes and the same quantity the registered kill reads.

**This is not the unaided number, and reading it as one would be the mistake
this docstring exists to stop.** G1's brief demands the arithmetic step by step
and tells the reader to declare a second defensible reading if one exists. That
is close to what `ledger` itself instructs, and nothing like the bare `off` arm.
So J here bounds the *treated* arm: it says the items are solvable and the key
is right, which is what G1 was for.

The registered kill reads unaided J, and unaided J is a different run. An `off`
arm given less help can only do the same or worse, and worse means headroom
rather than less of it. So a 1.0 here closes nothing on its own — it says the
ceiling of the treated arm is 1.0, and leaves J(on) − J(off) open until the
control arm is run against the same fifteen prompts with the arithmetic demand
and the fork warning stripped out.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
KILL = 0.70


def main() -> int:
    manifest = json.loads((HERE / "blind-manifest.json").read_text(encoding="utf-8"))

    answers: dict[str, list[float]] = defaultdict(list)
    forks: dict[str, int] = defaultdict(int)
    for line in (HERE / "g1-verdicts.jsonl").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        answers[row["blind_id"]].append(float(row["answer"]))
        if row.get("fork"):
            forks[row["blind_id"]] += 1

    arms: dict[str, dict[str, tuple[float | None, int, float]]] = defaultdict(dict)
    for blind_id, meta in manifest.items():
        got = answers[blind_id]
        agreed = got[0] if len(set(got)) == 1 else None
        arms[str(meta["triplet"])][str(meta["role"])] = (
            agreed,
            len(got),
            float(meta["expected"]),
        )

    print(f"{'triplet':<9} {'base':>8} {'governing':>10} {'matched':>8}   reading")
    hits = misses = 0
    correct_rejections = false_alarms = 0
    for triplet in sorted(arms):
        base, gov, matched = (arms[triplet][r] for r in ("base", "treatment", "control"))
        moved = gov[0] is not None and base[0] is not None and gov[0] != base[0]
        held = matched[0] is not None and matched[0] == base[0]
        hits += moved
        misses += not moved
        correct_rejections += held
        false_alarms += not held
        verdict = "moved on governing, held on matched" if moved and held else "see arms"
        print(f"{triplet:<9} {base[0]!s:>8} {gov[0]!s:>10} {matched[0]!s:>8}   {verdict}")

    n = len(arms)
    sensitivity = hits / n
    specificity = correct_rejections / n
    j = sensitivity + specificity - 1

    print(f"\n  readings           {sum(len(v) for v in answers.values())}")
    print(
        f"  arms read          {len(manifest)}, unanimous on {sum(1 for v in answers.values() if len(set(v)) == 1)}"
    )
    print(f"  volunteered forks  {sum(forks.values())}")
    print(f"\n  sensitivity        {sensitivity:.3f}   ({hits} of {n} triplets)")
    print(f"  specificity        {specificity:.3f}   ({correct_rejections} of {n})")
    print(f"  J under G1's brief {j:.3f}")
    print(f"  registered kill    unaided J >= {KILL:.2f} closes the stratum")
    print("\n  This is the treated ceiling, not the unaided number. The kill")
    print("  reads a control arm that has not run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
