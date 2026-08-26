"""One evolution run, start to finish.

What a search needs beyond the engine and the adapter, in the order it needs it:
the items, the seed body, a budget that can stop it, a manifest written before
the first call, and a winner that is checked rather than believed.

The last one is the reason this is a module rather than a script. GEPA returns a
best candidate whether or not it ever mutated anything, so :func:`evolve` reads
the lineage back off disk and runs
:func:`~decision_evals.evolution.lineage.assert_searched` against it before
returning. A frozen winner that came out of a search of one is the failure this
whole package was built after.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Final

from decision_evals.budget import BudgetLedger, NestedBudget
from decision_evals.evolution.adapter import COMPONENT, DecisionAdapter
from decision_evals.evolution.checkpoints import RunPaths, paths_for, run_name, write_manifest
from decision_evals.evolution.holdout import POOLS, assert_evolvable, census
from decision_evals.evolution.lineage import (
    Candidate,
    assert_searched,
    body_sha,
    find,
    load_lineage,
)
from decision_evals.evolution.venues import MOCK_MODEL, Venue, mock_call, venue_for
from decision_evals.generators import generate, load_all
from decision_evals.generators.generate import Item
from decision_evals.runner import CallFn
from decision_evals.solvers.arms import render_item

#: Where the human-written body a search starts from lives.
SEED_SKILL: Final = "skills/decision-making/SKILL.md"


class EvolveError(RuntimeError):
    """A run cannot be set up, or its result cannot be trusted."""


@dataclass(frozen=True, slots=True)
class EvolveRequest:
    """Everything a search is told before it starts.

    Written to ``run.json`` verbatim, so the manifest and the arguments cannot
    disagree.
    """

    engine: str
    target_model: str
    reflector_model: str | None = None
    train_seeds: tuple[int, ...] = (0, 1, 2)
    val_seeds: tuple[int, ...] = (1000, 1001)
    #: The whole-run call cap. On a venue that bills nothing this is the guard,
    #: which is why it has no default: a number nobody chose is not a budget.
    max_calls: int = 200
    #: Wall-clock seconds. The other guard, and the one that catches a run held
    #: at a free tier's rate limit, where no calls are being spent either.
    max_seconds: float = 3_600.0
    generation_calls: int = 400
    child_calls: int = 200
    #: Items per seed, after generation. Zero means all of them.
    limit: int = 0
    slug: str = ""

    def __post_init__(self) -> None:
        if not self.train_seeds or not self.val_seeds:
            raise EvolveError("a search needs training seeds and validation seeds, and has both")
        overlap = set(self.train_seeds) & set(self.val_seeds)
        if overlap:
            raise EvolveError(
                f"{sorted(overlap)} appear in both the training and validation seeds. An "
                "acceptance gate reading items the proposal was written against accepts "
                "everything."
            )
        assert_evolvable([*self.train_seeds, *self.val_seeds])


@dataclass(frozen=True, slots=True)
class EvolveResult:
    """What a finished search leaves behind."""

    paths: RunPaths
    winner: Candidate
    explored: int
    lineage: list[Candidate] = field(default_factory=list)


def seed_body(repo_root: Path, path: str = SEED_SKILL) -> str:
    """The human-written skill, frontmatter stripped.

    Frontmatter is the install contract -- name, description, the fields
    ``de check`` lints -- and not part of what the model reads. Handing it to an
    engine invites mutation of the one field
    ``scripts/run_triggers.py`` measures, which would make every published
    trigger number incomparable.

    Raises:
        EvolveError: No such file.
    """
    source = repo_root / path
    if not source.is_file():
        raise EvolveError(f"{path} is missing, so there is no seed for the search to start from")
    text = source.read_text(encoding="utf-8")
    if text.startswith("---"):
        _, _, rest = text.partition("---")
        _, sep, body = rest.partition("\n---")
        if sep:
            return body.lstrip("\n")
    return text


def items_for(seeds: Sequence[int], *, limit: int = 0) -> list[Item]:
    """Generate the corpus at each seed, in seed order.

    Seed order rather than interleaved, so a checkpoint reads as blocks and a
    truncated run is a whole number of seeds. ``limit`` caps items *per seed*,
    which keeps the strata balanced across seeds; capping the flattened list
    would take every stratum from the first seed and none from the last.
    """
    templates = load_all()
    items: list[Item] = []
    for seed in seeds:
        at_seed = [item for template in templates for item in generate(template, seed)]
        items.extend(at_seed[:limit] if limit else at_seed)
    return items


def budget_for(request: EvolveRequest, venue: Venue) -> NestedBudget:
    """Three nested ledgers sized from the request.

    Every one carries the call cap and the clock, because on these venues the
    dollar arm cannot fire and :class:`~decision_evals.budget.BudgetLedger`
    refuses a ledger that has nothing left to stop it with.
    """

    def ledger(calls: int) -> BudgetLedger:
        return BudgetLedger(
            limit_usd=0.0,
            bills=venue.bills,
            limit_calls=calls,
            limit_seconds=request.max_seconds,
        )

    return NestedBudget(
        run=ledger(request.max_calls),
        generation=ledger(min(request.generation_calls, request.max_calls)),
        child=ledger(min(request.child_calls, request.max_calls)),
    )


def evolve(
    request: EvolveRequest,
    *,
    repo_root: Path,
    git_sha: str,
    reflection_lm: Callable[[str], str] | None = None,
    on: date | None = None,
) -> EvolveResult:
    """Run one search and return its checked winner.

    Args:
        reflection_lm: What writes the proposals. A callable rather than a model
            name so the smoke path can pass a stub; a real run passes a hosted
            model, because a 4B target is a poor reflector for a skill it is
            meant to read.

    Raises:
        EvolveError: An unsupported engine, or GEPA is not installed.
        LineageError: The search explored one candidate, which is what a search
            whose every proposal failed also produces.
    """
    if request.engine != "gepa":
        raise EvolveError(
            f"engine {request.engine!r} has no driver here yet. `gepa` is wired end to "
            "end. `skillopt` has its environment and its venue configuration in "
            "`evolution/skillopt_env.py`, and what is missing is the flat config its "
            "`ReflACTTrainer` reads: guessing at those keys would produce a run whose "
            "settings nobody chose."
        )

    venue = venue_for(request.target_model)
    paths = paths_for(
        repo_root, run_name(engine=request.engine, git_sha=git_sha, on=on, slug=request.slug)
    )

    train = items_for(request.train_seeds, limit=request.limit)
    validation = items_for(request.val_seeds, limit=request.limit)
    if not train or not validation:
        raise EvolveError(
            "no items were generated. A search over an empty corpus scores zero "
            "everywhere and reports the seed as the winner."
        )

    write_manifest(
        paths,
        {
            "request": request,
            "git_sha": git_sha,
            "pools": {name: [span.start, span.stop] for name, span in POOLS.items()},
            "train": {"items": len(train), "seeds": census([i.seed for i in train])},
            "validation": {"items": len(validation), "seeds": census([i.seed for i in validation])},
        },
    )

    adapter = DecisionAdapter(
        venue=venue,
        call=_mock_oracle(venue, [*train, *validation]),
        checkpoint=paths.records,
        lineage=paths.lineage,
        budget=budget_for(request, venue),
        git_sha=git_sha,
        engine=request.engine,
        reflector_model=request.reflector_model,
    )

    result = _optimize(
        seed_candidate={COMPONENT: seed_body(repo_root)},
        trainset=train,
        valset=validation,
        adapter=adapter,
        reflection_lm=reflection_lm,
        max_metric_calls=request.max_calls,
        run_dir=str(paths.root / request.engine),
        logger=_FileLogger(paths.root / "search.log"),
    )

    lineage = load_lineage(paths.lineage)
    assert_searched(lineage)
    return EvolveResult(
        paths=paths,
        winner=find(lineage, body_sha(_best_body(result))),
        explored=len({c.candidate_sha for c in lineage}),
        lineage=lineage,
    )


def _mock_oracle(venue: Venue, items: Sequence[Item]) -> CallFn | None:
    """The answer key the mock venue needs, and ``None`` for every other venue.

    Built here rather than inside the venue because this is the only place that
    has both the items and their answers. A real venue gets ``None`` and the
    adapter derives its own call, so there is no path by which an answer key
    reaches a model.
    """
    if venue.model != MOCK_MODEL:
        return None
    return mock_call({render_item(item): item.answer for item in items})


class _FileLogger:
    """Where GEPA's own log goes.

    It logs every proposed candidate to stdout by default, and a Windows console
    is cp1252: the seed skill contains an arrow, and the first proposal killed
    the run with a UnicodeEncodeError from inside the engine's logger. Writing
    to a UTF-8 file in the run directory fixes the encoding and puts the search
    log where the rest of the search already is.
    """

    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = path.open("a", encoding="utf-8")

    def log(self, message: object) -> None:
        self._handle.write(f"{message}\n")
        self._handle.flush()


def _best_body(result: Any) -> str:
    """The body GEPA declared best.

    Read off the engine's own result rather than recomputed from the lineage.
    The acceptance rule is part of what an engine *is*, and a study comparing
    engines that substituted its own arithmetic for theirs would be comparing
    one rule to itself.

    Raises:
        EvolveError: The result carries no candidate. A search that returns
            nothing is a failure that otherwise surfaces as a hash of the empty
            string.
    """
    candidate = getattr(result, "best_candidate", None)
    body = (candidate or {}).get(COMPONENT) if isinstance(candidate, dict) else None
    if not body:
        raise EvolveError(
            f"the search returned no {COMPONENT!r} to freeze. An engine that finishes with "
            "no candidate has not produced a result, whatever its exit code says."
        )
    return str(body)


def _optimize(**kwargs: Any) -> Any:
    """Call ``gepa.optimize``, importing it at call time.

    Raises:
        EvolveError: GEPA is not installed. It is in the ``evolve`` dependency
            group, which the gate deliberately does not install.
    """
    try:
        import gepa
    except ImportError as exc:  # pragma: no cover - exercised by the import guard test
        raise EvolveError(
            "gepa is not installed. Run `python -m uv sync --group evolve`; the gate does "
            "not install it, because the engine under study must not become a dependency "
            "of the instrument."
        ) from exc
    return gepa.optimize(**kwargs)
