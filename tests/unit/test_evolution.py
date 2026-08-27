"""Tests for the evolution package.

The refusals are the point. Everything here exists because a search that ran
badly and a search that ran well produce the same shape of output, so each
check is a place where the difference becomes visible: a seed the engine may
not see, a lineage whose winner had no competitor, a body whose hash does not
match the record it is filed under.
"""

from __future__ import annotations

import importlib.util
import itertools
import json
import re
import time
from dataclasses import asdict
from datetime import date
from pathlib import Path

import pytest

from decision_evals.budget import BudgetError
from decision_evals.evolution.adapter import (
    COMPONENT,
    RESUME_FIELDS,
    AdapterError,
    DecisionAdapter,
    Trace,
    _feedback,
)
from decision_evals.evolution.checkpoints import (
    CheckpointError,
    paths_for,
    read_manifest,
    run_name,
    write_manifest,
)
from decision_evals.evolution.engine_prompts import (
    LOCK_PATH,
    VENDOR_ROOT,
    PromptError,
    ensure_installed,
    install,
    load_lock,
    verify_vendored,
)
from decision_evals.evolution.holdout import (
    HOLDOUT_FLOOR,
    POOLS,
    HoldoutBreachError,
    _derive,
    assert_evolvable,
    census,
    holdout_seeds,
    mint,
    pool_of,
)
from decision_evals.evolution.lineage import (
    Candidate,
    LineageError,
    append_candidate,
    assert_searched,
    best_scored,
    body_sha,
    find,
    load_lineage,
)
from decision_evals.evolution.run import (
    DRIVERS,
    Deadline,
    EvolveError,
    EvolveRequest,
    _best_validated,
    _freeze,
    _redacted,
    budget_for,
    evolve,
    items_for,
    seed_body,
    write_seed,
)
from decision_evals.evolution.skillopt_env import (
    COMPAT_AUTH,
    REFLECT_SETTINGS,
    TASK_TYPES,
    SkillOptError,
    _deployment,
    build_env,
    train_config,
    venue_config,
)
from decision_evals.evolution.solo import (
    LOCK_NAME,
    ConcurrencyError,
    Solo,
    read_holder,
    unsafe,
)
from decision_evals.evolution.venues import (
    MOCK_LADDER,
    MOCK_MARKER,
    MOCK_MODEL,
    VenueError,
    call_fn,
    isolation_receipt,
    key_is_present,
    mock_call,
    mock_reflector,
    venue_for,
)
from decision_evals.generators.generate import Item
from decision_evals.runner import load_records
from decision_evals.solvers.arms import render_item

#: The engines are the *subject* of this study, so they live in the `evolve`
#: dependency group and the gate never installs them. A test that needs one is
#: skipped rather than failed: a red gate on a missing subject would push
#: somebody to make the instrument depend on the thing it measures.
#: This repository, from a test file two directories down.
REPO_ROOT = Path(__file__).resolve().parents[2]

needs_skillopt = pytest.mark.skipif(
    importlib.util.find_spec("skillopt") is None,
    reason="skillopt is in the `evolve` group, which the gate does not install",
)
needs_gepa = pytest.mark.skipif(
    importlib.util.find_spec("gepa") is None,
    reason="gepa is in the `evolve` group, which the gate does not install",
)


class _Scored:
    """A stand-in for GEPA's ``EvaluationBatch``.

    ``make_reflective_dataset`` reads one attribute off it, and building the real
    one needs the engine installed. A stub keeps those tests running in a gate
    that deliberately does not have the engine; the one test that the real type
    comes back is marked and skipped there instead.
    """

    def __init__(self, trajectories: list[Trace] | None) -> None:
        self.trajectories = trajectories


# -- the seed firewall ------------------------------------------------------


@pytest.mark.parametrize(
    ("seed", "expected"),
    [(0, "train"), (999, "train"), (1000, "validation"), (HOLDOUT_FLOOR, "holdout"), (5000, None)],
)
def test_a_seed_reports_its_pool(seed: int, expected: str | None) -> None:
    assert pool_of(seed) == expected


def test_training_and_validation_seeds_pass() -> None:
    assert_evolvable([0, 1, 1000])


def test_a_holdout_seed_is_refused() -> None:
    """The refusal the whole package exists for."""
    with pytest.raises(HoldoutBreachError, match="fitted the test set"):
        assert_evolvable([0, HOLDOUT_FLOOR])


def test_a_seed_in_no_pool_is_refused() -> None:
    """An unassigned seed is neither training nor test, which is worse than either."""
    with pytest.raises(HoldoutBreachError, match="in no pool"):
        assert_evolvable([0, 5000])


def test_both_breaches_are_reported_at_once() -> None:
    with pytest.raises(HoldoutBreachError) as caught:
        assert_evolvable([HOLDOUT_FLOOR, 5000])
    assert "holdout seed" in str(caught.value)
    assert "in no pool" in str(caught.value)


def test_holdout_seeds_are_reproducible_from_the_passphrase() -> None:
    assert holdout_seeds("correct horse", 20) == holdout_seeds("correct horse", 20)


def test_a_different_passphrase_draws_a_different_split() -> None:
    assert holdout_seeds("one", 20) != holdout_seeds("two", 20)


def test_every_drawn_seed_is_in_the_holdout_pool_and_distinct() -> None:
    drawn = holdout_seeds("a passphrase", 200)
    assert len(set(drawn)) == 200
    assert all(pool_of(seed) == "holdout" for seed in drawn)


def test_an_empty_passphrase_is_refused() -> None:
    """A split anyone reading this file can rebuild is not a private split."""
    with pytest.raises(ValueError, match="not in the tree"):
        holdout_seeds("   ", 10)


@pytest.mark.parametrize("count", [0, 10_000])
def test_a_count_that_cannot_be_drawn_is_refused(count: int) -> None:
    with pytest.raises(ValueError, match="count must be between"):
        holdout_seeds("a passphrase", count)


def test_the_census_counts_what_it_could_not_classify() -> None:
    assert census([0, 1, 1000, HOLDOUT_FLOOR, 5000]) == {
        "train": 2,
        "validation": 1,
        "holdout": 1,
        "unassigned": 1,
    }


def test_the_pools_do_not_overlap() -> None:
    spans = list(POOLS.values())
    for index, span in enumerate(spans):
        for other in spans[index + 1 :]:
            assert not set(span) & set(other)


# -- the lineage ------------------------------------------------------------


def _candidate(**overrides: object) -> Candidate:
    body = str(overrides.pop("body", "# A skill\n\nDo the thing."))
    fields: dict[str, object] = {
        "candidate_sha": body_sha(body),
        "parent_sha": None,
        "generation": 0,
        "engine": "gepa",
        "target_model": MOCK_MODEL,
        "reflector_model": None,
        "seeds": (0, 1),
        "n_items": 8,
        "score": 0.5,
        "accepted": False,
        "git_sha": "abc1234",
        "created_at": "2026-08-26T00:00:00+00:00",
        "body": body,
    }
    fields.update(overrides)
    return Candidate(**fields)  # type: ignore[arg-type]


def test_the_hash_is_of_the_exact_bytes() -> None:
    """Trailing whitespace is something an engine mutates, so it is part of the key."""
    assert body_sha("a body") != body_sha("a body ")


def test_a_candidate_whose_hash_does_not_match_its_body_is_refused() -> None:
    with pytest.raises(LineageError, match="not the hash of this body"):
        _candidate(candidate_sha=body_sha("something else"))


def test_an_unknown_engine_is_refused() -> None:
    with pytest.raises(LineageError, match="unknown engine"):
        _candidate(engine="handwritten")


def test_the_first_generation_has_no_parent() -> None:
    with pytest.raises(LineageError, match="no parent"):
        _candidate(generation=0, parent_sha=body_sha("a parent"))


def test_a_later_generation_needs_one() -> None:
    """A search whose children are unparented is a list, not a lineage."""
    with pytest.raises(LineageError, match="has no parent"):
        _candidate(generation=2, parent_sha=None)


def test_a_lineage_round_trips(tmp_path: Path) -> None:
    path = tmp_path / "lineage.jsonl"
    first = _candidate()
    second = _candidate(body="# Better\n", generation=1, parent_sha=first.candidate_sha)
    append_candidate(path, first)
    append_candidate(path, second)
    assert load_lineage(path) == [first, second]


def test_a_missing_lineage_reads_as_empty(tmp_path: Path) -> None:
    assert load_lineage(tmp_path / "nothing.jsonl") == []


def test_a_truncated_line_is_reported_rather_than_skipped(tmp_path: Path) -> None:
    """Skipping it would under-count the search, and the count is what is checked."""
    path = tmp_path / "lineage.jsonl"
    append_candidate(path, _candidate())
    path.write_text(path.read_text(encoding="utf-8") + '{"candidate_sha": "ab', encoding="utf-8")
    with pytest.raises(LineageError, match="is not JSON"):
        load_lineage(path)


def test_a_line_that_is_not_a_candidate_is_reported(tmp_path: Path) -> None:
    path = tmp_path / "lineage.jsonl"
    path.write_text(json.dumps({"who": "knows"}) + "\n", encoding="utf-8")
    with pytest.raises(LineageError, match="is not a candidate"):
        load_lineage(path)


def test_blank_lines_are_ignored(tmp_path: Path) -> None:
    path = tmp_path / "lineage.jsonl"
    append_candidate(path, _candidate())
    path.write_text(path.read_text(encoding="utf-8") + "\n\n", encoding="utf-8")
    assert len(load_lineage(path)) == 1


def test_a_search_of_one_is_refused() -> None:
    """A run that explored one candidate and a run whose search failed look alike."""
    with pytest.raises(LineageError, match="under the floor"):
        assert_searched([_candidate()])


def test_a_search_of_two_passes() -> None:
    first = _candidate()
    assert_searched(
        [first, _candidate(body="# Two\n", generation=1, parent_sha=first.candidate_sha)]
    )


def test_the_best_score_wins_and_ties_break_late() -> None:
    first = _candidate(score=0.5)
    second = _candidate(body="# Two\n", generation=1, parent_sha=first.candidate_sha, score=0.5)
    assert best_scored([first, second]) is second


def test_an_unscored_search_has_no_winner() -> None:
    with pytest.raises(LineageError, match="no candidate carries a score"):
        best_scored([_candidate(score=None)])


def test_a_declared_winner_is_resolved_by_hash() -> None:
    first = _candidate()
    assert find([first], first.candidate_sha) is first


def test_a_winner_that_was_never_scored_here_is_refused() -> None:
    """An engine returning a body this record cannot account for."""
    with pytest.raises(LineageError, match="appears nowhere in this lineage"):
        find([_candidate()], body_sha("never evaluated"))


# -- the run directory ------------------------------------------------------


def test_a_run_name_carries_the_date_the_commit_and_the_engine() -> None:
    assert run_name(engine="gepa", git_sha="abc1234def", on=date(2026, 8, 26)) == (
        "2026-08-26-abc1234-gepa"
    )


def test_a_slug_is_appended_and_flattened() -> None:
    name = run_name(engine="gepa", git_sha="abc1234", on=date(2026, 8, 26), slug="First Try!")
    assert name == "2026-08-26-abc1234-gepa-first-try"


def test_a_truncated_sha_is_refused() -> None:
    """Two runs at two commits would otherwise collide silently."""
    with pytest.raises(CheckpointError, match="seven-character convention"):
        run_name(engine="gepa", git_sha="abc")


def test_a_run_name_defaults_to_today() -> None:
    assert run_name(engine="gepa", git_sha="abc1234").startswith(date.today().isoformat())


def test_the_manifest_round_trips(tmp_path: Path) -> None:
    paths = paths_for(tmp_path, "2026-08-26-abc1234-gepa")
    write_manifest(paths, {"engine": "gepa", "seeds": [0, 1]})
    assert read_manifest(paths)["engine"] == "gepa"


def test_a_dataclass_manifest_is_serialised(tmp_path: Path) -> None:
    paths = paths_for(tmp_path, "2026-08-26-abc1234-gepa")
    write_manifest(paths, EvolveRequest(engine="gepa", target_model=MOCK_MODEL))
    assert read_manifest(paths)["target_model"] == MOCK_MODEL


def test_records_with_no_manifest_cannot_be_attributed(tmp_path: Path) -> None:
    with pytest.raises(CheckpointError, match="nothing says what this run was"):
        read_manifest(paths_for(tmp_path, "2026-08-26-abc1234-gepa"))


def test_the_three_files_sit_under_one_directory(tmp_path: Path) -> None:
    paths = paths_for(tmp_path, "a-run")
    assert {p.parent for p in (paths.records, paths.lineage, paths.manifest)} == {paths.root}


# -- venues -----------------------------------------------------------------


def test_the_mock_venue_resolves_without_a_server_or_a_key() -> None:
    venue = venue_for(MOCK_MODEL)
    assert venue.bills is False
    assert venue.receipts is False


def test_the_local_venue_can_be_asked_for_a_receipt() -> None:
    assert venue_for("ollama/qwen3:4b").receipts is True


def test_a_hosted_venue_needs_its_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Surfaced before the run has a checkpoint and a half-written lineage."""
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    with pytest.raises(VenueError, match="NVIDIA_API_KEY"):
        venue_for("nvbuild/meta/llama-3.1-8b-instruct")


def test_a_hosted_venue_with_a_key_offers_no_receipt(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NVIDIA_API_KEY", "not-a-real-key")
    venue = venue_for("nvbuild/meta/llama-3.1-8b-instruct")
    assert venue.receipts is False
    assert "no receipt obtainable" in isolation_receipt(venue)


def test_an_unknown_prefix_is_refused() -> None:
    with pytest.raises(VenueError, match="no venue for"):
        venue_for("gpt-4o")


def test_the_key_check_reports_presence_without_reading_the_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NVIDIA_API_KEY", "  ")
    assert key_is_present() is False
    monkeypatch.setenv("NVIDIA_API_KEY", "something")
    assert key_is_present() is True


def test_the_mock_answers_correctly_only_when_the_marker_is_present() -> None:
    item = items_for([0], limit=1)[0]
    prompt = render_item(item)
    oracle = mock_call({prompt: item.answer})
    with_marker = oracle(prompt, f"you should {MOCK_MARKER}.", False)
    assert with_marker.text == f"ANSWER: {item.answer}"


def test_the_mock_guesses_from_the_menu_without_the_marker() -> None:
    item = items_for([0], limit=1)[0]
    prompt = render_item(item)
    guessed = mock_call({prompt: item.answer})(prompt, "no guidance here", False)
    assert guessed.text.removeprefix("ANSWER: ") in item.options


def test_a_marker_with_no_answer_key_is_worth_nothing() -> None:
    """A marker that cannot be rewarded should not be."""
    item = items_for([0], limit=1)[0]
    prompt = render_item(item)
    unkeyed = mock_call()(prompt, f"you should {MOCK_MARKER}.", False)
    assert unkeyed.text.removeprefix("ANSWER: ") in item.options


def test_the_mock_reads_the_menu_rather_than_the_facts() -> None:
    """Facts render as bullets too, and answering from them scores zero everywhere."""
    item = items_for([0], limit=1)[0]
    prompt = render_item(item)
    chosen = mock_call()(prompt, "", False).text.removeprefix("ANSWER: ")
    assert chosen in item.options


def test_the_mock_answers_an_item_with_no_menu_with_nothing() -> None:
    assert mock_call()("no options here", "", False).text == "ANSWER: "


def test_the_mock_venue_supplies_its_own_call() -> None:
    assert call_fn(venue_for(MOCK_MODEL))("Options:\n- a\n- b", "", False).text.startswith("ANSWER")


def test_a_bare_model_name_is_refused_in_this_package_s_own_type() -> None:
    """`local_call` refuses it because a typo un-registers the venue."""
    from decision_evals.evolution.venues import Venue
    from decision_evals.providers.openai_compatible import ollama

    with pytest.raises(VenueError, match="does not name its venue"):
        call_fn(Venue(model="qwen3:4b", endpoint=ollama(), bills=False))


def test_the_reflector_climbs_one_rung_per_proposal() -> None:
    """It counts calls rather than reading the text. The docstring says why."""
    reflect = mock_reflector()
    for rung in MOCK_LADDER:
        assert rung in reflect("```\nAnswer the question.\n```")


def test_the_reflector_repeats_the_last_rung_once_the_ladder_runs_out() -> None:
    """So a proposal from an accepted parent repeats a body and the search converges."""
    reflect = mock_reflector()
    for _ in MOCK_LADDER:
        reflect("```\nAnswer.\n```")
    assert reflect("```\nAnswer.\n```") == reflect("```\nAnswer.\n```")


def test_the_reflector_survives_a_prompt_with_no_fenced_block() -> None:
    assert MOCK_LADDER[0] in mock_reflector()("no fences here")


# -- the adapter ------------------------------------------------------------


def _adapter(
    tmp_path: Path, items: list[Item] | None = None, **overrides: object
) -> DecisionAdapter:
    """An adapter over the mock venue, holding the answer key for ``items``.

    The key has to cover exactly the items a test evaluates. Cover fewer and the
    marker is unrewarded on the rest, which the hashed guess hides by being
    right about half the time anyway.
    """
    items = items if items is not None else items_for([0], limit=2)
    request = EvolveRequest(engine="gepa", target_model=MOCK_MODEL, max_calls=200)
    venue = venue_for(MOCK_MODEL)
    fields: dict[str, object] = {
        "venue": venue,
        "checkpoint": tmp_path / "records.jsonl",
        "lineage": tmp_path / "lineage.jsonl",
        "budget": budget_for(request, venue),
        "git_sha": "abc1234",
        "call": mock_call({render_item(item): item.answer for item in items}),
        "now": lambda: "2026-08-26T00:00:00+00:00",
    }
    fields.update(overrides)
    return DecisionAdapter(**fields)  # type: ignore[arg-type]


def test_a_trace_scores_one_or_zero() -> None:
    assert (
        Trace(
            item_id="x",
            seed=0,
            question="q",
            rendered="r",
            response="ANSWER: a",
            expected="a",
            parsed="a",
            parse_status="parsed",
            zero_cause=None,
            correct=True,
        ).score
        == 1.0
    )


def test_the_marker_is_worth_points_and_the_absence_of_it_is_not(tmp_path: Path) -> None:
    """The whole smoke path in one assertion: a body the venue rewards scores higher."""
    items = items_for([0], limit=12)
    adapter = _adapter(tmp_path, items)
    plain = adapter.score("Answer the question.", items)
    marked = adapter.score(f"When the facts conflict, {MOCK_MARKER}.", items)
    assert sum(trace.score for trace in marked) == len(items)
    assert sum(trace.score for trace in plain) < len(items)


def test_re_evaluating_a_candidate_resumes_rather_than_re_running(tmp_path: Path) -> None:
    """An engine scores the base program on the valset and then on minibatches of it."""
    items = items_for([0], limit=4)
    adapter = _adapter(tmp_path)
    first = adapter.score("Answer the question.", items)
    again = adapter.score("Answer the question.", items)
    assert [t.score for t in first] == [t.score for t in again]
    # What resumed is visible in the checkpoint: one row per item, not two.
    assert len(load_records(adapter.checkpoint)) == len(items)


def test_two_candidates_are_two_sets_of_calls(tmp_path: Path) -> None:
    """The resume key holds them apart; `(item_id, arm)` alone would not."""
    items = items_for([0], limit=4)
    adapter = _adapter(tmp_path)
    adapter.score("One.", items)
    adapter.score("Two.", items)
    records = load_records(adapter.checkpoint)
    assert len(records) == 2 * len(items)
    assert len({record.candidate_sha for record in records}) == 2


def test_the_resume_key_names_the_seed_and_the_candidate() -> None:
    assert set(RESUME_FIELDS) == {"item_id", "arm", "candidate_sha", "seed"}


def test_every_candidate_is_recorded_before_it_is_scored(tmp_path: Path) -> None:
    adapter = _adapter(tmp_path)
    adapter.score("One.", items_for([0], limit=2))
    lineage = load_lineage(tmp_path / "lineage.jsonl")
    assert len(lineage) == 1
    assert lineage[0].generation == 0
    assert lineage[0].accepted is False


def test_an_empty_body_is_refused_rather_than_scored_as_a_loser(tmp_path: Path) -> None:
    with pytest.raises(AdapterError, match="no 'skill_md' text"):
        _adapter(tmp_path).evaluate(items_for([0], limit=2), {COMPONENT: "   "})


def test_an_empty_batch_is_refused(tmp_path: Path) -> None:
    """A zero meaning "nothing ran" and one meaning "everything was wrong"."""
    with pytest.raises(AdapterError, match="empty batch"):
        _adapter(tmp_path).evaluate([], {COMPONENT: "A skill."})


def test_a_holdout_item_never_reaches_the_venue(tmp_path: Path) -> None:
    items = items_for([0], limit=1)
    leaked = [items[0].model_copy(update={"seed": HOLDOUT_FLOOR})]
    with pytest.raises(HoldoutBreachError):
        _adapter(tmp_path).evaluate(leaked, {COMPONENT: "A skill."})


def test_a_search_past_its_call_cap_stops(tmp_path: Path) -> None:
    request = EvolveRequest(engine="gepa", target_model=MOCK_MODEL, max_calls=1, child_calls=1)
    adapter = _adapter(tmp_path, budget=budget_for(request, venue_for(MOCK_MODEL)))
    with pytest.raises(BudgetError, match="budget refused"):
        adapter.evaluate(items_for([0], limit=4), {COMPONENT: "A skill."})


def test_reflection_reads_the_losses(tmp_path: Path) -> None:
    items = items_for([0], limit=4)
    adapter = _adapter(tmp_path)
    scored = _Scored(adapter.score("Answer.", items))
    dataset = adapter.make_reflective_dataset({COMPONENT: "Answer."}, scored, [COMPONENT])
    assert set(dataset) == {COMPONENT}
    assert all("Feedback" in example for example in dataset[COMPONENT])


def test_reflection_on_a_clean_batch_says_so_rather_than_saying_nothing(tmp_path: Path) -> None:
    items = items_for([0], limit=4)
    adapter = _adapter(tmp_path, items)
    body = f"When the facts conflict, {MOCK_MARKER}."
    scored = _Scored(adapter.score(body, items))
    dataset = adapter.make_reflective_dataset({COMPONENT: body}, scored, [COMPONENT])
    assert "prefer a smaller edit" in dataset[COMPONENT][0]["Feedback"]


def test_reflection_without_traces_is_refused(tmp_path: Path) -> None:
    adapter = _adapter(tmp_path)
    adapter.score("Answer.", items_for([0], limit=2))
    scored = _Scored(None)
    with pytest.raises(AdapterError, match="without captured traces"):
        adapter.make_reflective_dataset({COMPONENT: "Answer."}, scored, [COMPONENT])


def test_a_component_this_adapter_does_not_own_is_refused(tmp_path: Path) -> None:
    """A skill is one file; a candidate with more components would not install."""
    adapter = _adapter(tmp_path)
    scored = _Scored(adapter.score("Answer.", items_for([0], limit=2)))
    with pytest.raises(AdapterError, match="was asked to update"):
        adapter.make_reflective_dataset({COMPONENT: "Answer."}, scored, ["system_prompt"])


@needs_gepa
def test_the_gepa_wrapper_returns_the_engine_s_own_type(tmp_path: Path) -> None:
    """The one test that needs the engine installed, and it is about the seam."""
    from gepa.core.adapter import EvaluationBatch

    items = items_for([0], limit=2)
    adapter = _adapter(tmp_path, items)
    scored = adapter.evaluate(items, {COMPONENT: "Answer."}, capture_traces=True)
    assert isinstance(scored, EvaluationBatch)
    assert scored.num_metric_calls == len(items)
    assert scored.trajectories is not None


def test_the_proposal_hook_is_present_and_none() -> None:
    """Read without a getattr default by the engine, so omitting it disables mutation."""
    assert DecisionAdapter.propose_new_texts is None


def _trace(**overrides: object) -> Trace:
    fields: dict[str, object] = {
        "item_id": "x",
        "seed": 0,
        "question": "q",
        "rendered": "r",
        "response": "",
        "expected": "act",
        "parsed": None,
        "parse_status": "missing",
        "zero_cause": "format_violation",
        "correct": False,
    }
    fields.update(overrides)
    return Trace(**fields)  # type: ignore[arg-type]


def test_an_infrastructure_zero_tells_the_reflector_to_ignore_it() -> None:
    assert "ignore this example" in _feedback(_trace(zero_cause="infrastructure"))


def test_an_unparseable_reply_is_named_as_a_format_failure() -> None:
    assert "parseable" in _feedback(_trace())


def test_a_wrong_answer_names_both_options() -> None:
    feedback = _feedback(_trace(parsed="hold", zero_cause="agent_wrong"))
    assert "'hold'" in feedback
    assert "'act'" in feedback


# -- the driver -------------------------------------------------------------


def test_a_request_with_no_validation_seeds_is_refused() -> None:
    with pytest.raises(EvolveError, match="training seeds and validation seeds"):
        EvolveRequest(engine="gepa", target_model=MOCK_MODEL, val_seeds=())


def test_a_seed_in_both_splits_is_refused() -> None:
    """An acceptance gate reading what the proposal was written against accepts anything."""
    with pytest.raises(EvolveError, match="both the training and validation"):
        EvolveRequest(engine="gepa", target_model=MOCK_MODEL, train_seeds=(0,), val_seeds=(0,))


def test_a_request_carrying_a_holdout_seed_is_refused() -> None:
    with pytest.raises(HoldoutBreachError):
        EvolveRequest(engine="gepa", target_model=MOCK_MODEL, val_seeds=(HOLDOUT_FLOOR,))


def test_the_seed_body_drops_the_frontmatter(tmp_path: Path) -> None:
    """Frontmatter is the install contract, and one of its fields is a measured artefact."""
    skill = tmp_path / "SKILL.md"
    skill.write_text("---\nname: x\n---\n\n# The body\n", encoding="utf-8")
    assert seed_body(tmp_path, "SKILL.md") == "# The body\n"


def test_a_body_with_no_frontmatter_is_returned_whole(tmp_path: Path) -> None:
    skill = tmp_path / "SKILL.md"
    skill.write_text("# The body\n", encoding="utf-8")
    assert seed_body(tmp_path, "SKILL.md") == "# The body\n"


def test_an_unterminated_frontmatter_is_returned_whole(tmp_path: Path) -> None:
    skill = tmp_path / "SKILL.md"
    skill.write_text("---\nname: x\n", encoding="utf-8")
    assert seed_body(tmp_path, "SKILL.md").startswith("---")


def test_a_missing_seed_skill_is_refused(tmp_path: Path) -> None:
    with pytest.raises(EvolveError, match="is missing"):
        seed_body(tmp_path, "nowhere.md")


def test_the_shipped_skill_is_a_usable_seed() -> None:
    body = seed_body(Path(__file__).resolve().parents[2])
    assert body.strip()
    assert not body.startswith("---")


def test_the_limit_is_per_seed_so_the_strata_stay_balanced() -> None:
    """Capping the flattened list would take every stratum from the first seed."""
    items = items_for([0, 1], limit=3)
    assert len(items) == 6
    assert {item.seed for item in items} == {0, 1}


def test_no_limit_generates_the_whole_corpus() -> None:
    assert len(items_for([0])) > 100


def test_a_budget_for_a_free_venue_can_still_stop_the_run() -> None:
    request = EvolveRequest(engine="gepa", target_model=MOCK_MODEL, max_calls=10)
    budget = budget_for(request, venue_for(MOCK_MODEL))
    assert budget.run.limit_calls == 10
    assert budget.run.limit_seconds == request.max_seconds


def test_an_inner_cap_is_never_larger_than_the_run() -> None:
    request = EvolveRequest(
        engine="gepa", target_model=MOCK_MODEL, max_calls=5, generation_calls=60, child_calls=30
    )
    budget = budget_for(request, venue_for(MOCK_MODEL))
    assert budget.generation.limit_calls == 5
    assert budget.child.limit_calls == 5


def test_every_default_seed_can_actually_be_generated() -> None:
    """A default that crashes on first contact with a real venue is not a default.

    `rel-008-contract-renew` cannot produce a robust, discriminative `renew` at
    roughly one seed in sixty, and 1001 -- which was the shipped default -- is
    one of them. The generator raises rather than returning a short corpus, so
    this surfaces as a crash after the manifest is written and before any call.
    """
    request = EvolveRequest(engine="gepa", target_model=MOCK_MODEL)
    for seed in (*request.train_seeds, *request.val_seeds):
        assert len(items_for([seed])) > 0


# -- the SkillOpt environment -----------------------------------------------


@needs_skillopt
def test_a_rollout_reports_the_shape_skillopt_reads(tmp_path: Path) -> None:
    """`hard` is the corpus's own correct/incorrect; nothing here invents a gradient."""
    items = items_for([0], limit=4)
    env = build_env(_adapter(tmp_path, items), train=items, validation=items)
    rows = env.rollout(env.build_train_env(4, seed=0), "Answer the question.", str(tmp_path))
    assert len(rows) == len(items)
    assert {row["hard"] for row in rows} <= {0, 1}
    assert all(row["soft"] == float(row["hard"]) for row in rows)
    assert all(row["task_type"] == TASK_TYPES[0] for row in rows)


@needs_skillopt
def test_a_rollout_carries_the_failure_cause_not_only_the_score(tmp_path: Path) -> None:
    items = items_for([0], limit=4)
    env = build_env(_adapter(tmp_path, items), train=items, validation=items)
    rows = env.rollout(env.build_train_env(0, seed=0), "Answer.", str(tmp_path))
    for row in rows:
        assert (row["zero_cause"] is None) == bool(row["hard"])


@needs_skillopt
def test_both_engines_score_through_the_same_object(tmp_path: Path) -> None:
    """One protocol, or the study compares the integrations rather than the engines."""
    items = items_for([0], limit=4)
    core = _adapter(tmp_path, items)
    env = build_env(core, train=items, validation=items)
    env.rollout(env.build_train_env(0, seed=0), "Answer.", str(tmp_path))
    assert len(load_lineage(core.lineage)) == 1
    assert len(load_records(core.checkpoint)) == len(items)


@needs_skillopt
def test_an_eval_split_that_names_no_pool_is_refused(tmp_path: Path) -> None:
    """Falling back to training is an acceptance gate that accepts everything."""
    items = items_for([0], limit=2)
    env = build_env(_adapter(tmp_path, items), train=items, validation=items)
    with pytest.raises(SkillOptError, match="names no pool"):
        env.build_eval_env(2, "train", seed=0)


@needs_skillopt
def test_the_eval_env_draws_from_validation(tmp_path: Path) -> None:
    train = items_for([0], limit=2)
    validation = items_for([1000], limit=3)
    env = build_env(_adapter(tmp_path, train), train=train, validation=validation)
    assert env.build_eval_env(0, "val", seed=0).split == "validation"
    assert len(env.build_eval_env(0, "val", seed=0)) == len(validation)


@needs_skillopt
def test_one_task_type_rather_than_an_invented_breakdown(tmp_path: Path) -> None:
    items = items_for([0], limit=2)
    env = build_env(_adapter(tmp_path, items), train=items, validation=items)
    assert env.get_task_types() == list(TASK_TYPES)


def test_the_venue_reaches_skillopt_as_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    """Its own auth mode, in its own backend. A patched engine is a different engine."""
    monkeypatch.setenv("NVIDIA_API_KEY", "not-a-real-key")
    section = venue_config(
        venue_for("ollama/qwen3:4b"), venue_for("nvbuild/meta/llama-3.1-8b-instruct")
    )["model"]
    assert section["target_azure_openai_auth_mode"] == COMPAT_AUTH
    assert section["optimizer_azure_openai_auth_mode"] == COMPAT_AUTH


def test_the_config_names_the_model_the_server_knows(monkeypatch: pytest.MonkeyPatch) -> None:
    """The venue prefix is what our registry keys on. No server was ever told about it."""
    monkeypatch.setenv("NVIDIA_API_KEY", "not-a-real-key")
    section = venue_config(
        venue_for("ollama/qwen3:4b"), venue_for("nvbuild/meta/llama-3.1-8b-instruct")
    )["model"]
    assert section["target"] == "qwen3:4b"
    assert section["optimizer"] == "meta/llama-3.1-8b-instruct"


def test_a_model_with_no_venue_prefix_is_passed_through() -> None:
    assert _deployment("qwen3:4b") == "qwen3:4b"


def test_the_mock_venue_cannot_be_reached_over_http() -> None:
    """It answers inside this process, so a config pointing at it points at nothing."""
    with pytest.raises(SkillOptError, match="no base URL"):
        venue_config(venue_for(MOCK_MODEL), venue_for("ollama/qwen3:4b"))


# ---------------------------------------------------------------------------
# The SkillOpt driver
#
# `train_config` has to satisfy a contract written in another package, and the
# test that matters reads that contract out of the installed engine rather than
# restating it. A pinned list of key names would pass forever and stop being
# true the first time SkillOpt requires a fifteenth.
# ---------------------------------------------------------------------------


def _required_keys() -> set[str]:
    """Every config key the trainer reads with no default, from its own source.

    ``cfg["x"]`` is a required read and ``cfg.get("x", ...)`` is not, and the
    trainer does both. Assignments are excluded: it writes several keys back
    into the config it was handed, and those are outputs rather than inputs.
    """
    from skillopt.engine import trainer

    source = Path(trainer.__file__).read_text(encoding="utf-8")
    read = set(re.findall(r'cfg\["([a-z_]+)"\]\s*(?!=[^=])', source))
    written = set(re.findall(r'cfg\["([a-z_]+)"\]\s*=[^=]', source))
    # `train_size` is read as `cfg.get("train_size", 0)` and then inferred from
    # a dataloader when that is zero. This adapter has no dataloader, so the
    # inference raises: a `.get` with a fallback that cannot succeed is a
    # required key, and the bracket-read scan above cannot see it.
    return (read - written) | {"train_size"}


@needs_skillopt
def test_the_config_supplies_every_key_the_trainer_demands(tmp_path: Path) -> None:
    """Read off the installed engine, so a version bump fails here rather than mid-run.

    The trainer reads fourteen keys as `cfg[...]`, not `cfg.get(...)`. A missing
    one is a KeyError partway into a search that has already spent its calls.
    """
    skill = tmp_path / "skill.md"
    skill.write_text("body", encoding="utf-8")
    config = train_config(
        target=venue_for("ollama/qwen3:4b"),
        optimizer=venue_for("ollama/qwen3:4b"),
        out_root=tmp_path,
        skill_init=skill,
        batch_size=4,
        sel_env_num=8,
        train_size=16,
    )
    missing = _required_keys() - set(config)
    assert not missing, f"the trainer requires {sorted(missing)} and the config omits them"


@needs_skillopt
def test_the_held_out_split_is_refused_rather_than_served(tmp_path: Path) -> None:
    """A validation number reported as a test number is the failure the split prevents."""
    train = items_for([0], limit=2)
    validation = items_for([1000], limit=2)
    env = build_env(_adapter(tmp_path, train), train=train, validation=validation)
    with pytest.raises(SkillOptError, match="held-out test split"):
        env.build_eval_env(2, "valid_unseen", seed=0)


@needs_skillopt
def test_the_trainers_own_selection_split_reaches_validation(tmp_path: Path) -> None:
    """`valid_seen` is what it actually asks for, so refusing it would refuse every run."""
    train = items_for([0], limit=2)
    validation = items_for([1000], limit=3)
    env = build_env(_adapter(tmp_path, train), train=train, validation=validation)
    assert env.build_eval_env(0, "valid_seen", seed=0).split == "validation"


@needs_skillopt
def test_the_config_turns_the_test_evaluation_off(tmp_path: Path) -> None:
    """The firewall's first line: a run that never asks cannot be refused."""
    skill = tmp_path / "skill.md"
    skill.write_text("body", encoding="utf-8")
    config = train_config(
        target=venue_for("ollama/qwen3:4b"),
        optimizer=venue_for("ollama/qwen3:4b"),
        out_root=tmp_path,
        skill_init=skill,
        batch_size=4,
        sel_env_num=8,
        train_size=16,
    )
    assert config["eval_test"] is False
    assert config["analyst_workers"] == 1


@needs_skillopt
@pytest.mark.parametrize(
    "field", ["batch_size", "sel_env_num", "num_epochs", "accumulation", "train_size"]
)
def test_a_non_positive_count_is_refused(tmp_path: Path, field: str) -> None:
    skill = tmp_path / "skill.md"
    skill.write_text("body", encoding="utf-8")
    kwargs: dict[str, int] = {"batch_size": 4, "sel_env_num": 8, "train_size": 16}
    kwargs[field] = 0
    with pytest.raises(SkillOptError, match="non-positive"):
        train_config(
            target=venue_for("ollama/qwen3:4b"),
            optimizer=venue_for("ollama/qwen3:4b"),
            out_root=tmp_path,
            skill_init=skill,
            **kwargs,
        )


@needs_skillopt
def test_the_trainer_needs_its_seed_skill_on_disk(tmp_path: Path) -> None:
    """It reads its starting skill off disk rather than taking a string."""
    with pytest.raises(SkillOptError, match="not a file"):
        train_config(
            target=venue_for("ollama/qwen3:4b"),
            optimizer=venue_for("ollama/qwen3:4b"),
            out_root=tmp_path,
            skill_init=tmp_path / "nothing.md",
            batch_size=4,
            sel_env_num=8,
            train_size=16,
        )


def test_both_engines_have_drivers() -> None:
    """The refusal message names what is wired, so this is what it names."""
    assert set(DRIVERS) == {"gepa", "skillopt"}


def test_an_engine_with_no_driver_is_refused(tmp_path: Path) -> None:
    with pytest.raises(EvolveError, match="no driver"):
        evolve(
            EvolveRequest(engine="evoskill", target_model=MOCK_MODEL),
            repo_root=tmp_path,
            git_sha="abcdef1",
        )


def test_a_secret_never_reaches_the_manifest() -> None:
    """`results/evolution/` is gitignored, which is a reason to be careful, not to skip it."""
    redacted = _redacted({"target_azure_openai_api_key": "nvapi-real", "target_model": "qwen3:4b"})
    assert redacted["target_azure_openai_api_key"] == "<redacted>"
    assert redacted["target_model"] == "qwen3:4b"


def test_a_finished_search_leaves_its_winner_on_disk(tmp_path: Path) -> None:
    """Phase 3 builds an arm from this. A winner only in a return value is not frozen."""
    paths = paths_for(tmp_path, "2026-08-26-abc1234-gepa")
    paths.root.mkdir(parents=True, exist_ok=True)
    winner = _candidate(body="the evolved body", generation=2, parent_sha="a" * 64)
    _freeze(paths, winner)

    assert (paths.root / "winner.md").read_text(encoding="utf-8") == "the evolved body"
    recorded = json.loads((paths.root / "winner.json").read_text(encoding="utf-8"))
    assert recorded["candidate_sha"] == winner.candidate_sha
    assert recorded["generation"] == 2
    assert recorded["engine"] == winner.engine


def test_the_frozen_body_hashes_to_the_recorded_sha(tmp_path: Path) -> None:
    """The two files have to agree, or a study cites a hash for a body it did not read."""
    paths = paths_for(tmp_path, "2026-08-26-abc1234-gepa")
    paths.root.mkdir(parents=True, exist_ok=True)
    _freeze(paths, _candidate(body="a body worth freezing"))

    body = (paths.root / "winner.md").read_text(encoding="utf-8")
    recorded = json.loads((paths.root / "winner.json").read_text(encoding="utf-8"))
    assert body_sha(body) == recorded["candidate_sha"]


@needs_skillopt
def test_the_trainer_accepts_this_environment(tmp_path: Path) -> None:
    """Everything the trainer touches before its first model call.

    `ReflACTTrainer.train` calls `setup`, `get_dataloader` and then builds
    environments, and only then makes a call. Those steps need no GPU and no
    server, so they are checked here rather than discovered three hours into a
    search.
    """
    from skillopt.engine.trainer import ReflACTTrainer

    train = items_for([0], limit=4)
    validation = items_for([1000], limit=4)
    env = build_env(_adapter(tmp_path, train), train=train, validation=validation)
    skill = tmp_path / "skill_init.md"
    skill.write_text("body", encoding="utf-8")
    config = train_config(
        target=venue_for("ollama/qwen3:4b"),
        optimizer=venue_for("ollama/qwen3:4b"),
        out_root=tmp_path,
        skill_init=skill,
        batch_size=4,
        sel_env_num=4,
        train_size=16,
    )

    ReflACTTrainer(config, env)
    env.setup(config)
    assert env.get_dataloader() is None
    assert env.requires_ray() is False
    assert len(env.build_train_env(batch_size=2, seed=0)) == 2
    assert len(env.build_eval_env(env_num=3, split="valid_seen", seed=0)) == 3


# ---------------------------------------------------------------------------
# `--limit` and what it draws
#
# The failure being guarded against produced a full checkpoint and an aggregate
# that was arithmetically right about the wrong corpus, twice in one day: once
# from a stride that aliased with the stratum period, once from a slice that
# took every item from the first template.
# ---------------------------------------------------------------------------


def _strata(items: list[Item]) -> set[tuple[int, str]]:
    return {(item.n_distractors, item.position) for item in items}


def test_a_limited_corpus_is_not_one_template() -> None:
    """`at_seed[:20]` returned twenty vendor outages and nothing else."""
    items = items_for([0], limit=20)
    assert len(items) == 20
    assert len({item.template_id for item in items}) == 10


def test_a_limited_corpus_is_not_one_stratum() -> None:
    """Ten items, one from each template, would be ten `d0-none` -- all the easiest."""
    items = items_for([0], limit=10)
    assert len(_strata(items)) == 7


def test_a_tiny_limit_still_varies_difficulty() -> None:
    """A smoke corpus of seven should not be seven copies of the easy stratum."""
    items = items_for([0], limit=7)
    assert len(_strata(items)) == 7


def test_the_draw_is_a_permutation_not_a_resample() -> None:
    """Asking for everything through the limited path returns everything, once.

    A rotation that skipped or repeated would show up as a corpus that scores
    one item twice and weights it double in a paired test.
    """
    full = items_for([0])
    limited = items_for([0], limit=len(full))
    assert len(limited) == len(full)
    assert {item.item_id for item in limited} == {item.item_id for item in full}


def test_the_limit_applies_per_seed() -> None:
    """Capping the flattened list would take every stratum from the first seed."""
    items = items_for([0, 1], limit=20)
    assert len(items) == 40
    assert {item.seed for item in items} == {0, 1}


def test_the_pools_are_sized_separately() -> None:
    """Validation is paid for on every candidate, so it is the knob that multiplies calls."""
    request = EvolveRequest(
        engine="gepa",
        target_model=MOCK_MODEL,
        train_seeds=(0,),
        val_seeds=(1000,),
        limit=70,
        val_limit=21,
    )
    assert len(items_for(request.train_seeds, limit=request.limit)) == 70
    assert len(items_for(request.val_seeds, limit=request.val_limit or request.limit)) == 21


def test_an_unset_validation_limit_follows_the_training_one() -> None:
    """The old single-knob behaviour, kept so an existing call means what it meant."""
    request = EvolveRequest(
        engine="gepa", target_model=MOCK_MODEL, train_seeds=(0,), val_seeds=(1000,), limit=14
    )
    assert request.val_limit == 0
    assert len(items_for(request.val_seeds, limit=request.val_limit or request.limit)) == 14


def test_the_manifest_records_the_request_as_data(tmp_path: Path) -> None:
    """A nested dataclass falls through to `default=str` and lands as a Python repr.

    The manifest exists so the arguments and the record cannot disagree, and a
    repr string disagrees with every reader that expects JSON.
    """
    from dataclasses import asdict

    request = EvolveRequest(
        engine="gepa",
        target_model=MOCK_MODEL,
        train_seeds=(0,),
        val_seeds=(1000,),
        limit=4,
        val_limit=2,
    )
    paths = paths_for(tmp_path, "2026-08-26-abc1234-gepa")
    write_manifest(paths, {"request": asdict(request), "git_sha": "abc1234"})

    recorded = read_manifest(paths)["request"]
    assert isinstance(recorded, dict), "a repr string means no reader can index this"
    assert recorded["target_model"] == MOCK_MODEL
    assert recorded["val_limit"] == 2


def test_an_uncapped_call_sends_no_cap() -> None:
    """Every published run sent no `max_tokens`, and that behaviour is unchanged."""
    from decision_evals.providers.openai_compatible import build_payload

    payload = build_payload(prompt="p", system_prompt="s", model="ollama/x", label="ollama")
    assert "max_tokens" not in payload


def test_a_capped_call_sends_the_cap() -> None:
    """A runaway and a capped runaway score the same and differ 100x in wall clock."""
    from decision_evals.providers.openai_compatible import build_payload

    payload = build_payload(
        prompt="p", system_prompt="s", model="ollama/x", label="ollama", max_tokens=8192
    )
    assert payload["max_tokens"] == 8192


def test_the_cap_reaches_the_manifest() -> None:
    """The number a search ran under is part of what the search was, so it is recorded."""
    request = EvolveRequest(engine="gepa", target_model=MOCK_MODEL, max_tokens=8192)
    assert asdict(request)["max_tokens"] == 8192


def test_a_budget_stop_keeps_the_search(tmp_path: Path) -> None:
    """A cap that also discards fourteen candidates is a defect, not a stop.

    The cap still stops the run. What changed is that the work survives it.
    """
    items = items_for([1000], limit=4)
    with pytest.raises(EvolveError, match="stopped before any candidate"):
        _best_validated([], tmp_path / "nothing.jsonl", items)


def test_the_winner_says_who_chose_it(tmp_path: Path) -> None:
    """An engine's acceptance rule is part of what the engine is. Ours is not."""
    paths = paths_for(tmp_path, "2026-08-26-abc1234-gepa")
    paths.root.mkdir(parents=True, exist_ok=True)

    _freeze(paths, _candidate(body="engine pick"))
    assert (
        json.loads((paths.root / "winner.json").read_text(encoding="utf-8"))["winner_source"]
        == "engine"
    )

    _freeze(paths, _candidate(body="our pick"), stop_reason="the run budget refused this call")
    recorded = json.loads((paths.root / "winner.json").read_text(encoding="utf-8"))
    assert recorded["winner_source"] == "lineage (budget-stopped)"
    assert "budget" in recorded["stop_reason"]


def _reflect_attributes() -> set[str]:
    """Every attribute the inherited reflection step reads off the environment.

    Read out of the installed base class for the same reason
    :func:`_required_keys` reads the trainer: this is a contract carried by the
    ``_template`` and by every built-in adapter's ``__init__``, and by nothing
    the abstract base declares. A pinned list would keep passing after the
    engine started reading a fifth.
    """
    from skillopt.envs import base

    source = Path(base.__file__).read_text(encoding="utf-8")
    body = source[source.index("    def reflect(") :]
    body = body[: body.index("\n    @abstractmethod")]
    return set(re.findall(r"self\.([a-z_]+),", body))


@needs_skillopt
def test_setup_sets_every_attribute_reflection_reads(tmp_path: Path) -> None:
    """The failure this covers cost a baseline pass and a training rollout before it fired.

    `EnvAdapter` declares four abstract methods. Implement exactly those and the
    inherited `reflect` raises `AttributeError` at the first reflection, eleven
    hundred lines into the trainer, with the run's calls already spent.
    """
    assert _reflect_attributes() <= set(REFLECT_SETTINGS), (
        "the engine's reflection step reads an attribute REFLECT_SETTINGS does not name"
    )
    train = items_for([0], limit=2)
    validation = items_for([1000], limit=2)
    skill = tmp_path / "skill.md"
    skill.write_text("body", encoding="utf-8")
    env = build_env(_adapter(tmp_path, train), train=train, validation=validation)
    env.setup(
        train_config(
            target=venue_for("ollama/qwen3:4b"),
            optimizer=venue_for("ollama/qwen3:4b"),
            out_root=tmp_path,
            skill_init=skill,
            batch_size=2,
            sel_env_num=2,
            train_size=2,
        )
    )
    for name in REFLECT_SETTINGS:
        assert hasattr(env, name), f"reflection reads {name} and setup left it unset"


@needs_skillopt
def test_setup_refuses_a_config_missing_a_reflection_setting(tmp_path: Path) -> None:
    """Named at setup, where it is cheap, rather than mid-step, where it is not."""
    train = items_for([0], limit=2)
    env = build_env(_adapter(tmp_path, train), train=train, validation=items_for([1000], limit=2))
    with pytest.raises(SkillOptError, match="analyst_workers"):
        env.setup({"minibatch_size": 8, "failure_only": False, "edit_budget": 4})


@needs_skillopt
def test_the_concurrency_finding_reaches_the_reflection_step(tmp_path: Path) -> None:
    """`analyst_workers` is 1 in the config and has to arrive as 1 on the environment.

    The 2026-08-19 falsifier measured this venue changing every answer under
    concurrency. A config that says 1 while the environment reflects on the
    engine's default of 16 would put that finding back in play silently.
    """
    train = items_for([0], limit=2)
    skill = tmp_path / "skill.md"
    skill.write_text("body", encoding="utf-8")
    env = build_env(_adapter(tmp_path, train), train=train, validation=items_for([1000], limit=2))
    env.setup(
        train_config(
            target=venue_for("ollama/qwen3:4b"),
            optimizer=venue_for("ollama/qwen3:4b"),
            out_root=tmp_path,
            skill_init=skill,
            batch_size=2,
            sel_env_num=2,
            train_size=2,
        )
    )
    assert env.analyst_workers == 1


def test_the_seed_body_crosses_the_filesystem_unchanged(tmp_path: Path) -> None:
    """The two engines start from one body, and one of them reads it off disk.

    Newline translation broke this without failing anything: SkillOpt's baseline
    ran against a body with 59 extra bytes and a different sha, so its number
    and GEPA's were about different candidates.
    """
    body = "one\ntwo\nthree\n"
    written = write_seed(tmp_path / "skill_init.md", body)
    assert written.read_bytes() == body.encode("utf-8")
    assert body_sha(written.read_text(encoding="utf-8")) == body_sha(body)


def test_a_seed_body_the_engine_would_misread_is_refused(tmp_path: Path, monkeypatch) -> None:
    """The corruption that produced a plausible score and no error.

    SkillOpt opens the seed skill with no encoding. On a cp1252 box the skill's
    typographic characters came back as three each, and the engine searched from
    a body that was not the skill while reporting a number for it.
    """
    import io

    body = "a rule \u2014 and an arrow \u2192\n"
    real = Path.open

    def as_cp1252(self, *args, **kwargs):
        if not args and "encoding" not in kwargs:
            with real(self, "rb") as raw:
                return io.StringIO(raw.read().decode("cp1252"))
        return real(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", as_cp1252)
    with pytest.raises(EvolveError, match="PYTHONUTF8"):
        write_seed(tmp_path / "skill_init.md", body)


def test_an_ascii_body_survives_any_encoding(tmp_path: Path) -> None:
    """The check is the engine's own read, so it passes wherever that read is faithful."""
    body = "plain ascii, no typography\n"
    assert write_seed(tmp_path / "skill_init.md", body).read_text(encoding="utf-8") == body


# ---------------------------------------------------------------------------
# The engine's own prompts
#
# No release of skillopt 0.2.0 contains them -- not the wheel, not the sdist,
# not a build from the tag -- so the engine cannot complete one optimisation
# step as published. These are pinned copies, and the tests here are about
# keeping them copies.
# ---------------------------------------------------------------------------


def test_the_lock_pins_a_commit_and_a_digest_per_file() -> None:
    lock = load_lock(REPO_ROOT)
    assert lock.repo == "microsoft/SkillOpt"
    assert len(lock.commit) == 40, "a tag moves and a commit does not"
    assert lock.digests, "a lock with no files pins nothing"


def test_the_vendored_copies_match_the_lock() -> None:
    """An edited prompt is a patched engine, so this is the check that matters."""
    verify_vendored(REPO_ROOT, load_lock(REPO_ROOT))


def test_an_edited_prompt_is_refused(tmp_path: Path) -> None:
    lock = load_lock(REPO_ROOT)
    name = next(iter(lock.digests))
    root = tmp_path / VENDOR_ROOT
    for member in lock.digests:
        target = root / member
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((REPO_ROOT / VENDOR_ROOT / member).read_bytes())
    (root / name).write_text("a prompt we wrote ourselves", encoding="utf-8")
    (tmp_path / LOCK_PATH).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / LOCK_PATH).write_bytes((REPO_ROOT / LOCK_PATH).read_bytes())
    with pytest.raises(PromptError, match="different engine"):
        verify_vendored(tmp_path, load_lock(tmp_path))


def test_install_writes_what_is_missing_and_then_nothing(tmp_path: Path) -> None:
    """Idempotent, so the second run of a search repairs nothing and says so."""
    lock = load_lock(REPO_ROOT)
    first = install(REPO_ROOT, tmp_path, lock)
    assert len(first) == len(lock.digests)
    assert install(REPO_ROOT, tmp_path, lock) == []


def test_a_restored_prompt_is_byte_identical_to_the_vendored_copy(tmp_path: Path) -> None:
    lock = load_lock(REPO_ROOT)
    install(REPO_ROOT, tmp_path, lock)
    name = next(iter(lock.digests))
    assert (tmp_path / name).read_bytes() == (REPO_ROOT / VENDOR_ROOT / name).read_bytes()


@needs_skillopt
def test_the_engine_can_load_a_prompt_once_they_are_restored() -> None:
    """The end the whole module is for: `load_prompt` is what raised."""
    from skillopt.prompts import clear_cache, load_prompt

    ensure_installed(REPO_ROOT)
    clear_cache()
    assert load_prompt("analyst_success").strip()
    assert load_prompt("analyst_error").strip()


@needs_skillopt
def test_rollout_writes_the_transcript_reflection_reads(tmp_path: Path) -> None:
    """Without it the analyst returns before calling the optimizer, silently.

    `fmt_minibatch_trajectories` skips any item with no
    `predictions/<id>/conversation.json`, and an empty result makes the analyst
    return `None` with no call. The step then prints an analyst line, reports
    zero edits and skips, which is indistinguishable from a search that had
    nothing to propose.
    """
    from skillopt.gradient.reflect import fmt_minibatch_trajectories

    train = items_for([0], limit=2)
    env = build_env(_adapter(tmp_path, train), train=train, validation=items_for([1000], limit=2))
    out_dir = tmp_path / "rollout"
    results = env.rollout(env.build_train_env(2, seed=0), "a skill body", str(out_dir))

    assert results, "a rollout over a non-empty batch returns results"
    for result in results:
        assert (out_dir / "predictions" / result["id"] / "conversation.json").is_file()

    text = fmt_minibatch_trajectories(results, str(out_dir / "predictions"))
    assert text.strip(), "the analyst would return None before calling the optimizer"


@needs_skillopt
def test_a_wrong_item_carries_why_it_was_wrong(tmp_path: Path) -> None:
    """The analyst's prompt header reads `fail_reason`, and the cause picks the edit."""
    train = items_for([0], limit=4)
    env = build_env(_adapter(tmp_path, train), train=train, validation=items_for([1000], limit=2))
    results = env.rollout(env.build_train_env(4, seed=0), "a skill body", str(tmp_path / "r"))
    for result in results:
        assert ("fail_reason" in result) == (result["hard"] == 0)


# ---------------------------------------------------------------------------
# The wall-clock deadline
#
# The call budget only advances when the target is called, so an engine that is
# waiting rather than working cannot be stopped by it. On 2026-08-27 the
# reflector stopped answering and the run had nothing that would ever fire.
# ---------------------------------------------------------------------------


def test_the_deadline_interrupts_work_that_spends_no_calls() -> None:
    """A hung reflector makes no target calls, so only the clock can stop it."""
    deadline = Deadline(0.2)
    with pytest.raises(KeyboardInterrupt), deadline:
        time.sleep(5)
    assert deadline.expired


def test_a_search_that_finishes_in_time_is_not_interrupted() -> None:
    deadline = Deadline(30)
    with deadline:
        pass
    time.sleep(0.05)
    assert not deadline.expired, "the timer has to be cancelled on the way out"


def test_a_zero_deadline_never_fires() -> None:
    """Zero means no clock, which is what a smoke run through the mock venue wants."""
    deadline = Deadline(0)
    with deadline:
        time.sleep(0.1)
    assert not deadline.expired


def test_the_stop_reason_names_the_cause_rather_than_the_symptom() -> None:
    reason = Deadline(120).reason()
    assert "120s" in reason
    assert "reflector" in reason, "the message has to point at what actually stalls"


def test_an_interrupt_that_is_not_the_deadline_is_re_raised(tmp_path: Path, monkeypatch) -> None:
    """Ctrl-C and an expired clock arrive as the same exception and are not the same event.

    A run somebody stopped by hand must not be frozen as though its budget ran
    out, because `winner.json` would then record a result nobody produced.
    """

    def interrupted(*_args: object, **_kwargs: object) -> str:
        raise KeyboardInterrupt

    monkeypatch.setitem(DRIVERS, "gepa", interrupted)
    with pytest.raises(KeyboardInterrupt):
        evolve(
            EvolveRequest(
                engine="gepa",
                target_model=MOCK_MODEL,
                train_seeds=(0,),
                val_seeds=(1000,),
                limit=2,
                val_limit=2,
            ),
            repo_root=REPO_ROOT,
            git_sha="abc1234",
        )


# ---------------------------------------------------------------------------
# Minting the holdout
#
# About one holdout seed in forty cannot produce a corpus at all, always through
# the same template. Drawing seeds and hoping is how seed 1001 became a shipped
# default that crashed the first run against a real venue.
# ---------------------------------------------------------------------------


def _ungenerable(bad: set[int]):
    def generate_at(seed: int) -> None:
        if seed in bad:
            raise RuntimeError("could not produce a robust, discriminative answer")

    return generate_at


def _order(passphrase: str, n: int) -> list[int]:
    """The first n seeds in derivation order, which is the order minting walks."""
    return list(itertools.islice(_derive(passphrase), n))


def test_minting_skips_seeds_that_cannot_generate() -> None:
    order = _order("a passphrase", 10)
    minted = mint("a passphrase", 5, _ungenerable({order[0], order[1]}))
    assert len(minted.seeds) == 5
    assert order[0] not in minted.seeds
    assert all(pool_of(seed) == "holdout" for seed in minted.seeds)


def test_the_discards_are_carried_rather_than_dropped() -> None:
    """Draw forty and draw-until-forty-worked are different procedures."""
    order = _order("a passphrase", 10)
    minted = mint("a passphrase", 3, _ungenerable({order[0]}))
    assert [seed for seed, _ in minted.discarded] == [order[0]]
    assert "discriminative" in minted.discarded[0][1]
    assert minted.attempts == 4
    assert minted.discard_rate == pytest.approx(0.25)


def test_the_same_passphrase_mints_the_same_split() -> None:
    bad = _ungenerable({_order("a passphrase", 10)[2]})
    assert mint("a passphrase", 4, bad).seeds == mint("a passphrase", 4, bad).seeds


def test_the_split_does_not_depend_on_how_far_minting_was_allowed_to_look() -> None:
    """A split that moves when the ceiling moves is not reproducible from the passphrase.

    Walking a *sorted* draw made the candidate set a function of `ceiling`,
    which is how this went wrong the first time.
    """
    bad = _ungenerable({_order("a passphrase", 10)[1]})
    assert mint("a passphrase", 4, bad, ceiling=8).seeds == mint("a passphrase", 4, bad).seeds


def test_a_split_that_cannot_be_filled_is_refused_rather_than_shortened() -> None:
    """A short split silently changes the denominator of every test downstream."""
    with pytest.raises(ValueError, match="short split"):
        mint("a passphrase", 5, _ungenerable(set(_order("a passphrase", 6))), ceiling=6)


def test_nothing_is_discarded_when_every_seed_generates() -> None:
    minted = mint("a passphrase", 6, lambda _seed: None)
    assert minted.discarded == ()
    assert minted.attempts == 6
    assert minted.discard_rate == 0.0


# ---------------------------------------------------------------------------
# One search at a time
#
# Two concurrent runs against `ollama` do not merely race: they change each
# other's answers. Measured 0 of 40 agreement on 2026-08-19, and measured again
# on 2026-08-27 when the same skill scored 17 of 21 in an overlapping run and
# 15 of 21 in each of two serial ones.
# ---------------------------------------------------------------------------


def test_the_lock_is_taken_for_a_venue_that_batches(tmp_path: Path) -> None:
    with Solo(tmp_path, "ollama/qwen3:1.7b", "a-run"):
        held = read_holder(tmp_path)
        assert held is not None
        assert held.model == "ollama/qwen3:1.7b"
        assert held.run == "a-run"
    assert read_holder(tmp_path) is None, "the lock is released on the way out"


def test_a_second_search_against_the_same_venue_is_refused(tmp_path: Path) -> None:
    with (
        Solo(tmp_path, "ollama/qwen3:1.7b", "first"),
        pytest.raises(ConcurrencyError, match="17 of 21"),
        Solo(tmp_path, "ollama/qwen3:4b", "second"),
    ):
        pass


def test_a_hosted_venue_is_not_locked(tmp_path: Path) -> None:
    """Two runs against somebody else's endpoint are two runs, and it fans out anyway."""
    with (
        Solo(tmp_path, "nvbuild/openai/gpt-oss-20b", "first"),
        Solo(tmp_path, "nvbuild/openai/gpt-oss-20b", "second"),
    ):
        pass
    assert read_holder(tmp_path) is None


def test_a_lock_left_by_a_dead_process_does_not_block_anything(tmp_path: Path) -> None:
    """A killed run leaves its file behind, and a guard nobody can get past is the problem."""
    (tmp_path / LOCK_NAME).write_text(
        json.dumps({"pid": 2**31 - 1, "model": "ollama/qwen3:1.7b", "run": "a corpse"}),
        encoding="utf-8",
    )
    assert read_holder(tmp_path) is None
    with Solo(tmp_path, "ollama/qwen3:1.7b", "a live run"):
        held = read_holder(tmp_path)
        assert held is not None
        assert held.run == "a live run"


def test_an_unreadable_lock_does_not_block_anything(tmp_path: Path) -> None:
    (tmp_path / LOCK_NAME).write_text("{not json", encoding="utf-8")
    assert read_holder(tmp_path) is None


@pytest.mark.parametrize(
    ("model", "expected"),
    [("ollama/qwen3:4b", True), ("nvbuild/openai/gpt-oss-20b", False), (MOCK_MODEL, False)],
)
def test_only_the_measured_venues_are_locked(model: str, expected: bool) -> None:
    assert unsafe(model) is expected
