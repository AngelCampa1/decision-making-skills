"""Skill evolution: running an engine against this harness, under its controls.

Two engines are the subject — `gepa` and `skillopt`, both installed from PyPI
into the `evolve` dependency group and neither a dependency of the gate. What
lives here is everything they need that they do not ship: a scored environment
built out of the arms and scorers already in this package, a seed firewall, a
lineage record, and a budget that can stop a search on a venue where every call
costs nothing.

The one claim this package exists to make checkable is that an evolved skill
was scored on items no engine ever saw. Everything else is bookkeeping around
it.
"""

from decision_evals.evolution.holdout import (
    HOLDOUT_FLOOR,
    POOLS,
    HoldoutBreachError,
    assert_evolvable,
    holdout_seeds,
    pool_of,
)
from decision_evals.evolution.lineage import (
    Candidate,
    LineageError,
    append_candidate,
    body_sha,
    load_lineage,
)

__all__ = [
    "HOLDOUT_FLOOR",
    "POOLS",
    "Candidate",
    "HoldoutBreachError",
    "LineageError",
    "append_candidate",
    "assert_evolvable",
    "body_sha",
    "holdout_seeds",
    "load_lineage",
    "pool_of",
]
