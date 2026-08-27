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

import json
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Final

from decision_evals.budget import BudgetError, BudgetLedger, NestedBudget
from decision_evals.evolution.adapter import COMPONENT, DecisionAdapter
from decision_evals.evolution.checkpoints import RunPaths, paths_for, run_name, write_manifest
from decision_evals.evolution.engine_prompts import LOCK_PATH as PROMPT_LOCK
from decision_evals.evolution.engine_prompts import ensure_installed
from decision_evals.evolution.holdout import POOLS, assert_evolvable, census
from decision_evals.evolution.lineage import (
    Candidate,
    assert_searched,
    body_sha,
    find,
    load_lineage,
)
from decision_evals.evolution.skillopt_env import build_env, train_config
from decision_evals.evolution.venues import (
    MOCK_MODEL,
    Venue,
    call_fn,
    mock_call,
    venue_for,
)
from decision_evals.generators import generate, load_all
from decision_evals.generators.generate import Item
from decision_evals.runner import CallFn, load_records
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
    #: 1002 rather than the adjacent 1001, which cannot be generated at all:
    #: `rel-008-contract-renew` fails to produce a robust, discriminative
    #: `renew` there in 500 attempts. Roughly one seed in sixty does this and
    #: it is always that template. A default that crashes on first contact
    #: with a real venue is worse than one that is merely arbitrary.
    val_seeds: tuple[int, ...] = (1000, 1002)
    #: The whole-run call cap, and on a venue that bills nothing it is the
    #: guard. The default is small on purpose: 200 calls is a smoke run, and a
    #: real search has to raise it deliberately and record the number it chose.
    max_calls: int = 200
    #: Wall-clock seconds. The other guard, and the one that catches a run held
    #: at a free tier's rate limit, where no calls are being spent either.
    max_seconds: float = 3_600.0
    generation_calls: int = 400
    child_calls: int = 200
    #: Items per seed in the training pool, after generation. Zero means all of
    #: them.
    limit: int = 0
    #: Items per seed in the validation pool. Zero follows ``limit``, which is
    #: the old single-knob behaviour. It is separate because the two pools are
    #: sized for different jobs: training wants breadth for a proposal to learn
    #: from, and validation is an acceptance gate paid for on every candidate,
    #: so it is the one that multiplies the call count.
    val_limit: int = 0
    slug: str = ""
    #: SkillOpt only. GEPA sizes its own batches from ``max_metric_calls``;
    #: SkillOpt requires these three and divides by two of them, so they are
    #: request fields rather than constants and reach the manifest with
    #: everything else the run was told.
    batch_size: int = 8
    sel_env_num: int = 20
    num_epochs: int = 1
    #: Output-token cap per call. Zero sends none, which is what every published
    #: run did. It is here rather than in the provider so the number a search
    #: ran under reaches `run.json`: a `qwen3:1.7b` call has generated 40,960
    #: tokens over 317 seconds without emitting an answer line, against 4,479 for
    #: the longest answer that ever finished, and an uncapped runaway spends a
    #: matched budget on one item.
    max_tokens: int = 0

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
    #: Empty when the engine finished on its own terms. Otherwise what stopped
    #: it, and a signal that ``winner`` was chosen here rather than by the
    #: engine.
    stop_reason: str = ""


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


def write_seed(path: Path, body: str) -> Path:
    """Write a starting body to disk and prove the engine will read it back.

    SkillOpt reads its starting skill off a file where GEPA takes a string, so
    this is the one place a body crosses the filesystem before a search sees it,
    and the study depends on both engines starting from the same body.

    ``newline=""`` because the default translates ``\\n`` to ``\\r\\n`` on
    Windows. That one turned out to be harmless -- the reader translates it
    back -- and it is still not left to chance, because which of the two ends
    normalises is not something this function gets to know.

    The read-back is the part that caught something. SkillOpt opens the file
    with no encoding, so it decodes by locale, and on a ``cp1252`` box a UTF-8
    body comes back mojibaked: eight typographic characters became twenty-four,
    3,428 became 3,444, and the engine spent its whole baseline scoring a body
    that was not the skill. Nothing raised. The number it produced -- 0.857
    against the same items GEPA scored the real body at 0.714 -- looked like a
    result.

    So the check is the engine's own read rather than a rule about locales:
    perform it, compare, and refuse. The fix is ``PYTHONUTF8=1``, which is not a
    patch to the engine but the environment it already has everywhere its
    locale is UTF-8.

    Raises:
        EvolveError: The default-encoding read does not return the body.
    """
    path.write_text(body, encoding="utf-8", newline="")
    with path.open() as handle:  # deliberately no encoding: what the engine does
        read_back = handle.read()
    if read_back != body:
        raise EvolveError(
            f"{path.name} does not read back as itself under this machine's default "
            f"encoding: {len(body)} characters written, {len(read_back)} read. SkillOpt's "
            "trainer opens the seed skill with no encoding, so it would search from a "
            "corrupted body and report a score for it. Set `PYTHONUTF8=1` in the "
            "environment and run again."
        )
    return path


def items_for(seeds: Sequence[int], *, limit: int = 0) -> list[Item]:
    """Generate the corpus at each seed, in seed order.

    Seed order rather than interleaved, so a checkpoint reads as blocks and a
    truncated run is a whole number of seeds.

    ``limit`` caps items per seed and **draws them evenly across templates and
    strata**, which the obvious implementation does not. A seed's corpus is
    template-major: ten templates of 28 items each, and those 28 are four
    variants crossed with seven strata in a fixed order. So ``at_seed[:limit]``
    with a limit of 20 returns twenty items from ``rel-001-vendor-outage`` and
    nothing else, and a search run against it optimises for vendor outages while
    the manifest records a corpus of ten scenarios.

    That is the same defect as sampling every seventh item and drawing one
    stratum forty times, which happened here on 2026-08-26 and is written up in
    the notebook. Both produce a full checkpoint and an aggregate that is
    arithmetically right about the wrong object.

    Template balance and stratum balance pull against each other below one item
    per template, so the order rotates: template ``t`` starts at stratum ``t``.
    Ten items then span ten templates *and* seven strata, where taking one item
    from each template would span ten templates and one stratum — every one of
    them ``d0-none``, the easiest, which is precisely the reading that made a
    ceilinged model look like a headroom problem.

    Striding within a template is the trap to avoid. A template's 28 items are
    variant-major and stratum-minor, so a stride of ``28 // per`` is usually a
    multiple of seven and draws the same stratum every time.
    """
    templates = load_all()
    items: list[Item] = []
    for seed in seeds:
        by_template = [list(generate(template, seed)) for template in templates]
        if not limit:
            items.extend(item for rows in by_template for item in rows)
            continue
        items.extend(_rotated(by_template)[:limit])
    return items


def _rotated(by_template: Sequence[Sequence[Item]]) -> list[Item]:
    """Every item once, ordered so any prefix spans templates and strata.

    Each template is grouped into its strata, and template ``t`` is read from an
    offset of ``t``, so the templates are never all on the same stratum at the
    same time.
    """
    grouped: list[list[list[Item]]] = []
    for rows in by_template:
        buckets: dict[tuple[int, str], list[Item]] = {}
        for item in rows:
            buckets.setdefault((item.n_distractors, item.position), []).append(item)
        grouped.append(list(buckets.values()))

    order: list[Item] = []
    depth = max((len(strata) * max(len(v) for v in strata) for strata in grouped), default=0)
    for cycle in range(depth):
        for offset, strata in enumerate(grouped):
            spot = (cycle + offset) % (len(strata) * max(len(v) for v in strata))
            variants = strata[spot % len(strata)]
            index = spot // len(strata)
            if index < len(variants):
                order.append(variants[index])
    return order


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
        reflection_lm: What writes GEPA's proposals. A callable rather than a
            model name so the smoke path can pass a stub; a real run passes a
            hosted model, because a 4B target is a poor reflector for a skill it
            is meant to read. SkillOpt ignores it and reads its optimizer out of
            its own config, which is a difference between the engines rather
            than an inconsistency here.

    Raises:
        EvolveError: An unsupported engine, or the engine is not installed.
        LineageError: The search explored one candidate, which is what a search
            whose every proposal failed also produces.
    """
    if request.engine not in DRIVERS:
        raise EvolveError(
            f"engine {request.engine!r} has no driver here. Wired end to end: {sorted(DRIVERS)}."
        )

    venue = venue_for(request.target_model)
    paths = paths_for(
        repo_root, run_name(engine=request.engine, git_sha=git_sha, on=on, slug=request.slug)
    )

    train = items_for(request.train_seeds, limit=request.limit)
    validation = items_for(request.val_seeds, limit=request.val_limit or request.limit)
    if not train or not validation:
        raise EvolveError(
            "no items were generated. A search over an empty corpus scores zero "
            "everywhere and reports the seed as the winner."
        )

    write_manifest(
        paths,
        {
            # `asdict` rather than the object: `write_manifest` unpacks a
            # dataclass only at the top level, and a nested one falls through to
            # `default=str`, which writes a Python repr into a JSON file.
            "request": asdict(request),
            "git_sha": git_sha,
            "pools": {name: [span.start, span.stop] for name, span in POOLS.items()},
            "train": {"items": len(train), "seeds": census([i.seed for i in train])},
            "validation": {"items": len(validation), "seeds": census([i.seed for i in validation])},
        },
    )

    adapter = DecisionAdapter(
        venue=venue,
        call=_mock_oracle(venue, [*train, *validation])
        or call_fn(venue, max_tokens=request.max_tokens or None),
        checkpoint=paths.records,
        lineage=paths.lineage,
        budget=budget_for(request, venue),
        git_sha=git_sha,
        engine=request.engine,
        reflector_model=request.reflector_model,
    )

    stop_reason = ""
    body = ""
    try:
        body = DRIVERS[request.engine](
            request,
            repo_root=repo_root,
            paths=paths,
            adapter=adapter,
            train=train,
            validation=validation,
            venue=venue,
            reflection_lm=reflection_lm,
        )
    except BudgetError as exc:
        # A budget is a stopping rule. One that also discards the search is a
        # defect, and it was one here: a 300-call cap fired mid-proposal, the
        # exception propagated out of `de evolve`, and fourteen candidates and
        # 287 scored records stayed on disk with nothing pointing at them.
        # The cap still stops the run -- it is not raised, retried or widened.
        stop_reason = str(exc)

    lineage = load_lineage(paths.lineage)
    assert_searched(lineage)
    winner = (
        find(lineage, body_sha(body))
        if body
        else _best_validated(lineage, paths.records, validation)
    )
    _freeze(paths, winner, stop_reason=stop_reason)
    return EvolveResult(
        paths=paths,
        winner=winner,
        explored=len({c.candidate_sha for c in lineage}),
        lineage=lineage,
        stop_reason=stop_reason,
    )


def _best_validated(
    lineage: list[Candidate], checkpoint: Path, validation: Sequence[Item]
) -> Candidate:
    """The best candidate that was scored on the *whole* validation pool.

    Only reached when a search was stopped before its engine declared a winner.
    **This is our arithmetic rather than the engine's acceptance rule**, and the
    difference is recorded in ``winner.json`` so that a study built on this body
    cannot quietly describe it as the engine's choice.

    Completeness is the whole of the care here. A lineage records the *first*
    score a candidate got, and for GEPA that is a three-item minibatch, so
    ranking on it compares 1.000-of-3 against 0.714-of-21 and picks the noise.
    Candidates evaluated on fewer than every validation item are not ranked at
    all -- not ranked lower, because a partial pass is not a worse score, it is
    an answer to a different question.

    Raises:
        EvolveError: No candidate completed a validation pass, so there is
            nothing here that can be compared with anything.
    """
    wanted = {item.item_id for item in validation}
    seen: dict[str, dict[str, bool]] = {}
    for record in load_records(checkpoint):
        if record.item_id in wanted and record.candidate_sha:
            seen.setdefault(record.candidate_sha, {})[record.item_id] = record.correct

    scored = [
        (sum(items.values()) / len(wanted), sha)
        for sha, items in seen.items()
        if len(items) == len(wanted)
    ]
    if not scored:
        raise EvolveError(
            f"the search stopped before any candidate was scored on all {len(wanted)} "
            "validation items, so there is no winner to freeze. Every candidate on file "
            "was seen on a minibatch only, and a minibatch score is not comparable with "
            "the seed's full pass. Resume with a larger budget."
        )
    return find(lineage, max(scored)[1])


def _freeze(paths: RunPaths, winner: Candidate, *, stop_reason: str = "") -> None:
    """Write the winning body where a later study can read it.

    Two files rather than one. ``winner.md`` is the body itself and is what an
    arm would be built from; ``winner.json`` carries the hash, the generation,
    the engine, the venue and the score, so a study can state which search
    produced its arm without re-deriving it from a lineage.

    The body is written last. A reader that finds ``winner.md`` finds a
    ``winner.json`` already beside it, rather than a body with no provenance.
    """
    paths.root.joinpath("winner.json").write_text(
        json.dumps(
            {
                "candidate_sha": winner.candidate_sha,
                "parent_sha": winner.parent_sha,
                "generation": winner.generation,
                "engine": winner.engine,
                "target_model": winner.target_model,
                "reflector_model": winner.reflector_model,
                "score": winner.score,
                "n_items": winner.n_items,
                "git_sha": winner.git_sha,
                "created_at": winner.created_at,
                # Which of the two selected this body. An engine's acceptance
                # rule is part of what the engine is; ours is not, and a study
                # citing this file has to be able to tell them apart.
                "winner_source": "lineage (budget-stopped)" if stop_reason else "engine",
                "stop_reason": stop_reason,
            },
            indent=2,
            ensure_ascii=False,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )
    paths.root.joinpath("winner.md").write_text(winner.body, encoding="utf-8")


def _drive_gepa(
    request: EvolveRequest,
    *,
    repo_root: Path,
    paths: RunPaths,
    adapter: DecisionAdapter,
    train: list[Item],
    validation: list[Item],
    venue: Venue,
    reflection_lm: Callable[[str], str] | None,
) -> str:
    """Run GEPA and return the body it declared best."""
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
    return _best_body(result)


def _drive_skillopt(
    request: EvolveRequest,
    *,
    repo_root: Path,
    paths: RunPaths,
    adapter: DecisionAdapter,
    train: list[Item],
    validation: list[Item],
    venue: Venue,
    reflection_lm: Callable[[str], str] | None,
) -> str:
    """Run SkillOpt's trainer and return the body it declared best.

    ``reflection_lm`` is ignored, and that is the difference between the two
    engines rather than an oversight. GEPA takes a callable for its proposal
    step; SkillOpt reads its optimizer out of the config and calls it through
    its own model layer, which is why
    :func:`~decision_evals.evolution.skillopt_env.venue_config` exists. A run
    that quietly routed SkillOpt's reflection through our callable would be
    measuring an engine nobody ships.

    The seed body is written to the run directory rather than pointed at
    ``skills/decision-making/SKILL.md``, for two reasons. The trainer reads its
    starting skill off disk and would otherwise get the frontmatter, which GEPA
    does not; both engines have to start from the same bytes or the comparison
    is between starting points. And the trainer rewrites what it is given, so
    aiming it at the tracked file would have a search editing the product.
    """
    out_root = paths.root / request.engine
    out_root.mkdir(parents=True, exist_ok=True)

    # No release of this engine carries its own reflection prompts, so a stock
    # install raises `FileNotFoundError` at the first step of any search. The
    # pinned copies go back where it looks for them, and what had to be restored
    # is written beside the run: which prompts a search reflected with is part of
    # what the search was.
    restored = ensure_installed(repo_root)
    (out_root / "restored-prompts.json").write_text(
        json.dumps(
            {"lock": PROMPT_LOCK, "restored": restored, "count": len(restored)},
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    start = write_seed(out_root / "skill_init.md", seed_body(repo_root))

    config = train_config(
        target=venue,
        optimizer=venue_for(request.reflector_model or request.target_model),
        out_root=out_root,
        skill_init=start,
        batch_size=request.batch_size,
        sel_env_num=min(request.sel_env_num, len(validation)),
        train_size=len(train),
        num_epochs=request.num_epochs,
    )
    # Beside the engine's own output rather than in `run.json`, which already
    # holds the request and is what `read_manifest` returns. Two manifests each
    # describing one layer beat one describing neither.
    (out_root / "config.json").write_text(
        json.dumps(_redacted(config), indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )

    _train(config, build_env(adapter, train=train, validation=validation))

    winner = out_root / "best_skill.md"
    if not winner.is_file():
        raise EvolveError(
            f"the trainer finished and wrote no {winner.name}. That file is how SkillOpt "
            "declares its winner, so there is nothing here to freeze -- and its own "
            "summary reports a best score regardless, which is why this is checked "
            "rather than read."
        )
    return winner.read_text(encoding="utf-8")


#: Which engines can actually be run, and what runs them. A dict rather than a
#: chain of ``if``, so the refusal message above names exactly what is wired.
DRIVERS: Final[dict[str, Any]] = {"gepa": _drive_gepa, "skillopt": _drive_skillopt}


def _redacted(config: dict[str, Any]) -> dict[str, Any]:
    """The config with every secret removed, for the manifest.

    Keys live in the environment and never in the tree, and a manifest is a
    file. ``results/evolution/`` is gitignored, which is a reason to be careful
    here rather than a reason not to be: an ignore rule is one line away from
    not applying.
    """
    return {
        key: ("<redacted>" if "api_key" in key or "token" in key else value)
        for key, value in config.items()
    }


def _train(config: dict[str, Any], env: Any) -> Any:
    """Call ``ReflACTTrainer(...).train()``, importing it at call time.

    Raises:
        EvolveError: SkillOpt is not installed.
    """
    try:
        from skillopt.engine.trainer import ReflACTTrainer
    except ImportError as exc:  # pragma: no cover - exercised by the import guard test
        raise EvolveError(
            "skillopt is not installed. Run `python -m uv sync --group evolve`; the gate "
            "does not install it, because the engine under study must not become a "
            "dependency of the instrument."
        ) from exc
    return ReflACTTrainer(config, env).train()


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
