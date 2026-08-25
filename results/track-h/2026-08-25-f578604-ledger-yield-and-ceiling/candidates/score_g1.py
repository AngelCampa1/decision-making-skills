"""Apply G1's disposition table to a set of blind re-derivations.

G1 does not cut. It produces a disagreement dossier and a per-arm disposition,
and G2 adjudicates what the dossier holds. The asymmetry is the whole design:
unanimity is *required* on the base and governing arms and *recorded but never
gated* on the matched arm, because requiring three blind readers to agree the
matched fact does not move selects for an easy matched arm, drives specificity
to 1.0, and manufactures a ceiling on purpose.

Reads two files:

``--manifest``
    ``blind-manifest.json``, mapping each opaque blind id to the triplet, arm,
    role, unit and keyed expected value it was cut from. Written after the
    blind prompts, and never shown to a G1 instance.

``--verdicts``
    JSON Lines, one row per instance per prompt::

        {"blind_id": "b07", "instance": 0, "answer": 41.0, "fork": null}

    ``fork`` carries the second defensible reading verbatim where an instance
    volunteered one, and ``null`` where it did not. A volunteered fork routes to
    G2 whatever the answer line said, which is how the two pass-two items with
    ambiguous governing arms would have been caught by a gate rather than by a
    reader happening to notice.

Usage::

    python results/track-h/candidates/score_g1.py \
        --manifest results/track-h/candidates/blind-manifest.json \
        --verdicts results/track-h/candidates/g1-verdicts.jsonl
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

Role = Literal["base", "treatment", "control"]

#: What the dispatcher does with an arm, before G2 sees anything.
Disposition = Literal["ok", "cut", "to_g2", "recorded"]


@dataclass(frozen=True, slots=True)
class ArmReading:
    """Every instance's answer for one arm, with the key beside it."""

    triplet: str
    arm: str
    role: str
    unit: str
    expected: float
    answers: tuple[float | None, ...]
    forks: tuple[str, ...]

    @property
    def unanimous(self) -> bool:
        parsed = [a for a in self.answers if a is not None]
        return len(parsed) == len(self.answers) and len(set(parsed)) == 1

    @property
    def agreed(self) -> float | None:
        """The value every instance returned, or ``None`` where they differ."""
        return self.answers[0] if self.unanimous else None


@dataclass
class TripletVerdict:
    triplet: str
    dispositions: dict[str, Disposition] = field(default_factory=dict)
    objections: list[str] = field(default_factory=list)

    @property
    def survives_g1(self) -> bool:
        """Whether this candidate reaches G2 at all.

        A ``cut`` on any arm ends it here. Anything else goes to G2, which is
        the only gate that cuts on judgement.
        """
        return "cut" not in self.dispositions.values()


def _base_disposition(base: ArmReading) -> tuple[Disposition, list[str]]:
    if not base.unanimous:
        parsed = [a for a in base.answers if a is not None]
        if len(set(parsed)) >= len(parsed):
            return "cut", ["base: three readings, no two agree - disqualifier 6"]
        return "to_g2", ["base: two of three, minority routed as an objection"]
    if base.agreed != base.expected:
        return "cut", [f"base: unanimous at {base.agreed}, key says {base.expected}"]
    return "ok", []


def _governing_disposition(gov: ArmReading, base: ArmReading) -> tuple[Disposition, list[str]]:
    if not gov.unanimous:
        return "to_g2", ["governing: disagreement, flagged disqualifier 15"]
    if base.unanimous and gov.agreed == base.agreed:
        return "cut", ["governing: unanimous and equal to base - the fact does not govern"]
    if gov.agreed != gov.expected:
        return "cut", [f"governing: unanimous at {gov.agreed}, key says {gov.expected}"]
    return "ok", []


def _matched_disposition(matched: ArmReading) -> tuple[Disposition, list[str]]:
    """Recorded, never gated.

    Disagreement here is either ambiguity, which is fatal, or difficulty, which
    is the property the item exists to have. G1 cannot tell them apart and G2
    can, so this arm never returns ``cut``.
    """
    if matched.unanimous:
        return "recorded", []
    return "recorded", ["matched: disagreement routed to G2 to be ruled ambiguity or difficulty"]


def score(readings: dict[tuple[str, str], ArmReading]) -> list[TripletVerdict]:
    by_triplet: dict[str, dict[str, ArmReading]] = defaultdict(dict)
    for (triplet, role), reading in readings.items():
        by_triplet[triplet][role] = reading

    verdicts: list[TripletVerdict] = []
    for triplet in sorted(by_triplet):
        arms = by_triplet[triplet]
        verdict = TripletVerdict(triplet=triplet)
        missing = {"base", "treatment", "control"} - set(arms)
        if missing:
            verdict.dispositions["*"] = "cut"
            verdict.objections.append(f"incomplete triplet, missing {sorted(missing)}")
            verdicts.append(verdict)
            continue

        dispositions = (
            ("base", _base_disposition(arms["base"])),
            ("treatment", _governing_disposition(arms["treatment"], arms["base"])),
            ("control", _matched_disposition(arms["control"])),
        )
        for role, (disposition, notes) in dispositions:
            verdict.dispositions[role] = disposition
            verdict.objections.extend(notes)

        for role, reading in arms.items():
            for fork in reading.forks:
                verdict.objections.append(f"{role}: volunteered fork routed to G2 - {fork}")

        verdicts.append(verdict)
    return verdicts


def load(manifest_path: Path, verdicts_path: Path) -> dict[tuple[str, str], ArmReading]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows: dict[str, list[dict[str, object]]] = defaultdict(list)
    for line in verdicts_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        rows[str(row["blind_id"])].append(row)

    readings: dict[tuple[str, str], ArmReading] = {}
    for blind_id, meta in manifest.items():
        instances = sorted(rows.get(blind_id, []), key=lambda r: int(r["instance"]))  # type: ignore[arg-type]
        answers = tuple(
            None if r.get("answer") is None else float(r["answer"])  # type: ignore[arg-type]
            for r in instances
        )
        forks = tuple(str(r["fork"]) for r in instances if r.get("fork"))
        readings[(str(meta["triplet"]), str(meta["role"]))] = ArmReading(
            triplet=str(meta["triplet"]),
            arm=str(meta["arm"]),
            role=str(meta["role"]),
            unit=str(meta["unit"]),
            expected=float(meta["expected"]),  # type: ignore[arg-type]
            answers=answers,
            forks=forks,
        )
    return readings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--verdicts", type=Path, required=True)
    args = parser.parse_args()

    readings = load(args.manifest, args.verdicts)
    verdicts = score(readings)

    print("G1 dispositions\n")
    for verdict in verdicts:
        arms = " ".join(f"{r}={d}" for r, d in sorted(verdict.dispositions.items()))
        print(f"  {verdict.triplet}: {arms}")
        for objection in verdict.objections:
            print(f"      - {objection}")

    reaching_g2 = [v for v in verdicts if v.survives_g1]
    print(f"\n  {len(reaching_g2)} of {len(verdicts)} candidate(s) reach G2")
    print("\n  G1 does not decide the yield. G2 does, and it has not run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
