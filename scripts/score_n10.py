"""Score N10, the six description arms on answer key v6.

Everything the run record asserts and no gate recomputes is here: the four
licensed predictions, the paired tests behind the opener result, the routing
precision table and the bootstrap on prediction 5's margin. The pre-run rule is
that a registered figure names its estimator and its denominator, and this file
is where N10's denominators are readable instead of guessed.

Predictions 1 and 3 are absent on purpose. Both register a band against a v4
figure, `label_versions_comparable` and `skill_versions_comparable` both refuse
that comparison, and the addendum beside the prediction records it. A scorer
that computed them anyway would be manufacturing the licence.

    python -m uv run python scripts/score_n10.py

Reads the published records under `results/decision-making/`, writes nothing.
"""

from __future__ import annotations

import collections
import random
import sys
from math import comb
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "evals" / "src"))

from decision_evals import trigger_arms as ta  # noqa: E402
from decision_evals.triggers import load_trigger_set  # noqa: E402

RUN = REPO_ROOT / "results/decision-making/2026-08-25-5ed5d38-n10-six-arms-v6"
CORPUS = REPO_ROOT / "datasets/triggers/decision-making/index.yaml"
ARMS = (
    "full",
    "no-exclusions",
    "opener-only",
    "no-opener",
    "stakes-named",
    "stakes-shown",
)
CARRIED_ROUTES = ("cascade", "timing", "fit", "ledger")

# Prediction 5's bootstrap. Fixed so the interval in the run record is
# reproducible: an unrecorded seed makes a published CI unfalsifiable.
BOOTSTRAP_SEED = 1
BOOTSTRAP_RESAMPLES = 20_000


def route_of(row: ta.Record) -> str | None:
    """The item's registered route, however this record spells it."""
    routes = row.get("routes")
    if isinstance(routes, (list, tuple)) and routes:
        return routes[0]
    return row.get("route")


def exact_mcnemar(b: int, c: int) -> float:
    """Two-sided exact McNemar on the discordant pairs alone."""
    n = b + c
    if n == 0:
        return 1.0
    tail = sum(comb(n, i) for i in range(min(b, c) + 1))
    return min(1.0, 2 * tail / 2**n)


def paired(arms: dict[str, list[ta.Record]], a: str, b: str, *, positives: bool):
    """Discordant counts between two arms over one half of the corpus."""
    left = {(r["case"], r["repeat"]): r for r in arms[a]}
    right = {(r["case"], r["repeat"]): r for r in arms[b]}
    only_left = only_right = n = 0
    for key in left.keys() & right.keys():
        if bool(left[key]["should_fire"]) is not positives:
            continue
        n += 1
        x, y = bool(left[key]["fired"]), bool(right[key]["fired"])
        only_left += x and not y
        only_right += y and not x
    return n, only_left, only_right


def fire_rate(records, ids) -> tuple[float, int, int]:
    """Share of parsed records on `ids` that fired. Voids leave the denominator."""
    fired = seen = 0
    for row in records:
        if row["case"] in ids and row["should_fire"] and row["fired"] is not None:
            seen += 1
            fired += bool(row["fired"])
    return (fired / seen if seen else 0.0), fired, seen


def bootstrap_fpr_gap(arms, high: str, low: str) -> tuple[float, float, float, float]:
    """Paired cluster bootstrap on the FPR gap, resampling triples.

    Paired because both arms answer the same 220 negative items; resampling the
    arms independently would price a between-subject comparison that was never
    made. `trigger_arms.bootstrap_rate_difference` refuses shared case ids for
    that reason, which is why this is computed here rather than called.
    """

    def negatives_by_triple(records):
        out: dict[str, list[ta.Record]] = {}
        for row in records:
            if not row["should_fire"] and row["fired"] is not None:
                out.setdefault(row["triple"], []).append(row)
        return out

    hi, lo = negatives_by_triple(arms[high]), negatives_by_triple(arms[low])
    triples = sorted(hi.keys() & lo.keys())

    def fpr(rows):
        return sum(1 for r in rows if r["fired"]) / len(rows)

    point = fpr([r for t in triples for r in hi[t]]) - fpr([r for t in triples for r in lo[t]])
    rng = random.Random(BOOTSTRAP_SEED)
    draws = []
    for _ in range(BOOTSTRAP_RESAMPLES):
        pick = [triples[rng.randrange(len(triples))] for _ in triples]
        draws.append(fpr([r for t in pick for r in hi[t]]) - fpr([r for t in pick for r in lo[t]]))
    draws.sort()
    lo_ci = draws[int(0.025 * len(draws))]
    hi_ci = draws[int(0.975 * len(draws))]
    share = sum(1 for d in draws if d > 0.10) / len(draws)
    return point, lo_ci, hi_ci, share


def main() -> int:
    trigger_set = load_trigger_set(CORPUS)
    positives = [c for c in trigger_set.cases if c.should_fire]
    new_ids = {c.id for c in positives if getattr(c, "route", None) in ("council", "hinge")}
    carried_ids = {c.id for c in positives} - new_ids

    if len(new_ids) != 24 or len(carried_ids) != 86:
        print("REFUSING: the 86/24 split predictions 2 and 6 rest on does not hold")
        return 1

    arms = {name: ta.load_arm(RUN / f"verdicts-{name}.jsonl") for name in ARMS}
    for name, records in arms.items():
        if len(records) != 660:
            print(f"REFUSING: {name} has {len(records)} records, wants 660")
            return 1

    flat = [r for records in arms.values() for r in records]
    for guard in (
        ta.label_versions_comparable,
        ta.models_comparable,
        ta.venue_comparable,
        ta.skill_versions_comparable,
    ):
        if (reason := guard(flat, flat)) is not None:
            print(f"REFUSING: {reason}")
            return 1

    summaries = {n: ta.summarise(r) for n, r in arms.items()}
    print("=== per arm, record-weighted ===")
    print(f"{'arm':>14} {'parse':>7} {'acc':>7} {'recall':>7} {'FPR':>7}")
    for name, s in summaries.items():
        parse = (s.n_records - s.unparseable) / s.n_records
        print(
            f"{name:>14} {parse:>7.4f} {s.accuracy:>7.4f} "
            f"{s.recall:>7.4f} {s.false_positive_rate:>7.4f}"
        )

    print("\n=== the opener: full against no-opener, paired on the same items ===")
    for label, is_pos in (("positives (recall)", True), ("negatives (FPR)", False)):
        n, full_only, noop_only = paired(arms, "full", "no-opener", positives=is_pos)
        p = exact_mcnemar(full_only, noop_only)
        print(
            f"  {label:>18} n={n:>3}  full-only={full_only:>2}  "
            f"no-opener-only={noop_only:>2}  discordant={full_only + noop_only:>2}  "
            f"exact McNemar p={p:.4f}"
        )
    fpr_full = summaries["full"].false_positive_rate
    fpr_noop = summaries["no-opener"].false_positive_rate
    print(f"  FPR {fpr_full:.4f} -> {fpr_noop:.4f}, a {1 - fpr_noop / fpr_full:.1%} reduction")

    print("\n=== prediction 2: new positives fire below carried, in EVERY arm ===")
    held = True
    for name, records in arms.items():
        c_rate, _, c_n = fire_rate(records, carried_ids)
        n_rate, _, n_n = fire_rate(records, new_ids)
        ok = n_rate < c_rate
        held &= ok
        print(
            f"  {name:>14} carried {c_rate:.4f} (n={c_n})  new {n_rate:.4f} (n={n_n})  "
            f"{'held' if ok else 'FAILED'}"
        )
    print(f"  --> prediction 2 {'HELD' if held else 'FAILED'}")

    print("\n=== prediction 6: no arm reaches 1.0000 recall on the 24 new positives ===")
    held = True
    for name, records in arms.items():
        rate, fired, seen = fire_rate(records, new_ids)
        held &= rate < 1.0
        print(f"  {name:>14} {rate:.4f} ({fired}/{seen})")
    print(f"  --> prediction 6 {'HELD' if held else 'FAILED'}")

    print("\n=== prediction 5: the two named arms top FPR by more than 0.10 ===")
    order = sorted(
        ((n, s.false_positive_rate) for n, s in summaries.items()), key=lambda kv: -kv[1]
    )
    for n, v in order:
        print(f"  {n:>14} {v:.4f}")
    pair_ok = {order[0][0], order[1][0]} == {"no-exclusions", "opener-only"}
    gap = order[1][1] - order[2][1]
    point, lo_ci, hi_ci, share = bootstrap_fpr_gap(arms, order[1][0], order[2][0])
    print(f"  top two as registered: {pair_ok}   gap {gap:.4f}")
    print(
        f"  paired cluster bootstrap on triples, seed {BOOTSTRAP_SEED}, "
        f"{BOOTSTRAP_RESAMPLES} resamples: point {point:.4f} "
        f"95% CI [{lo_ci:.4f}, {hi_ci:.4f}], P(gap > 0.10) = {share:.3f}"
    )
    print(f"  --> prediction 5 {'HELD' if pair_ok and gap > 0.10 else 'FAILED'}")

    print("\n=== prediction 4: ledger weakest of the four carried routes ===")
    for rule in ta.ROUTING_RULES:
        routing = ta.routing_by_procedure(flat, rule=rule)
        rates = {name: g.over_answered for name, g in routing.groups.items()}
        carried = {k: v for k, v in rates.items() if k in CARRIED_ROUTES}
        weakest = min(carried, key=lambda k: carried[k])
        print(f"  rule {rule!r}: weakest carried route is {weakest}")

    print("\n=== routing, pooled over six arms, positives only, rule 'first' ===")
    routing = ta.routing_by_procedure(flat, rule="first")
    recall = {name: g.over_answered for name, g in routing.groups.items()}
    on_pos: collections.Counter[str] = collections.Counter()
    right_pos: collections.Counter[str] = collections.Counter()
    on_all: collections.Counter[str] = collections.Counter()
    right_all: collections.Counter[str] = collections.Counter()
    for row in flat:
        got = row.get("procedure")
        if not row.get("fired") or not got:
            continue
        on_all[got] += 1
        right_all[got] += got == route_of(row)
        if row["should_fire"] and route_of(row):
            on_pos[got] += 1
            right_pos[got] += got == route_of(row)
    print(f"{'procedure':>10} {'precision':>10} {'recall':>8} {'chosen':>7} | over every row")
    for proc in sorted(on_pos, key=lambda k: -on_pos[k]):
        wide = right_all[proc] / on_all[proc]
        print(
            f"{proc:>10} {right_pos[proc] / on_pos[proc]:>10.4f} {recall[proc]:>8.4f} "
            f"{on_pos[proc]:>7} | {right_all[proc]:>4}/{on_all[proc]:<4} = {wide:.4f}"
        )

    print("\n=== where ledger's fires went ===")
    dest: collections.Counter[str] = collections.Counter()
    unnamed = 0
    for row in flat:
        if not row["should_fire"] or not row["fired"] or route_of(row) != "ledger":
            continue
        got = row.get("procedure")
        if not got:
            unnamed += 1
        elif got != "ledger":
            dest[got] += 1
    named = sum(dest.values())
    for k, v in dest.most_common():
        print(
            f"  ledger -> {k:>10} {v:>4}  {v / named:.1%} of named, {v / (named + unnamed):.1%} of all"
        )
    print(f"  ({unnamed} misroutes named no procedure)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
