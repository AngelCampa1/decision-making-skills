"""Which seeds an engine may see, and the refusal when it sees one it may not.

An evolution run is a contamination machine. It reads scores off items,
rewrites the skill to score better on them, and repeats a few hundred times.
Whatever it optimised against stops being a test of anything, and the number
that matters is the one from items no engine ever touched.

Every published skill-evolution result the survey found reports a single score
on a fixed split, with the engine's own validation set doing double duty as the
test set. That is not a small methodological quibble: an engine that runs
hundreds of accept/reject decisions against a set has fitted it, and reporting
that set's score is reporting training accuracy. The only defence is a split
drawn *after* the search is frozen, from seeds the search could not reach.

So seeds are partitioned by range, the partition is checked rather than
remembered, and :func:`assert_evolvable` refuses a set of items carrying a
holdout seed before the call is made rather than after the number is computed.

**The ranges are arbitrary and that is fine.** What matters is that they are
disjoint, that they are written down in one place, and that a seed outside all
of them is an error rather than a default — an unassigned seed is how a set
quietly becomes neither training nor test.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Sequence
from typing import Final, Literal

Pool = Literal["train", "validation", "holdout"]

#: The lowest holdout seed. Far above the other pools so a range that grows
#: cannot walk into it, and round so a seed in a record says which pool it came
#: from at a glance.
HOLDOUT_FLOOR: Final = 10_000

#: Seed ranges by pool, in the order a run uses them. ``train`` is what the
#: engine mutates against. ``validation`` is what its acceptance gate reads, and
#: it is resampled during a run, which is why it is a range rather than a fixed
#: set. ``holdout`` is minted after the winners are frozen and is read once.
POOLS: Final[dict[Pool, range]] = {
    "train": range(0, 1_000),
    "validation": range(1_000, 1_500),
    "holdout": range(HOLDOUT_FLOOR, HOLDOUT_FLOOR + 1_000),
}

#: The pools an engine may draw from. Everything else is a breach.
EVOLVABLE: Final[frozenset[Pool]] = frozenset({"train", "validation"})


class HoldoutBreachError(RuntimeError):
    """An engine was about to see an item it may not see."""


def pool_of(seed: int) -> Pool | None:
    """Which pool a seed belongs to, or ``None`` when it belongs to none.

    ``None`` rather than a fourth pool called "other". A seed nobody assigned is
    not a category of item, it is a mistake, and naming it would make it look
    like a decision someone took.
    """
    for pool, seeds in POOLS.items():
        if seed in seeds:
            return pool
    return None


def assert_evolvable(seeds: Iterable[int]) -> None:
    """Refuse a batch an engine may not optimise against.

    Called before the calls go out, so a breach costs a refusal rather than a
    frozen winner whose score means nothing. Both failures are reported in one
    message: fixing an unassigned seed and then discovering a holdout seed is
    two rounds of the same conversation.

    Raises:
        HoldoutBreachError: Any seed outside :data:`EVOLVABLE`.
    """
    breached: dict[str, list[int]] = {"holdout": [], "unassigned": []}
    for seed in sorted(set(seeds)):
        pool = pool_of(seed)
        if pool is None:
            breached["unassigned"].append(seed)
        elif pool not in EVOLVABLE:
            breached[pool].append(seed)

    if not any(breached.values()):
        return

    lines = []
    if breached["holdout"]:
        lines.append(
            f"{len(breached['holdout'])} holdout seed(s) in this batch, "
            f"starting {breached['holdout'][0]}. An engine that scores on these has "
            "fitted the test set, and there is no undoing it inside a seed."
        )
    if breached["unassigned"]:
        lines.append(
            f"{len(breached['unassigned'])} seed(s) in no pool, starting "
            f"{breached['unassigned'][0]}. Assign them in POOLS or draw from a pool; "
            "a seed that is neither training nor test is how a split stops meaning "
            "anything."
        )
    raise HoldoutBreachError(" ".join(lines))


def holdout_seeds(passphrase: str, count: int) -> tuple[int, ...]:
    """Draw ``count`` holdout seeds from a passphrase.

    Derived rather than stored, so the split can be rebuilt from something that
    is not in the tree — the convention ``datasets/holdout/README.md`` sets out,
    reused here because the same argument applies. SHA-256 rather than
    :func:`hash`, which is randomised per process.

    Drawn without replacement and returned sorted, because a duplicate seed is a
    duplicate item and would weight one scenario twice in a paired test.

    Raises:
        ValueError: A count that cannot be drawn, or an empty passphrase. An
            empty passphrase derives a split anyone can rebuild, which is the
            one property this is for.
    """
    if not passphrase.strip():
        raise ValueError(
            "a holdout needs a passphrase that is not in the tree; an empty one "
            "derives a split that anyone reading this file can rebuild"
        )
    span = POOLS["holdout"]
    if not 1 <= count <= len(span):
        raise ValueError(f"count must be between 1 and {len(span)}, got {count}")

    drawn: list[int] = []
    seen: set[int] = set()
    attempt = 0
    while len(drawn) < count:
        digest = hashlib.sha256(f"{passphrase}:{attempt}".encode()).digest()
        seed = span.start + int.from_bytes(digest[:8], "big") % len(span)
        attempt += 1
        if seed in seen:
            continue
        seen.add(seed)
        drawn.append(seed)
    return tuple(sorted(drawn))


def census(seeds: Sequence[int]) -> dict[str, int]:
    """How many seeds fall in each pool, for a run's own record.

    Unassigned seeds are counted under ``"unassigned"`` rather than dropped. A
    census that silently omits what it could not classify reports a clean split
    for a batch that has none.
    """
    counts: dict[str, int] = dict.fromkeys(POOLS, 0)
    counts["unassigned"] = 0
    for seed in seeds:
        counts[pool_of(seed) or "unassigned"] += 1
    return counts
