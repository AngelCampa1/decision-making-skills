"""The five-arm study's arithmetic, against fabricated records.

No model calls. What is checked here is the part that decides a verdict: which
records belong to which arm, which questions two arms share, what the paired
test is handed, and what the correction does to it. Every one of those has a
plausible wrong version that produces a clean number.
"""

from __future__ import annotations

import itertools
import json
from datetime import date
from pathlib import Path

import pytest

from decision_evals.evolution import study
from decision_evals.evolution.checkpoints import RunPaths, paths_for
from decision_evals.evolution.holdout import HOLDOUT_FLOOR
from decision_evals.evolution.run import EvolveError
from decision_evals.evolution.study import (
    Arm,
    ArmPasses,
    ItemSet,
    PassAgreement,
    SetPasses,
    StudyError,
    StudyRequest,
    analyse,
    analyse_passes,
    by_arm,
    compare,
    freeze,
    load_pass,
    records_path,
    run_study,
)
from decision_evals.evolution.venues import MOCK_MODEL, mock_call, venue_for
from decision_evals.runner import RunRecord, load_records

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


# ---------------------------------------------------------------------------
# The 2026-09-02 changes: per-arm files, passes, chunked ordering, the corpus.
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = str(REPO_ROOT / "datasets" / "templates")
HARD = str(REPO_ROOT / "datasets" / "templates-hard")


class TestAnArmLabelIsAFileName:
    def test_a_label_with_a_separator_is_refused(self) -> None:
        """`figures.load_readings` reads the arm back off `records-<label>.jsonl`,
        so a label that cannot name one file cannot be read back."""
        with pytest.raises(StudyError, match="cannot name a checkpoint"):
            Arm(label="gepa/v2", kind="candidate", body="x")

    def test_the_aa_label_is_taken(self) -> None:
        with pytest.raises(StudyError, match="cannot name a checkpoint"):
            Arm(label="aa", kind="placebo", body="x")

    def test_an_ordinary_label_is_accepted(self) -> None:
        assert Arm(label="skillopt-2", kind="candidate", body="x").label == "skillopt-2"


class TestWhereAnArmsRecordsGo:
    def test_pass_one_is_the_published_layout(self, tmp_path: Path) -> None:
        assert records_path(tmp_path, "off") == tmp_path / "records-off.jsonl"

    def test_a_later_pass_is_its_own_checkpoint(self, tmp_path: Path) -> None:
        """Resume keys carry no pass index, so a second pass into the first file
        would be skipped as already done and report agreement it never measured."""
        assert records_path(tmp_path, "off", 3) == tmp_path / "pass-3" / "records-off.jsonl"

    def test_an_arm_with_no_file_is_left_out(self, tmp_path: Path) -> None:
        assert load_pass(tmp_path, ARMS) == []


class TestTheRequestRefusesAnUnsoundSchedule:
    def _sets(self) -> tuple[ItemSet, ...]:
        return (ItemSet(label="u", templates=("rel-001-vendor-outage",), seeds=(HOLDOUT_FLOOR,)),)

    def test_zero_passes_is_refused(self) -> None:
        with pytest.raises(StudyError, match="at least one pass"):
            StudyRequest(target_model="mockllm/deterministic", sets=self._sets(), passes=0)

    def test_an_empty_chunk_is_refused(self) -> None:
        with pytest.raises(StudyError, match="at least one item"):
            StudyRequest(target_model="mockllm/deterministic", sets=self._sets(), chunk=0)

    def test_the_defaults_are_one_pass_of_eight_item_chunks(self) -> None:
        request = StudyRequest(target_model="mockllm/deterministic", sets=self._sets())
        assert (request.passes, request.chunk, request.templates_root) == (
            1,
            8,
            "datasets/templates",
        )


class TestPassAgreement:
    def _set(self) -> ItemSet:
        return ItemSet(label="unseen", templates=("rel-001-vendor-outage",), seeds=(HOLDOUT_FLOOR,))

    def _pass(self, pattern: list[bool]) -> list[RunRecord]:
        return [
            _record(arm="off", item_id=f"i{index}", correct=correct)
            for index, correct in enumerate(pattern)
        ]

    def test_identical_passes_agree_everywhere(self) -> None:
        first = self._pass([True, False] * 5)
        (outcome,) = analyse_passes([first, first], ARMS[:1], [self._set()])
        (row,) = outcome.arms
        assert row.accuracy == (0.5, 0.5)
        (agreement,) = row.agreement
        assert (agreement.pass_index, agreement.n_pairs) == (2, 10)
        assert (agreement.identical, agreement.different) == (10, 0)
        assert agreement.p_value == 1.0

    def test_a_pass_that_drifts_one_way_is_seen_by_the_test(self) -> None:
        """Every disagreement in the same direction is what a venue that changed
        between passes looks like, and the two-sided McNemar reads it."""
        first = self._pass([False] * 12)
        second = self._pass([True] * 12)
        (outcome,) = analyse_passes([first, second], ARMS[:1], [self._set()])
        (agreement,) = outcome.arms[0].agreement
        assert (agreement.identical, agreement.different) == (0, 12)
        assert agreement.p_value < 0.01
        assert outcome.arms[0].accuracy == (0.0, 1.0)

    def test_only_shared_questions_are_paired(self) -> None:
        first = self._pass([True] * 6)
        second = self._pass([True] * 4)
        (outcome,) = analyse_passes([first, second], ARMS[:1], [self._set()])
        assert outcome.arms[0].agreement[0].n_pairs == 4

    def test_a_pass_sharing_nothing_gets_an_accuracy_and_no_agreement(self) -> None:
        """A McNemar over nothing would print 1.0 and read as perfect."""
        first = self._pass([True] * 4)
        second = [_record(arm="off", item_id="other", correct=False, seed=HOLDOUT_FLOOR + 1)]
        (outcome,) = analyse_passes([first, second], ARMS[:1], [self._set()])
        assert outcome.arms[0].accuracy == (1.0, 0.0)
        assert outcome.arms[0].agreement == ()

    def test_each_pass_is_measured_against_the_first(self) -> None:
        first = self._pass([True] * 4)
        second = self._pass([False] * 4)
        third = self._pass([True] * 4)
        (outcome,) = analyse_passes([first, second, third], ARMS[:1], [self._set()])
        assert [a.pass_index for a in outcome.arms[0].agreement] == [2, 3]
        assert [a.identical for a in outcome.arms[0].agreement] == [0, 4]


class TestFreezingThePasses:
    def _paths(self, tmp_path: Path) -> RunPaths:
        paths = paths_for(tmp_path, "2026-09-02-abc1234-study")
        paths.root.mkdir(parents=True)
        return paths

    def test_a_one_pass_study_writes_the_keys_it_always_had(self, tmp_path: Path) -> None:
        paths = self._paths(tmp_path)
        freeze(paths, ())
        assert list(json.loads((paths.root / "analysis.json").read_text())) == [
            "control",
            "sets",
            "aa",
        ]

    def test_a_repeated_study_writes_its_passes(self, tmp_path: Path) -> None:
        paths = self._paths(tmp_path)
        passes = (
            SetPasses(
                label="unseen",
                arms=(
                    ArmPasses(
                        arm="off",
                        accuracy=(0.5, 0.6),
                        agreement=(
                            PassAgreement(
                                pass_index=2, n_pairs=10, identical=9, different=1, p_value=1.0
                            ),
                        ),
                    ),
                ),
            ),
        )
        freeze(paths, (), None, passes)
        written = json.loads((paths.root / "analysis.json").read_text())
        assert written["passes"][0]["arms"][0]["accuracy"] == [0.5, 0.6]
        assert written["passes"][0]["arms"][0]["agreement"][0]["identical"] == 9


class TestRunningTheStudyOnTheMockVenue:
    """No server. What is checked is the schedule and the files it leaves."""

    def _request(self, **overrides: object) -> StudyRequest:
        fields: dict[str, object] = {
            "target_model": MOCK_MODEL,
            "sets": (
                ItemSet(
                    label="unseen", templates=("rel-001-vendor-outage",), seeds=(HOLDOUT_FLOOR,)
                ),
            ),
            "templates_root": TEMPLATES,
            "chunk": 4,
        }
        fields.update(overrides)
        return StudyRequest(**fields)  # type: ignore[arg-type]

    def _run(self, tmp_path: Path, request: StudyRequest, arms: tuple[Arm, ...] = ARMS[:2]):
        return run_study(
            request,
            arms,
            venue=venue_for(MOCK_MODEL),
            repo_root=tmp_path,
            git_sha="abc1234",
            on=date(2026, 9, 2),
        )

    def test_every_arm_writes_its_own_file(self, tmp_path: Path) -> None:
        """The published run's per-arm files were split by hand from one
        checkpoint. `figures.load_readings` reads the arm off the file name."""
        result = self._run(tmp_path, self._request())
        names = sorted(path.name for path in result.paths.root.glob("*.jsonl"))
        assert names == ["records-aa.jsonl", "records-off.jsonl", "records-placebo.jsonl"]
        assert not result.paths.records.exists()
        assert all(r.arm == "off" for r in load_records(result.paths.root / "records-off.jsonl"))

    def test_the_manifest_records_the_schedule_and_the_corpus(self, tmp_path: Path) -> None:
        result = self._run(tmp_path, self._request(passes=2))
        manifest = json.loads((result.paths.root / "run.json").read_text(encoding="utf-8"))
        assert manifest["ordering"] == "item-major"
        assert (manifest["chunk"], manifest["passes"]) == (4, 2)
        assert manifest["request"]["templates_root"] == TEMPLATES
        assert manifest["templates_roots"] == [TEMPLATES]

    def test_arms_interleave_by_chunk(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """No arm runs as one block. Four items of `off`, four of `placebo`,
        then the next four of `off`, for the whole set."""
        seen: list[str] = []
        inner = mock_call()

        def recording(prompt: str, system_prompt: str, append: bool):
            seen.append(system_prompt)
            return inner(prompt, system_prompt, append)

        monkeypatch.setattr(study, "call_fn", lambda *_a, **_k: recording)
        self._run(tmp_path, self._request(run_aa=False))
        runs = [len(list(group)) for _, group in itertools.groupby(seen)]
        assert len(seen) == 28 * 2
        assert runs == [4] * 14
        assert len(set(seen[:4])) == 1
        assert seen[0] != seen[4]

    def test_a_second_invocation_answers_nothing_again(self, tmp_path: Path) -> None:
        """Resume is per file and per key: the run is repeated and every
        checkpoint is byte-identical afterwards."""
        request = self._request(passes=2)
        first = self._run(tmp_path, request)
        before = {p: p.read_bytes() for p in first.paths.root.rglob("*.jsonl")}
        again = self._run(tmp_path, request)
        after = {p: p.read_bytes() for p in again.paths.root.rglob("*.jsonl")}
        assert before == after
        assert again.records == first.records

    def test_a_later_pass_is_a_separate_checkpoint_and_is_analysed(self, tmp_path: Path) -> None:
        result = self._run(tmp_path, self._request(passes=2))
        assert (result.paths.root / "pass-2" / "records-off.jsonl").is_file()
        assert (result.paths.root / "pass-2" / "records-placebo.jsonl").is_file()
        assert not (result.paths.root / "pass-2" / "records-aa.jsonl").exists()
        (unseen,) = result.passes
        assert [row.arm for row in unseen.arms] == ["off", "placebo"]
        for row in unseen.arms:
            assert len(row.accuracy) == 2
            (agreement,) = row.agreement
            assert agreement.n_pairs == 28
        assert result.records == 28 * 2 * 2

    def test_the_registered_numbers_read_pass_one_only(self, tmp_path: Path) -> None:
        """Adding passes cannot move a registered comparison."""
        one = self._run(tmp_path / "one", self._request(passes=1))
        two = self._run(tmp_path / "two", self._request(passes=3))
        assert one.sets == two.sets
        assert one.passes == ()
        assert len(two.passes[0].arms[0].agreement) == 2

    def test_a_pooled_corpus_reaches_the_items(self, tmp_path: Path) -> None:
        request = self._request(
            sets=(
                ItemSet(
                    label="unseen",
                    templates=("rel-001-vendor-outage", "hrd-001-warranty-claim"),
                    seeds=(HOLDOUT_FLOOR,),
                ),
            ),
            templates_root=f"{TEMPLATES},{HARD}",
        )
        result = self._run(tmp_path, request)
        manifest = json.loads((result.paths.root / "run.json").read_text(encoding="utf-8"))
        assert manifest["sets"]["unseen"]["templates"] == [
            "hrd-001-warranty-claim",
            "rel-001-vendor-outage",
        ]
        assert manifest["templates_roots"] == [TEMPLATES, HARD]

    def test_a_template_outside_the_root_is_refused_before_any_call(self, tmp_path: Path) -> None:
        request = self._request(
            sets=(
                ItemSet(label="u", templates=("hrd-001-warranty-claim",), seeds=(HOLDOUT_FLOOR,)),
            )
        )
        with pytest.raises(EvolveError, match="no template answers to"):
            self._run(tmp_path, request)
