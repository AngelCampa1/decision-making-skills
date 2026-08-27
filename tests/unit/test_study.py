"""The five-arm study's arithmetic, against fabricated records.

No model calls. What is checked here is the part that decides a verdict: which
records belong to which arm, which questions two arms share, what the paired
test is handed, and what the correction does to it. Every one of those has a
plausible wrong version that produces a clean number.
"""

from __future__ import annotations

import pytest

from decision_evals.evolution.holdout import HOLDOUT_FLOOR
from decision_evals.evolution.study import (
    Arm,
    ItemSet,
    StudyError,
    StudyRequest,
    analyse,
    by_arm,
    compare,
)
from decision_evals.runner import RunRecord

GEPA_BODY = "# GEPA winner\n\nDo the thing well."
SKILLOPT_BODY = "# SkillOpt winner\n\nDo the thing differently."

ARMS = (
    Arm(label="off", kind="off"),
    Arm(label="placebo", kind="placebo", body="# Placebo\n\nWords."),
    Arm(label="gepa", kind="candidate", body=GEPA_BODY),
    Arm(label="skillopt", kind="candidate", body=SKILLOPT_BODY),
)


def _record(
    *,
    arm: str,
    item_id: str,
    correct: bool,
    seed: int = HOLDOUT_FLOOR,
    candidate_sha: str | None = None,
    template_id: str = "rel-001-vendor-outage",
) -> RunRecord:
    return RunRecord(
        item_id=item_id,
        template_id=template_id,
        arm=arm,
        model="mockllm/deterministic",
        n_distractors=0,
        position="none",
        expected="a",
        parsed="a" if correct else "b",
        parse_status="parsed",
        correct=correct,
        zero_cause=None if correct else "agent_wrong",
        cost_usd=0.0,
        input_tokens=1,
        output_tokens=1,
        duration_ms=1,
        response="",
        seed=seed,
        candidate_sha=candidate_sha,
    )


class TestWhichArmARecordBelongsTo:
    def test_two_candidate_arms_are_told_apart_by_their_body(self) -> None:
        """Both record `arm="candidate"`. Keying on the arm name alone would pool
        two engines into one number and report it as one arm."""
        gepa = ARMS[2]
        skillopt = ARMS[3]
        records = [
            _record(arm="candidate", item_id="i1", correct=True, candidate_sha=gepa.sha),
            _record(arm="candidate", item_id="i1", correct=False, candidate_sha=skillopt.sha),
        ]
        table = by_arm(records, ARMS)
        assert table["gepa"][(HOLDOUT_FLOOR, "i1")] is True
        assert table["skillopt"][(HOLDOUT_FLOOR, "i1")] is False

    def test_a_record_from_no_declared_arm_is_dropped(self) -> None:
        """A body nobody declared cannot be silently counted as one that was."""
        records = [_record(arm="candidate", item_id="i1", correct=True, candidate_sha="deadbeef")]
        table = by_arm(records, ARMS)
        assert all(not answers for answers in table.values())

    def test_the_same_item_id_under_two_seeds_is_two_questions(self) -> None:
        """`item_id` carries the template and the stratum and not the seed, so
        keying on it alone would collapse two scenarios into one."""
        records = [
            _record(arm="off", item_id="i1", correct=True, seed=HOLDOUT_FLOOR),
            _record(arm="off", item_id="i1", correct=False, seed=HOLDOUT_FLOOR + 1),
        ]
        assert len(by_arm(records, ARMS)["off"]) == 2


class TestTheComparison:
    def test_an_arm_that_wins_every_discordant_pair_beats_the_control(self) -> None:
        records = []
        for index in range(20):
            records.append(
                _record(
                    arm="placebo",
                    item_id=f"i{index}",
                    correct=index < 10,
                    candidate_sha=ARMS[1].sha,
                )
            )
            records.append(
                _record(
                    arm="candidate",
                    item_id=f"i{index}",
                    correct=True,
                    candidate_sha=ARMS[2].sha,
                )
            )
        outcome = compare("unseen", "gepa", by_arm(records, ARMS))
        assert (outcome.arm_only, outcome.control_only) == (10, 0)
        assert outcome.effect == pytest.approx(0.5)
        assert outcome.p_value < 0.01

    def test_only_the_questions_both_arms_answered_are_paired(self) -> None:
        """An arm missing an item is dropped from that comparison, not from the
        study, and `n_pairs` says how many were left. A comparison quietly
        computed over fewer items than its neighbour is what nobody notices."""
        records = [
            _record(arm="placebo", item_id="i1", correct=True, candidate_sha=ARMS[1].sha),
            _record(arm="placebo", item_id="i2", correct=True, candidate_sha=ARMS[1].sha),
            _record(arm="candidate", item_id="i1", correct=True, candidate_sha=ARMS[2].sha),
        ]
        assert compare("unseen", "gepa", by_arm(records, ARMS)).n_pairs == 1

    def test_a_comparison_with_no_shared_question_is_refused(self) -> None:
        records = [
            _record(arm="placebo", item_id="i1", correct=True, candidate_sha=ARMS[1].sha),
            _record(arm="candidate", item_id="i2", correct=True, candidate_sha=ARMS[2].sha),
        ]
        with pytest.raises(StudyError, match="no question in common"):
            compare("unseen", "gepa", by_arm(records, ARMS))

    def test_a_control_that_ran_nothing_is_refused_rather_than_defaulted(self) -> None:
        """`by_arm` seeds a key for every declared arm, so a control that never
        ran is present and empty. Checking for the key alone would pass it
        through to a comparison over nothing."""
        records = [_record(arm="off", item_id="i1", correct=True)]
        with pytest.raises(StudyError, match="nothing to compare against"):
            compare("unseen", "off", by_arm(records, ARMS), control="placebo")

    def test_the_test_is_one_sided_in_the_direction_of_helping(self) -> None:
        """An arm that loses every discordant pair must not come out significant
        for losing. A two-sided test here would report a harmful arm as a result."""
        records = []
        for index in range(20):
            records.append(
                _record(arm="placebo", item_id=f"i{index}", correct=True, candidate_sha=ARMS[1].sha)
            )
            records.append(
                _record(
                    arm="candidate",
                    item_id=f"i{index}",
                    correct=index < 10,
                    candidate_sha=ARMS[2].sha,
                )
            )
        outcome = compare("unseen", "gepa", by_arm(records, ARMS))
        assert outcome.effect < 0
        assert outcome.p_value > 0.9


class TestTheSetsAreNeverPooled:
    def _both_sets(self) -> tuple[list[RunRecord], tuple[ItemSet, ...]]:
        sets = (
            ItemSet(label="unseen", templates=("rel-001-vendor-outage",), seeds=(HOLDOUT_FLOOR,)),
            ItemSet(
                label="seen", templates=("rel-003-oncall-escalate",), seeds=(HOLDOUT_FLOOR + 1,)
            ),
        )
        records = []
        for index in range(10):
            # Unseen: the candidate matches the placebo exactly.
            records.append(
                _record(
                    arm="placebo",
                    item_id=f"u{index}",
                    correct=index < 5,
                    seed=HOLDOUT_FLOOR,
                    candidate_sha=ARMS[1].sha,
                )
            )
            records.append(
                _record(
                    arm="candidate",
                    item_id=f"u{index}",
                    correct=index < 5,
                    seed=HOLDOUT_FLOOR,
                    candidate_sha=ARMS[2].sha,
                )
            )
            # Seen: the candidate wins every discordant pair.
            records.append(
                _record(
                    arm="placebo",
                    item_id=f"s{index}",
                    correct=False,
                    seed=HOLDOUT_FLOOR + 1,
                    template_id="rel-003-oncall-escalate",
                    candidate_sha=ARMS[1].sha,
                )
            )
            records.append(
                _record(
                    arm="candidate",
                    item_id=f"s{index}",
                    correct=True,
                    seed=HOLDOUT_FLOOR + 1,
                    template_id="rel-003-oncall-escalate",
                    candidate_sha=ARMS[2].sha,
                )
            )
        return records, sets

    def test_a_set_reads_only_its_own_seeds_and_templates(self) -> None:
        records, sets = self._both_sets()
        unseen, seen = analyse(records, ARMS[:3], sets)
        assert (unseen.n_items, seen.n_items) == (10, 10)
        assert unseen.accuracy["gepa"] == pytest.approx(0.5)
        assert seen.accuracy["gepa"] == pytest.approx(1.0)

    def test_a_win_on_one_set_does_not_carry_to_the_other(self) -> None:
        """Transfer and memorisation are different questions, and a pooled number
        answers neither."""
        records, sets = self._both_sets()
        unseen, seen = analyse(records, ARMS[:3], sets)
        assert not unseen.comparisons[0].rejected
        assert seen.comparisons[0].rejected

    def test_the_correction_family_excludes_the_control_and_the_empty_arm(self) -> None:
        """`off` answers whether any document helps, which is a different question
        from whether this one does, so correcting it alongside would spend power
        on a hypothesis nobody registered."""
        records, sets = self._both_sets()
        unseen, _ = analyse(records, ARMS[:3], sets)
        assert [c.arm for c in unseen.comparisons] == ["gepa"]


class TestTheRequestRefusesAnUnsoundStudy:
    def test_a_seed_a_search_could_reach_is_refused(self) -> None:
        """Scoring on anything a search touched is reporting training accuracy,
        which is the practice this design exists to test."""
        with pytest.raises(StudyError, match="not holdout seeds"):
            StudyRequest(
                target_model="mockllm/deterministic",
                sets=(ItemSet(label="unseen", templates=("rel-001-vendor-outage",), seeds=(0,)),),
            )

    def test_two_sets_cannot_share_a_label(self) -> None:
        with pytest.raises(StudyError, match="distinct labels"):
            StudyRequest(
                target_model="mockllm/deterministic",
                sets=(
                    ItemSet(label="x", templates=("a",), seeds=(HOLDOUT_FLOOR,)),
                    ItemSet(label="x", templates=("b",), seeds=(HOLDOUT_FLOOR,)),
                ),
            )

    def test_a_study_with_no_items_is_refused(self) -> None:
        with pytest.raises(StudyError, match="at least one item set"):
            StudyRequest(target_model="mockllm/deterministic", sets=())
