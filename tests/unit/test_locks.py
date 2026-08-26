"""Tests for the integrity locks: arenas, pre-registration, budget.

These three modules carry a 100% branch-coverage floor, and the reason is
specific to what they are. A refusal branch that has never executed is a refusal
nobody has checked, and every one of them exists to stop a run that would
produce a dishonest number. A lock that silently fails open is worse than no
lock, because the run still completes and the number still looks fine.

So every ``raise`` below has a test asserting it fires.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from decision_evals.arenas import (
    ARENAS,
    MODELS,
    ArenaError,
    assert_may_emit_verdict,
    assert_may_revise_skill,
    assert_model_allowed,
    assert_split_allowed,
    policy_for,
    resolve_model,
)
from decision_evals.budget import (
    LEDGER_SCOPES,
    BudgetError,
    BudgetLedger,
    NestedBudget,
    estimate_cost_usd,
    project_cost,
)
from decision_evals.prereg import (
    Preregistration,
    PreregistrationError,
    RepoState,
    assert_runnable,
    load_preregistration,
    sha256_text,
)

SKILL = "# Evidence ledger\nVerify, then discard."
ANALYSIS = "def analyse():\n    return 1\n"


# ===========================================================================
# Arenas
# ===========================================================================


def test_every_arena_is_self_consistent() -> None:
    """A verdict from a public split, or from a revisable skill, is not a verdict."""
    for policy in ARENAS.values():
        if policy.emits_verdict:
            assert policy.split == "holdout"
            assert not policy.may_revise_skill
            assert policy.requires_preregistration


def test_exactly_one_arena_emits_verdicts() -> None:
    assert [name for name, p in ARENAS.items() if p.emits_verdict] == ["confirm"]


def test_an_unknown_arena_is_refused() -> None:
    with pytest.raises(ArenaError, match="unknown arena"):
        policy_for("production")


@pytest.mark.parametrize(
    ("arena", "model"),
    [
        ("dev", "mockllm/model"),
        ("dev", "ollama/qwen3:8b"),
        ("screen", "haiku"),
        ("screen", "claude-haiku-4-5-20251001"),
        ("confirm", "sonnet"),
        ("confirm", "claude-opus-4-6"),
    ],
)
def test_permitted_models_are_accepted(arena: str, model: str) -> None:
    assert assert_model_allowed(arena, model).name == arena


def test_a_frontier_model_is_refused_in_dev() -> None:
    """Spends quota on a run that cannot produce a verdict."""
    with pytest.raises(ArenaError, match="belongs to the 'confirm' arena, not 'dev'"):
        assert_model_allowed("dev", "opus")


@pytest.mark.parametrize(
    ("model", "arena", "backend", "vendor"),
    [
        ("agy/gemini-3.7-flash-low", "screen", "antigravity", "google"),
        ("agy/gpt-oss-120b-medium", "screen", "antigravity", "openai"),
        ("agy/claude-sonnet-4-6", "screen", "antigravity", "anthropic"),
    ],
)
def test_antigravity_models_resolve_to_screen(
    model: str, arena: str, backend: str, vendor: str
) -> None:
    """Every model on this backend screens, however capable the weights are.

    The venue cannot support a verdict -- the agent scaffold and its 57 tools are
    in context on every call and no flag removes them -- so the tier of the model
    is not what decides this.
    """
    entry = resolve_model(model)
    assert (entry.arena, entry.backend, entry.vendor) == (arena, backend, vendor)


@pytest.mark.parametrize(
    ("model", "vendor"),
    [
        ("nvbuild/meta/llama-3.3-70b-instruct", "meta"),
        ("nvbuild/qwen/qwen3-next-80b-a3b-instruct", "alibaba"),
        ("nvbuild/nvidia/llama-3.3-nemotron-super-49b-v1.5", "nvidia"),
        ("nvbuild/openai/gpt-oss-120b", "openai"),
        ("nvbuild/deepseek-ai/deepseek-v3.1", "deepseek"),
        ("nvbuild/google/gemma-3-27b-it", "google"),
        ("nvbuild/mistralai/mistral-small-24b-instruct", "mistral"),
    ],
)
def test_nvidia_build_models_resolve_to_screen(model: str, vendor: str) -> None:
    """A free hosted tier screens, because no receipt can be had from it.

    Narrower than the reason ``agy`` screens. There is no scaffold in context
    here; what is missing is the model card, so isolation is unverifiable and a
    verdict would rest on an absence.
    """
    entry = resolve_model(model)
    assert (entry.arena, entry.backend, entry.vendor) == ("screen", "openai_compatible", vendor)


def test_a_qwen_on_two_venues_is_two_venues() -> None:
    """The same collision ``agy/`` resolves, one venue further out.

    NVIDIA Build serves a ``qwen/qwen3-*`` and a local Ollama serves
    ``qwen3:4b``. Both are Qwen weights reached two ways, and only the label
    says which answered -- one of them free-tier hosted with no receipt, the
    other local with a model card.
    """
    assert resolve_model("ollama/qwen3:4b").arena == "dev"
    assert resolve_model("nvbuild/qwen/qwen3-next-80b-a3b-instruct").arena == "screen"


def test_an_nvidia_vendor_with_no_row_is_refused_rather_than_guessed() -> None:
    """The registry refuses an unknown vendor even under a known venue prefix."""
    with pytest.raises(ArenaError, match="is not in the registry"):
        resolve_model("nvbuild/ai21/jamba-1.5-large")


def test_the_same_weights_on_two_backends_are_two_venues() -> None:
    """The collision this registry exists to resolve.

    ``agy`` serves a model it calls ``claude-opus-4-6`` and ``claude -p`` accepts
    that id too. Reading them as one model would file a coding agent's answers
    under the arena whose results are evidence.
    """
    assert resolve_model("claude-opus-4-6").arena == "confirm"
    assert resolve_model("agy/claude-opus-4-6").arena == "screen"
    with pytest.raises(ArenaError, match="belongs to the 'screen' arena"):
        assert_model_allowed("confirm", "agy/claude-opus-4-6")


@pytest.mark.parametrize("alias", ["auto", "pro", "flash", "flash-lite", "default", "latest"])
def test_an_unpinned_alias_is_refused(alias: str) -> None:
    """A record naming a family cannot say which weights answered.

    ``agy`` defaults to ``--model auto``, so this is the refusal that stops a
    whole arm being run against an unknown.
    """
    with pytest.raises(ArenaError, match="names a family, not a set of weights"):
        resolve_model(alias)


def test_an_unknown_model_names_the_row_to_add() -> None:
    with pytest.raises(ArenaError, match="not in the registry"):
        resolve_model("llama-4-scout")


def test_a_backend_that_does_not_serve_the_model_is_refused() -> None:
    with pytest.raises(ArenaError, match="is served by 'antigravity'"):
        assert_model_allowed("screen", "agy/gemini-3.7-flash-low", backend="claude_code")


def test_arena_prefixes_are_derived_from_the_registry() -> None:
    """Two copies of a model's arena would eventually disagree, invisibly."""
    for name, policy in ARENAS.items():
        assert policy.model_prefixes == tuple(
            sorted(entry.prefix for entry in MODELS if entry.arena == name)
        )


def test_a_local_model_is_refused_in_confirm() -> None:
    """Would produce a verdict about an entirely different model."""
    with pytest.raises(ArenaError, match="different experiment"):
        assert_model_allowed("confirm", "ollama/qwen3:8b")


def test_screening_models_are_refused_in_confirm() -> None:
    with pytest.raises(ArenaError):
        assert_model_allowed("confirm", "haiku")


def test_revising_a_skill_is_refused_in_the_locked_arena() -> None:
    with pytest.raises(ArenaError, match="hash-locked"):
        assert_may_revise_skill("confirm")


@pytest.mark.parametrize("arena", ["dev", "screen"])
def test_revision_is_permitted_where_iteration_happens(arena: str) -> None:
    assert_may_revise_skill(arena)


@pytest.mark.parametrize("arena", ["dev", "screen"])
def test_a_verdict_is_refused_outside_confirm(arena: str) -> None:
    with pytest.raises(ArenaError, match="not evidence"):
        assert_may_emit_verdict(arena)


def test_confirm_may_emit_a_verdict() -> None:
    assert_may_emit_verdict("confirm")


def test_the_holdout_cannot_be_spent_on_screening() -> None:
    """Contamination cannot be undone within a seed."""
    with pytest.raises(ArenaError, match="runs on the 'public' split"):
        assert_split_allowed("screen", "holdout")


def test_confirm_refuses_the_public_split() -> None:
    with pytest.raises(ArenaError, match="runs on the 'holdout' split"):
        assert_split_allowed("confirm", "public")


def test_matching_splits_pass() -> None:
    assert_split_allowed("dev", "public")
    assert_split_allowed("confirm", "holdout")


# ===========================================================================
# Pre-registration
# ===========================================================================


def _prereg_dict(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "skill": "evidence-ledger",
        "version": 1,
        "hypothesis": "The ledger raises accuracy on distractor-present items.",
        "primary_metric": "accuracy_distractor_present",
        "n_items": 280,
        "minimum_detectable_effect": 0.08,
        "alpha": 0.05,
        "guards": ["no_harm_clean", "beats_placebo", "beats_cot", "format_integrity"],
        "stopping_rule": "fixed N, no interim analysis",
        "difficulty_band": [0.35, 0.75],
        "budget_usd": 40.0,
        "skill_sha256": sha256_text(SKILL),
        "analysis_script_sha256": sha256_text(ANALYSIS),
    }
    base.update(overrides)
    return base


def _prereg(**overrides: Any) -> Preregistration:
    return Preregistration.model_validate(_prereg_dict(**overrides))


CLEAN_REPO = RepoState(committed_and_clean=True, is_ancestor_of_head=True, precedes_results=True)


def _run(prereg: Preregistration | None = None, **overrides: Any) -> None:
    kwargs: dict[str, Any] = {
        "repo": CLEAN_REPO,
        "skill_body": SKILL,
        "analysis_source": ANALYSIS,
        "baseline_accuracy": 0.55,
        "projected_cost_usd": 12.0,
    }
    kwargs.update(overrides)
    assert_runnable(prereg or _prereg(), **kwargs)


def test_a_well_formed_run_is_permitted() -> None:
    """Guards the rest: each test below asserts a *deviation* is refused."""
    _run()


def test_line_endings_do_not_break_the_hash() -> None:
    """Otherwise a Windows checkout fails a lock over a difference that is not one."""
    assert sha256_text("a\r\nb") == sha256_text("a\nb") == sha256_text("a\rb")


def test_an_uncommitted_preregistration_is_refused() -> None:
    repo = RepoState(committed_and_clean=False, is_ancestor_of_head=True, precedes_results=True)
    with pytest.raises(PreregistrationError, match="entirely in its timestamp"):
        _run(repo=repo)


def test_a_preregistration_off_the_current_history_is_refused() -> None:
    repo = RepoState(committed_and_clean=True, is_ancestor_of_head=False, precedes_results=True)
    with pytest.raises(PreregistrationError, match="not an ancestor of HEAD"):
        _run(repo=repo)


def test_a_preregistration_written_after_the_results_is_refused() -> None:
    repo = RepoState(committed_and_clean=True, is_ancestor_of_head=True, precedes_results=False)
    with pytest.raises(PreregistrationError, match="postdiction"):
        _run(repo=repo)


def test_one_changed_character_in_the_skill_aborts_the_run() -> None:
    """The lock the whole design turns on."""
    with pytest.raises(PreregistrationError, match="skill hash mismatch"):
        _run(skill_body=SKILL + " ")


def test_the_abort_message_names_the_next_version() -> None:
    with pytest.raises(PreregistrationError, match=r"evidence-ledger-v2\.yaml"):
        _run(skill_body="different")


def test_editing_the_analysis_script_aborts_the_run() -> None:
    """A pre-registered metric means nothing if its code can be rewritten."""
    with pytest.raises(PreregistrationError, match="analysis script hash mismatch"):
        _run(analysis_source=ANALYSIS + "# tweak\n")


@pytest.mark.parametrize("accuracy", [0.20, 0.34, 0.76, 0.99])
def test_a_baseline_outside_the_difficulty_band_is_refused(accuracy: float) -> None:
    with pytest.raises(PreregistrationError, match="difficulty band"):
        _run(baseline_accuracy=accuracy)


@pytest.mark.parametrize("accuracy", [0.35, 0.55, 0.75])
def test_the_difficulty_band_is_inclusive(accuracy: float) -> None:
    _run(baseline_accuracy=accuracy)


def test_a_run_over_budget_is_refused() -> None:
    with pytest.raises(PreregistrationError, match="optional-stopping"):
        _run(projected_cost_usd=40.01)


def test_a_run_exactly_on_budget_is_permitted() -> None:
    _run(projected_cost_usd=40.0)


# -- loading ----------------------------------------------------------------


def test_a_preregistration_round_trips(tmp_path: Path) -> None:
    path = tmp_path / "evidence-ledger-v1.yaml"
    path.write_text(yaml.safe_dump(_prereg_dict()), encoding="utf-8")
    assert load_preregistration(path).skill == "evidence-ledger"


def test_a_missing_preregistration_is_an_error(tmp_path: Path) -> None:
    with pytest.raises(PreregistrationError):
        load_preregistration(tmp_path / "absent.yaml")


def test_a_non_mapping_preregistration_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "listy.yaml"
    path.write_text(yaml.safe_dump(["not", "a", "mapping"]), encoding="utf-8")
    with pytest.raises(PreregistrationError, match="expected a mapping"):
        load_preregistration(path)


def test_malformed_yaml_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "broken.yaml"
    path.write_text("key: [unclosed\n", encoding="utf-8")
    with pytest.raises(PreregistrationError):
        load_preregistration(path)


def test_an_invalid_preregistration_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text(yaml.safe_dump(_prereg_dict(alpha=1.5)), encoding="utf-8")
    with pytest.raises(PreregistrationError):
        load_preregistration(path)


def test_a_malformed_hash_is_rejected() -> None:
    """A truncated or uppercase hash would never match and would fail confusingly later."""
    with pytest.raises(Exception, match="skill_sha256"):
        _prereg(skill_sha256="abc123")


def test_a_preregistration_needs_at_least_one_guard() -> None:
    with pytest.raises(Exception, match="guards"):
        _prereg(guards=[])


# ===========================================================================
# Budget
# ===========================================================================


def test_cost_projection_multiplies_every_factor() -> None:
    assert project_cost(n_items=280, n_arms=4, repeats=2, usd_per_item=0.01) == pytest.approx(22.4)


def test_repeats_default_to_two() -> None:
    """A one-repeat run is not the cheap version of this experiment.

    Harness variance makes single-run point estimates uninterpretable, so the
    default is the design, not a convenience.
    """
    assert project_cost(n_items=10, n_arms=2, usd_per_item=1.0) == 40.0


@pytest.mark.parametrize(
    "kwargs",
    [
        {"n_items": 0, "n_arms": 4, "repeats": 2},
        {"n_items": 10, "n_arms": 0, "repeats": 2},
        {"n_items": 10, "n_arms": 4, "repeats": 0},
    ],
)
def test_a_degenerate_projection_is_refused(kwargs: dict[str, int]) -> None:
    """A projection of zero would pass any budget check -- the one silent wrong answer."""
    with pytest.raises(BudgetError, match="at least one item"):
        project_cost(usd_per_item=0.01, **kwargs)


@pytest.mark.parametrize("rate", [0.0, -1.0])
def test_a_non_positive_rate_is_refused(rate: float) -> None:
    with pytest.raises(BudgetError, match="must be positive"):
        project_cost(n_items=10, n_arms=4, usd_per_item=rate)


def test_the_ledger_is_immutable() -> None:
    """A checkpointed run resumes from a serialisable value, not an accumulator."""
    start = BudgetLedger(limit_usd=10.0)
    after = start.record(3.0)
    assert start.spent_usd == 0.0
    assert after.spent_usd == 3.0
    assert after.remaining_usd == 7.0


def test_remaining_never_goes_negative() -> None:
    assert BudgetLedger(limit_usd=10.0, spent_usd=12.0).remaining_usd == 0.0


def test_exhaustion_is_reported_at_the_limit() -> None:
    assert not BudgetLedger(limit_usd=10.0, spent_usd=9.99).exhausted
    assert BudgetLedger(limit_usd=10.0, spent_usd=10.0).exhausted


def test_a_negative_cost_is_refused() -> None:
    with pytest.raises(BudgetError, match="cannot be negative"):
        BudgetLedger(limit_usd=10.0).record(-1.0)


def test_an_affordable_call_passes() -> None:
    BudgetLedger(limit_usd=10.0, spent_usd=9.0).assert_can_afford(1.0)


def test_a_call_that_would_overrun_is_refused_before_it_happens() -> None:
    """Checked before the call, so the limit is a limit rather than a report."""
    with pytest.raises(BudgetError, match="past the"):
        BudgetLedger(limit_usd=10.0, spent_usd=9.0).assert_can_afford(1.01)


# -- the three limits -------------------------------------------------------
#
# Dollars were the only unit while every call went through a subscription that
# priced them. A local model and a free tier both report zero, so a ledger
# carrying only a dollar cap authorises everything it is ever shown.


def test_a_free_venue_with_only_a_dollar_cap_is_refused() -> None:
    """The refusal the whole free-tier venue rests on."""
    with pytest.raises(BudgetError, match="cannot fire"):
        BudgetLedger(limit_usd=10.0, bills=False)


@pytest.mark.parametrize("guard", [{"limit_calls": 100}, {"limit_seconds": 600.0}])
def test_a_free_venue_with_a_guard_that_can_bind_is_allowed(guard: dict[str, float]) -> None:
    assert BudgetLedger(limit_usd=0.0, bills=False, **guard)  # type: ignore[arg-type]


def test_a_call_cap_below_one_is_refused() -> None:
    with pytest.raises(BudgetError, match="at least 1"):
        BudgetLedger(limit_usd=10.0, limit_calls=0)


def test_a_clock_cap_at_or_below_zero_is_refused() -> None:
    with pytest.raises(BudgetError, match="must be positive"):
        BudgetLedger(limit_usd=10.0, limit_seconds=0.0)


def test_an_unset_cap_reports_no_remainder_rather_than_zero() -> None:
    """None and 0 are opposite answers, and confusing them stops a run early."""
    ledger = BudgetLedger(limit_usd=10.0)
    assert ledger.remaining_calls is None
    assert ledger.remaining_seconds is None


def test_a_set_cap_reports_what_is_left() -> None:
    ledger = BudgetLedger(limit_usd=10.0, limit_calls=10, limit_seconds=60.0)
    charged = ledger.record(0.0, calls=4, seconds=15.0)
    assert charged.remaining_calls == 6
    assert charged.remaining_seconds == 45.0


def test_neither_remainder_goes_negative() -> None:
    over = BudgetLedger(
        limit_usd=10.0, limit_calls=2, spent_calls=5, limit_seconds=10.0, elapsed_seconds=30.0
    )
    assert over.remaining_calls == 0
    assert over.remaining_seconds == 0.0


def test_exhaustion_reads_every_limit() -> None:
    assert BudgetLedger(limit_usd=10.0, limit_calls=5, spent_calls=5).exhausted
    assert BudgetLedger(limit_usd=10.0, limit_seconds=60.0, elapsed_seconds=60.0).exhausted
    assert not BudgetLedger(
        limit_usd=10.0, spent_usd=1.0, limit_calls=5, spent_calls=1, limit_seconds=60.0
    ).exhausted


def test_a_free_venue_is_not_exhausted_by_a_dollar_figure() -> None:
    """The mirror of the construction refusal: zero cost cannot exhaust anything."""
    spent = BudgetLedger(limit_usd=0.0, spent_usd=0.0, bills=False, limit_calls=5)
    assert not spent.exhausted


@pytest.mark.parametrize(
    "charge",
    [
        {"calls": -1},
        {"seconds": -1.0},
        {"seconds": 1.0, "backoff_seconds": -1.0},
    ],
)
def test_a_negative_charge_is_refused(charge: dict[str, float]) -> None:
    with pytest.raises(BudgetError, match="cannot be negative"):
        BudgetLedger(limit_usd=10.0).record(**charge)  # type: ignore[arg-type]


def test_backoff_longer_than_the_call_it_is_part_of_is_refused() -> None:
    """Backoff is a share of the elapsed time, so it cannot exceed it."""
    with pytest.raises(BudgetError, match="part of the elapsed time"):
        BudgetLedger(limit_usd=10.0).record(0.0, seconds=2.0, backoff_seconds=3.0)


def test_waiting_can_be_booked_without_a_call() -> None:
    """A backpressure pause burns the clock and nothing else."""
    waited = BudgetLedger(limit_usd=10.0, limit_seconds=600.0).record(
        calls=0, seconds=45.0, backoff_seconds=45.0
    )
    assert waited.spent_calls == 0
    assert waited.elapsed_seconds == 45.0
    assert waited.backoff_seconds == 45.0


def test_a_call_past_the_call_cap_is_refused_before_it_happens() -> None:
    with pytest.raises(BudgetError, match="past the 10-call limit"):
        BudgetLedger(limit_usd=10.0, limit_calls=10, spent_calls=10).assert_can_afford()


def test_a_call_past_the_clock_cap_is_refused_before_it_happens() -> None:
    ledger = BudgetLedger(
        limit_usd=10.0, limit_seconds=600.0, elapsed_seconds=590.0, backoff_seconds=300.0
    )
    with pytest.raises(BudgetError, match="waiting out rate limits"):
        ledger.assert_can_afford(seconds=30.0)


def test_a_free_venue_is_not_stopped_by_the_dollar_arm() -> None:
    BudgetLedger(limit_usd=0.0, bills=False, limit_calls=10).assert_can_afford(5.0)


def test_a_call_inside_every_cap_passes() -> None:
    BudgetLedger(
        limit_usd=10.0, spent_usd=1.0, limit_calls=10, spent_calls=1, limit_seconds=600.0
    ).assert_can_afford(1.0, seconds=10.0)


def test_a_reset_keeps_the_limits_and_drops_the_totals() -> None:
    spent = BudgetLedger(limit_usd=10.0, limit_calls=10, limit_seconds=60.0).record(
        2.0, calls=3, seconds=20.0, backoff_seconds=5.0
    )
    fresh = spent.reset()
    assert (fresh.limit_usd, fresh.limit_calls, fresh.limit_seconds) == (10.0, 10, 60.0)
    assert (fresh.spent_usd, fresh.spent_calls, fresh.elapsed_seconds, fresh.backoff_seconds) == (
        0.0,
        0,
        0.0,
        0.0,
    )


# -- the nested budget ------------------------------------------------------


def _nested(*, run: int = 100, generation: int = 20, child: int = 5) -> NestedBudget:
    return NestedBudget(
        run=BudgetLedger(limit_usd=0.0, bills=False, limit_calls=run),
        generation=BudgetLedger(limit_usd=0.0, bills=False, limit_calls=generation),
        child=BudgetLedger(limit_usd=0.0, bills=False, limit_calls=child),
    )


@pytest.mark.parametrize("scope", LEDGER_SCOPES)
def test_the_refusal_names_the_scope_that_refused(scope: str) -> None:
    """A bare "over budget" is not actionable when three budgets are in play."""
    caps = {"run": 100, "generation": 20, "child": 5}
    budget = _nested(**{**caps, scope: 1})
    budget = budget.record(calls=1)
    with pytest.raises(BudgetError, match=f"the {scope} budget refused"):
        budget.assert_can_afford()


def test_one_call_is_charged_to_all_three_scopes() -> None:
    charged = _nested().record(calls=1, seconds=3.0, backoff_seconds=1.0)
    for scope in LEDGER_SCOPES:
        ledger: BudgetLedger = getattr(charged, scope)
        assert (ledger.spent_calls, ledger.elapsed_seconds, ledger.backoff_seconds) == (1, 3.0, 1.0)


def test_a_new_generation_rolls_both_inner_ledgers_over() -> None:
    spent = _nested().record(calls=3)
    rolled = spent.start_generation()
    assert rolled.run.spent_calls == 3
    assert rolled.generation.spent_calls == 0
    assert rolled.child.spent_calls == 0


def test_a_new_child_leaves_the_generation_accumulating() -> None:
    """A per-child cap bounds one pathological candidate, not the generation."""
    spent = _nested().record(calls=3)
    rolled = spent.start_child()
    assert rolled.run.spent_calls == 3
    assert rolled.generation.spent_calls == 3
    assert rolled.child.spent_calls == 0


def test_a_run_that_can_afford_the_call_everywhere_passes() -> None:
    _nested().assert_can_afford()


# -- cost estimation --------------------------------------------------------


def test_a_long_prompt_is_authorised_at_more_than_a_short_one() -> None:
    assert estimate_cost_usd(prompt_chars=400_000) > 20 * estimate_cost_usd(prompt_chars=1_500)


def test_the_estimate_never_falls_below_the_floor() -> None:
    assert estimate_cost_usd(prompt_chars=0) == pytest.approx(0.005)


@pytest.mark.parametrize(
    ("achieved_tokens", "observed_usd"),
    [(1_533, 0.0052), (25_489, 0.0298), (63_313, 0.0714), (101_142, 0.2296)],
)
def test_the_estimate_covers_every_call_the_canary_actually_made(
    achieved_tokens: int, observed_usd: float
) -> None:
    """An authorisation that under-counts is a budget that is not a budget.

    Canary filler measured 6.01 chars/token; the estimator assumes 4.0. The
    mismatch is deliberate and one-directional -- it over-estimates.
    """
    assert estimate_cost_usd(prompt_chars=int(achieved_tokens * 6.0)) >= observed_usd


def test_a_negative_length_is_a_bug_not_a_free_call() -> None:
    with pytest.raises(BudgetError, match="cannot be negative"):
        estimate_cost_usd(prompt_chars=-1)
