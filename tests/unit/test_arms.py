"""Tests for the experimental arms.

The three invariants asserted here are the ones that make the comparison fair.
If any of them breaks, the harness still runs and still produces numbers -- it
just stops measuring what it claims to measure, which is why they are tests
rather than review notes.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from decision_evals.generators.generate import generate
from decision_evals.generators.schema import Template
from decision_evals.solvers.arms import (
    ARM_NAMES,
    BASE_FRAMING,
    COT_INSTRUCTION,
    FORMAT_CONTRACT,
    ArmError,
    ArmName,
    build_arm,
    check_placebo_match,
    render_item,
)

Build = Callable[..., dict[str, Any]]

SKILL = "# Ledger\n\n## Step one\nVerify each fact.\n\n## Step two\nDiscard the inert ones."
PLACEBO = "# Notes\n\n## Consider\nRead with care.\n\n## Proceed\nThen answer as usual here."


def _build(arm: ArmName) -> str:
    return build_arm(arm, skill_body=SKILL, placebo_body=PLACEBO).system_prompt


# -- the three invariants ---------------------------------------------------


@pytest.mark.parametrize("arm", ARM_NAMES)
def test_the_format_contract_is_in_every_arm(arm: ArmName) -> None:
    """Otherwise the experiment measures instruction-following, not decisions."""
    assert FORMAT_CONTRACT in _build(arm)


@pytest.mark.parametrize("arm", ARM_NAMES)
def test_the_task_framing_is_in_every_arm(arm: ArmName) -> None:
    """No arm may be better oriented than another before the skill is introduced."""
    assert BASE_FRAMING in _build(arm)


def test_the_option_menu_does_not_vary_by_arm(template_dict: Build) -> None:
    """AgentAtlas measured 14-40pp from the menu alone -- larger than any effect here.

    Rendering is arm-independent by construction; this asserts that stays true.
    """
    item = generate(Template.model_validate(template_dict()), 1)[0]
    rendered = render_item(item)
    for option in item.options:
        assert f"- {option}" in rendered
    assert "Options:" in rendered


# -- arm content ------------------------------------------------------------


def test_the_control_carries_no_intervention() -> None:
    prompt = _build("off")
    assert SKILL not in prompt
    assert PLACEBO not in prompt
    assert COT_INSTRUCTION not in prompt


def test_the_treatment_carries_the_skill() -> None:
    assert SKILL in _build("on")


def test_the_placebo_carries_filler_and_not_the_skill() -> None:
    prompt = _build("placebo")
    assert PLACEBO in prompt
    assert SKILL not in prompt


def test_the_cot_arm_is_the_plainest_phrasing() -> None:
    """A tuned CoT prompt would be a different experiment."""
    prompt = _build("cot")
    assert COT_INSTRUCTION in prompt
    assert SKILL not in prompt


def test_only_the_in_situ_arm_appends() -> None:
    for arm in ARM_NAMES:
        expected = arm == "in_situ"
        assert build_arm(arm, skill_body=SKILL, placebo_body=PLACEBO).append is expected


def test_in_situ_carries_the_same_skill_as_the_treatment() -> None:
    assert SKILL in _build("in_situ")


# -- refusals ---------------------------------------------------------------


def test_an_unknown_arm_is_refused() -> None:
    with pytest.raises(ArmError, match="unknown arm"):
        build_arm("sideways")  # type: ignore[arg-type]


@pytest.mark.parametrize("arm", ["on", "in_situ"])
def test_a_missing_skill_body_is_an_error_not_a_silent_control(arm: ArmName) -> None:
    """An arm that quietly degrades into `off` yields a null that looks like evidence."""
    with pytest.raises(ArmError, match="needs a skill body"):
        build_arm(arm, placebo_body=PLACEBO)


def test_a_missing_placebo_body_is_refused() -> None:
    with pytest.raises(ArmError, match="needs a placebo body"):
        build_arm("placebo", skill_body=SKILL)


# -- placebo matching -------------------------------------------------------


def test_a_well_matched_placebo_passes() -> None:
    match = check_placebo_match(SKILL, PLACEBO)
    assert match.ok
    assert match.structure_matches


def test_a_short_placebo_is_rejected() -> None:
    """The obvious failure: two lines standing in for two pages."""
    match = check_placebo_match(SKILL, "# Notes\n\n## A\nShort.")
    assert not match.ok
    assert not match.words_match


def test_a_structurally_different_placebo_is_rejected() -> None:
    flat = " ".join(["word"] * len(SKILL.split()))
    match = check_placebo_match(SKILL, flat)
    assert match.words_match
    assert not match.structure_matches
    assert not match.ok


def test_the_tolerance_is_adjustable() -> None:
    padded = PLACEBO + " one two three four five six seven"
    assert not check_placebo_match(SKILL, padded, tolerance=0.01).words_match
    assert check_placebo_match(SKILL, padded, tolerance=0.9).words_match


def test_an_empty_skill_has_a_defined_ratio() -> None:
    assert check_placebo_match("", PLACEBO).word_ratio == 0.0


def test_a_placebo_without_the_skills_output_template_is_not_matched() -> None:
    """Word count and heading count are both blind to a fenced output block.

    A treatment that hands the model a template and a placebo that does not is
    an arm pair differing in how much structure was requested -- which is
    exactly what the venue's own five-block contract then scores. An arm winning
    because it was told to emit more structure is a format effect wearing a
    decision effect's clothes.
    """
    skill = "# S\n\nsome guidance\n\n```\nBLOCK\n  <thing>\n```\n"
    placebo = "# P\n\nsome guidance\n\nwritten as ordinary prose instead.\n"

    match = check_placebo_match(skill, placebo)
    assert not match.templates_match
    assert not match.ok


def test_matching_fenced_blocks_satisfy_the_template_check() -> None:
    skill = "# S\n\nguidance here\n\n```\nBLOCK\n  <thing>\n```\n"
    placebo = "# P\n\nguidance there\n\n```\nSECTION\n  <thing>\n```\n"

    assert check_placebo_match(skill, placebo).templates_match


def test_two_documents_with_no_templates_at_all_match() -> None:
    """Most skills carry no output block; the check must not invent a failure."""
    assert check_placebo_match("# S\n\nprose", "# P\n\nprose").templates_match


# -- the shipped placebo against the shipped extractor ----------------------

#: A reply that obeys `placebo-council.md`'s four-slot template and the format
#: contract. Hand-written, so this costs no model call, and it is the check that
#: would catch a format collision between a placebo's output block and the
#: `ANSWER:` line before a run is spent finding out.
TEMPLATE_FOLLOWING_REPLY = """WHAT THEY ASKED
  Whether to take the offer or keep going.

WHAT YOU UNDERSTOOD
  The price clears the mark they set themselves, and runway is eleven months.

WHAT YOU SAY
  Take it. The number they wrote down before anyone was buying has been met.

HOW YOU LEAVE IT
  You set the number cold, and it was met.

ANSWER: Sell the company now"""


def test_a_reply_following_the_council_placebo_template_still_parses() -> None:
    from decision_evals.scorers.answer import parse_answer

    options = ["Sell the company now", "Keep building for another year"]
    parsed = parse_answer(TEMPLATE_FOLLOWING_REPLY, options)
    assert parsed.ok
    assert parsed.value == "Sell the company now"


def test_the_council_placebo_arm_carries_no_frontmatter() -> None:
    """The marker is for the site and the guard, never for the model."""
    from decision_evals.generators.loader import REPO_ROOT
    from decision_evals.skills import delivered_body

    body = delivered_body(REPO_ROOT / "skills" / "decision-making" / "placebo-council.md")
    prompt = build_arm("placebo", placebo_body=body).system_prompt
    assert "matched_to" not in prompt
    assert "# Writing back to someone" in prompt
