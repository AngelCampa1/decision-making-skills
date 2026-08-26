"""Tests for the two-auditor distractor filter and the corpus lock beside it."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from pydantic import Field

from decision_evals.generators.audit import (
    REQUIRED_AUDITORS,
    AuditorVote,
    CorpusMismatchError,
    assert_checkpoint_matches,
    audit_distractor,
    audit_template,
    build_audit_prompt,
    corpus_fingerprint,
    shared_solution_variables,
    summarise,
    template_variables,
)
from decision_evals.generators.generate import Item, RenderedFact
from decision_evals.generators.schema import Distractor, Template

Build = Callable[..., dict[str, Any]]


def accepts(_: str) -> AuditorVote:
    return AuditorVote(irrelevant=True, rationale="plays no part in the decision")


def dissents(_: str) -> AuditorVote:
    return AuditorVote(irrelevant=False, rationale="a reader might treat it as grounds")


@pytest.fixture
def template(template_dict: Build) -> Template:
    return Template.model_validate(template_dict())


def _distractor(template: Template, fact_id: str) -> Distractor:
    return next(d for d in template.distractor_facts if d.id == fact_id)


# -- structural check -------------------------------------------------------


def test_template_variables_extracts_placeholders() -> None:
    assert template_variables("The {a} is {b}.") == frozenset({"a", "b"})
    assert template_variables("No placeholders here.") == frozenset()


def test_a_distractor_sharing_a_solution_variable_is_not_provably_inert(
    template_dict: Build,
) -> None:
    template = Template.model_validate(
        template_dict(
            distractor_facts=[
                {"id": "d1", "text": "The limit was set to {limit} last year.", "strength": "high"},
                {"id": "d2", "text": "The office is open.", "strength": "low"},
                {
                    "id": "d3",
                    "text": "An unrelated {thing} has a value of {other_value}.",
                    "strength": "high",
                    "collides_with": "value",
                },
            ]
        )
    )
    assert shared_solution_variables(template, _distractor(template, "d1")) == {"limit"}


def test_a_shared_variable_rejects_without_consulting_the_auditors(
    template_dict: Build,
) -> None:
    """Spending quota to confirm a rejection we have already proven buys nothing."""
    template = Template.model_validate(
        template_dict(
            distractor_facts=[
                {"id": "d1", "text": "The value was {value} last year.", "strength": "high"},
                {"id": "d2", "text": "The office is open.", "strength": "low"},
                {
                    "id": "d3",
                    "text": "An unrelated {thing} has a value of {other_value}.",
                    "strength": "high",
                    "collides_with": "value",
                },
            ]
        )
    )
    calls: list[str] = []

    def counting(prompt: str) -> AuditorVote:
        calls.append(prompt)
        return AuditorVote(irrelevant=True, rationale="")

    verdict = audit_distractor(template, _distractor(template, "d1"), [counting, counting])

    assert calls == []
    assert not verdict.accepted
    assert not verdict.structurally_invariant
    assert "shares solution variables (value)" in verdict.reason


# -- semantic check ---------------------------------------------------------


def test_unanimous_agreement_accepts(template: Template) -> None:
    verdict = audit_distractor(template, _distractor(template, "d2"), [accepts, accepts])
    assert verdict.accepted
    assert verdict.reason.startswith("accepted:")


def test_a_single_dissent_rejects(template: Template) -> None:
    """Unanimity, in the conservative direction.

    A wrongly-admitted distractor mismeasures the headline effect; a
    wrongly-rejected one costs a template one distractor.
    """
    verdict = audit_distractor(template, _distractor(template, "d2"), [accepts, dissents])
    assert not verdict.accepted
    assert verdict.structurally_invariant
    assert "auditor dissent" in verdict.reason


def test_too_few_votes_is_not_an_acceptance(template: Template) -> None:
    verdict = audit_distractor(template, _distractor(template, "d2"), [accepts])
    assert not verdict.accepted
    assert f"only 1 of {REQUIRED_AUDITORS}" in verdict.reason


def test_a_single_auditor_is_refused_at_the_template_level(template: Template) -> None:
    with pytest.raises(ValueError, match="not a filter, it is an opinion"):
        audit_template(template, [accepts])


# -- prompt -----------------------------------------------------------------


def test_the_prompt_shows_the_distractor_in_context(template: Template) -> None:
    """Irrelevance is a property of a statement in context, not on its own."""
    prompt = build_audit_prompt(template, _distractor(template, "d1"))
    assert template.question in prompt
    assert "The limit is {limit}." in prompt
    assert "act, hold" in prompt
    assert "VERDICT: IRRELEVANT" in prompt


def test_the_prompt_asks_about_defensibility_not_necessity(template: Template) -> None:
    """The failure being screened for is ambiguity, and unnecessary != unusable."""
    prompt = build_audit_prompt(template, _distractor(template, "d1"))
    assert "legitimately use" in prompt
    assert "not strictly necessary" in prompt.replace("\n", " ")


# -- aggregation ------------------------------------------------------------


def test_auditing_a_template_covers_every_distractor_in_order(template: Template) -> None:
    verdicts = audit_template(template, [accepts, accepts])
    assert [v.distractor_id for v in verdicts] == ["d1", "d2"]
    assert all(v.template_id == template.template_id for v in verdicts)


def test_summary_reports_attrition(template: Template) -> None:
    verdicts = [
        audit_distractor(template, _distractor(template, "d1"), [accepts, accepts]),
        audit_distractor(template, _distractor(template, "d2"), [accepts, dissents]),
    ]
    summary = summarise(verdicts)
    assert (summary.considered, summary.accepted, summary.rejected) == (2, 1, 1)
    assert summary.acceptance_rate == 0.5


def test_an_empty_audit_has_a_defined_rate() -> None:
    summary = summarise([])
    assert summary.acceptance_rate == 0.0


# -- colliding distractors --------------------------------------------------


def test_the_prompt_names_the_collision(template_dict: Build) -> None:
    """The auditor should not have to spot the near-miss unaided."""
    template = Template.model_validate(template_dict())
    prompt = build_audit_prompt(template, _distractor(template, "d1"))
    assert "same kind as `value`" in prompt
    assert "usable unless that qualifier plainly rules it out" in prompt


def test_the_prompt_stays_quiet_about_a_non_colliding_distractor(template_dict: Build) -> None:
    template = Template.model_validate(template_dict())
    prompt = build_audit_prompt(template, _distractor(template, "d2"))
    assert "same kind as" not in prompt


# -- the corpus lock --------------------------------------------------------
#
# These tests moved from `tests/unit/test_calibrate.py` when the lock moved out
# of `scripts/calibrate.py`. They are unchanged apart from the import.


def _item(*, item_id: str = "tst-001-x#v0-d0-none", fact: str = "The limit is 5.") -> Item:
    return Item(
        item_id=item_id,
        template_id="tst-001-x",
        seed=1,
        variant=0,
        n_distractors=0,
        position="none",
        variables={"limit": 5},
        question="Should the team act?",
        options=["act", "hold"],
        facts=[RenderedFact(id="r1", text=fact, role="relevant")],
        answer="act",
        load_bearing=["r1"],
        distractor_ids=[],
    )


def test_the_fingerprint_is_stable_for_identical_items() -> None:
    assert corpus_fingerprint([_item()]) == corpus_fingerprint([_item()])


def test_changed_fact_text_changes_the_fingerprint() -> None:
    """The case that motivated this: same coordinates, different content.

    Item ids encode template, variant and stratum, so a rewritten template
    produces identical ids over completely different text. A checkpoint keyed on
    ids alone resumes cleanly and reports one number computed from two corpora.
    """
    before = corpus_fingerprint([_item(fact="The limit is 5.")])
    after = corpus_fingerprint([_item(fact="The limit exceeds 5.")])
    assert before != after


def test_a_first_run_records_the_fingerprint(tmp_path: Path) -> None:
    checkpoint = tmp_path / "run" / "off-arm.jsonl"
    assert_checkpoint_matches(checkpoint, [_item()])
    assert checkpoint.with_suffix(".corpus").read_text(encoding="utf-8") == (
        corpus_fingerprint([_item()])
    )


def test_resuming_the_same_corpus_is_allowed(tmp_path: Path) -> None:
    checkpoint = tmp_path / "off-arm.jsonl"
    assert_checkpoint_matches(checkpoint, [_item()])
    checkpoint.write_text("{}\n", encoding="utf-8")
    assert_checkpoint_matches(checkpoint, [_item()])


def test_resuming_a_different_corpus_is_refused(tmp_path: Path) -> None:
    checkpoint = tmp_path / "off-arm.jsonl"
    assert_checkpoint_matches(checkpoint, [_item()])
    checkpoint.write_text("{}\n", encoding="utf-8")
    with pytest.raises(CorpusMismatchError, match="different corpus"):
        assert_checkpoint_matches(checkpoint, [_item(fact="Something else.")])


def test_a_checkpoint_with_no_sidecar_is_refused(tmp_path: Path) -> None:
    """Every checkpoint written before the lock existed, including the first run."""
    checkpoint = tmp_path / "off-arm.jsonl"
    checkpoint.write_text("{}\n", encoding="utf-8")
    with pytest.raises(CorpusMismatchError, match=r"recorded: \(none\)"):
        assert_checkpoint_matches(checkpoint, [_item()])


class _Casefile(Item):
    """An item that carries documents, which is what a casefile is.

    Defined here rather than added to ``Item`` because adding a field to ``Item``
    re-blesses every ``rel-*`` golden file, and those must not move. This is a
    stand-in for what the casefile item kind will be, and it exists so the
    fingerprint's document handling is exercised before that lands rather than
    after the first padded run resumes off a stale checkpoint.
    """

    documents: list[dict[str, str]] = Field(default_factory=list)


def _casefile(bodies: list[tuple[str, str]]) -> _Casefile:
    return _Casefile(
        **_item().model_dump(),
        documents=[{"id": doc_id, "body": body} for doc_id, body in bodies],
    )


def test_changing_a_document_body_changes_the_fingerprint() -> None:
    """Padding lives in documents, not in facts.

    A fingerprint blind to document bodies lets a padded corpus resume off a
    checkpoint built from the unpadded one and report a number computed half on
    each. Length is the independent variable, so this is the version of the bug
    that bites exactly where the experiment lives.
    """
    before = corpus_fingerprint([_casefile([("doc1", "The figure was 12.")])])
    after = corpus_fingerprint([_casefile([("doc1", "The figure was restated to 14.")])])
    assert before != after


def test_reordering_documents_changes_the_fingerprint() -> None:
    """Padding order is reshuffled between arms, so it is part of the prompt."""
    forwards = _casefile([("doc1", "alpha"), ("doc2", "beta")])
    backwards = _casefile([("doc2", "beta"), ("doc1", "alpha")])
    assert corpus_fingerprint([forwards]) != corpus_fingerprint([backwards])


def test_an_item_without_documents_still_fingerprints() -> None:
    """The rel-* corpus has no documents and must keep working unchanged."""
    assert corpus_fingerprint([_item()])
