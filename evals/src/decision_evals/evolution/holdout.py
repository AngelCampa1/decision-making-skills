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
import itertools
from collections.abc import Callable, Iterable, Iterator, Sequence
from dataclasses import dataclass
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

    drawn = list(itertools.islice(_derive(passphrase), count))
    return tuple(sorted(drawn))


def _derive(passphrase: str) -> Iterator[int]:
    """Holdout seeds in derivation order, without repeats, forever.

    Separate from :func:`holdout_seeds` because the two callers want different
    things from the same sequence. A split is reported sorted, which is a
    presentation choice. :func:`mint` has to walk the sequence *in the order it
    was derived*, or which seeds it keeps would depend on how many it looked at
    -- and a split that changes when the search ceiling changes is not
    reproducible from the passphrase.
    """
    span = POOLS["holdout"]
    seen: set[int] = set()
    attempt = 0
    while len(seen) < len(span):
        digest = hashlib.sha256(f"{passphrase}:{attempt}".encode()).digest()
        seed = span.start + int.from_bytes(digest[:8], "big") % len(span)
        attempt += 1
        if seed in seen:
            continue
        seen.add(seed)
        yield seed


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


@dataclass(frozen=True, slots=True)
class Mint:
    """A holdout split, and every seed that was thrown away making it.

    Discards are carried rather than dropped because dropping them is a
    researcher degree of freedom. "Draw forty seeds" and "draw until forty of
    them worked" are different procedures, and only the second one is what
    happens; a split that reports the first while doing the second has an
    unrecorded filter in it.
    """

    seeds: tuple[int, ...]
    #: Seed -> why it could not be minted, in the order they were drawn.
    discarded: tuple[tuple[int, str], ...]
    #: How many draws it took. The denominator for the discard rate.
    attempts: int

    @property
    def discard_rate(self) -> float:
        return len(self.discarded) / self.attempts if self.attempts else 0.0


def mint(
    passphrase: str,
    count: int,
    generate_at: Callable[[int], object],
    *,
    ceiling: int = 0,
) -> Mint:
    """Draw ``count`` holdout seeds that can actually produce a corpus.

    Roughly one seed in forty cannot. It is always the same template --
    ``rel-008-contract-renew`` fails to produce a robust, discriminative
    ``renew`` in 500 attempts -- and it is not rare enough to leave to chance:
    seed 1001 was this package's shipped default and crashed the first run
    against a real venue. Finding one inside a frozen holdout partway through a
    study is the same failure with the cost of the study attached.

    Seeds are tried in the order :func:`holdout_seeds` derives them, so the same
    passphrase mints the same split, discards included.

    Args:
        passphrase: Not in the tree. See :func:`holdout_seeds`.
        count: How many usable seeds are wanted.
        generate_at: What proves a seed usable. Called once per candidate and
            expected to raise when the corpus cannot be built. Injected rather
            than imported so this module does not depend on the generator, and
            so a test can mint without generating 280 items a seed.
        ceiling: Give up after this many draws. Zero derives one from ``count``,
            which is enough headroom for a discard rate many times the observed
            one.

    Raises:
        ValueError: The ceiling was reached. A run that quietly returned a
            short split would put a smaller denominator into every test that
            reads it.
    """
    limit = ceiling or max(count * 4, count + 50)
    kept: list[int] = []
    discarded: list[tuple[int, str]] = []
    attempts = 0
    for seed in itertools.islice(_derive(passphrase), limit):
        if len(kept) == count:
            break
        attempts += 1
        try:
            generate_at(seed)
        except Exception as exc:
            discarded.append((seed, f"{type(exc).__name__}: {exc}"))
            continue
        kept.append(seed)
    if len(kept) < count:
        raise ValueError(
            f"only {len(kept)} of {count} holdout seeds could be minted in {attempts} "
            f"draws ({len(discarded)} discarded). Raise `ceiling` deliberately rather "
            "than accepting a short split: every paired test downstream reads its "
            "denominator off this."
        )
    return Mint(tuple(sorted(kept)), tuple(discarded), attempts)
