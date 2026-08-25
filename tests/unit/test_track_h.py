"""Track H Phase 0 scoring: the J-equals-d identity, the clustering guard, the
falsifier gate, and both movement-threshold rules.

Ten sections. The first four are the proofs standing rule 2 and the H1
registration ask for:

1. Youden's J is numerically identical to the programme's ``d`` (module
   docstring's algebra, checked rather than trusted).
2. Clustering on the triplet gives a materially different interval than
   pooling over files/items — the exact defect ``docs/STATUS.md`` records as
   "pooled AUC used on a matched corpus".
3. The falsifier battery passes a known-good extractor and refuses on a
   known-bad one, and no ``Phase0Result`` is reachable without a passed
   battery.
4. The movement threshold is derivable from, and only from, base-arm records.

The next six cover ``pooled_log_noise_v2`` and what it replaced:

5. The log scale is symmetric in direction where the relative scale is not,
   with ``t04``'s and ``t03``'s arithmetic checked rather than quoted.
6. A threshold carries the rule that derived it, and a threshold from one scale
   is refused by the other's comparison.
7. ``sigma-hat`` is RMS about zero, its estimand is fixed in n, and the maximum's
   is not.
8. The structural ceiling on specificity, and the inert-instrument signature a
   run at that ceiling produces.
9. Recomputing the threshold inside each replicate, and the interval width a
   fixed threshold understates.
10. Events that cannot be put on the scale are dropped from both arms, counted,
    and reported.

Everything else here is the ordinary edge-case sweep needed for the 100%
line+branch floor on ``decision_evals/stats``.
"""

from __future__ import annotations

import dataclasses
import math

import numpy as np
import pytest

from decision_evals.stats.agreement import fleiss_kappa
from decision_evals.stats.cluster import cluster_bootstrap_diff
from decision_evals.stats.track_h import (
    ADEQUACY_CEILING,
    KILL_THRESHOLD_J,
    BaseRepeatPair,
    FalsifierBatteryFailedError,
    FalsifierBatteryResult,
    FalsifierCase,
    MovementThreshold,
    Phase0Result,
    TripletEvent,
    classify_movement,
    compute_phase0_result,
    derive_movement_threshold,
    derive_movement_threshold_pooled,
    exceeds_log_threshold,
    exceeds_relative_threshold,
    extractor_movement_agreement,
    log_movement,
    relative_movement,
    run_falsifier_battery,
    specificity_ceiling,
)

# --------------------------------------------------------------------------- #
# Shared fixtures
# --------------------------------------------------------------------------- #

#: A threshold with a round value, for tests that don't need to derive one.
THRESHOLD = MovementThreshold(value=0.10, n_base_pairs=20, max_triplet_id="t07")


def _events(
    n_triplets: int = 20,
    *,
    sensitivity_rate: float = 0.85,
    specificity_rate: float = 0.60,
    seed: int = 0,
) -> list[TripletEvent]:
    """40 synthetic Phase 0 events (n_triplets triplets x 2 repeats).

    Governing contrasts move at ``sensitivity_rate``; matched contrasts hold at
    ``specificity_rate``. Movement is encoded directly as a 10x jump (always
    above THRESHOLD) or a 0.1% wiggle (always below it), so the classification
    is unambiguous and the test is about the estimator, not the boundary.
    """
    rng = np.random.default_rng(seed)
    events: list[TripletEvent] = []
    for t in range(n_triplets):
        triplet_id = f"t{t:02d}"
        for repeat in (0, 1):
            q_base = 10.0
            q_governing = q_base * 10.0 if rng.random() < sensitivity_rate else q_base * 1.001
            q_matched = q_base * 10.0 if rng.random() < (1 - specificity_rate) else q_base * 1.001
            events.append(
                TripletEvent(
                    triplet_id=triplet_id,
                    repeat=repeat,
                    q_base=q_base,
                    q_governing=q_governing,
                    q_matched=q_matched,
                )
            )
    return events


def _base_pairs(n_triplets: int = 20) -> list[BaseRepeatPair]:
    """One base repeat-0/repeat-1 pair per triplet, matching ``_events``' ids.

    Small, positive, and unequal excursions: positive because the log scale
    refuses anything else, unequal so a pooled sigma-hat is not trivially zero.
    """
    return [
        BaseRepeatPair(
            triplet_id=f"t{t:02d}",
            q_repeat0=10.0,
            q_repeat1=10.0 * (1.0 + 0.01 * (1 + t % 3)),
        )
        for t in range(n_triplets)
    ]


def _v1(
    events: list[TripletEvent],
    battery: FalsifierBatteryResult,
    *,
    threshold: MovementThreshold | None = None,
    seed: int | None = None,
) -> Phase0Result:
    """Score under ``max_relative_v1``, the fixed-threshold path it needs."""
    return compute_phase0_result(
        events,
        THRESHOLD if threshold is None else threshold,
        battery,
        base_pairs=_base_pairs(),
        recompute_threshold=False,
        seed=seed,
    )


def _passed_battery() -> FalsifierBatteryResult:
    cases = [
        FalsifierCase(
            name="obvious-move",
            q_base=10.0,
            q_governing=100.0,
            q_matched=10.05,
            expect_governing_change=True,
            expect_matched_change=False,
        ),
        FalsifierCase(
            name="obvious-still",
            q_base=20.0,
            q_governing=90.0,
            q_matched=20.02,
            expect_governing_change=True,
            expect_matched_change=False,
        ),
    ]
    return run_falsifier_battery(cases, THRESHOLD)


# --------------------------------------------------------------------------- #
# 1. J is identically d
# --------------------------------------------------------------------------- #


class TestJEqualsD:
    def test_j_equals_sensitivity_plus_specificity_minus_one(self) -> None:
        """J = sens + spec - 1, computed two independent ways, must agree.

        ``compute_phase0_result`` reports J as the cluster-bootstrap point
        estimate (mean(governing_change) - mean(matched_change)) and,
        separately, sensitivity and specificity as their own means. The
        registration's algebra says these must coincide; this asserts it
        numerically rather than trusting the derivation in the docstring.
        """
        events = _events(seed=1)
        battery = _passed_battery()
        result = _v1(events, battery, seed=42)

        assert result.j == pytest.approx(result.sensitivity + result.specificity - 1.0, abs=1e-12)

    def test_j_equals_d_the_raw_paired_mean_difference(self) -> None:
        """d = P(change|governing) - P(change|matched), computed from raw
        indicator arrays with plain numpy, must equal the reported J exactly
        up to floating summation order.
        """
        events = _events(seed=2)
        battery = _passed_battery()
        result = _v1(events, battery, seed=7)

        governing = np.array(
            [classify_movement(e.q_base, e.q_governing, THRESHOLD) for e in events],
            dtype=np.float64,
        )
        matched = np.array(
            [classify_movement(e.q_base, e.q_matched, THRESHOLD) for e in events],
            dtype=np.float64,
        )
        d = float(governing.mean() - matched.mean())

        assert result.j == pytest.approx(d, abs=1e-12)

    def test_symmetric_0_85_reaches_the_registered_kill_exactly(self) -> None:
        """0.85 + 0.85 - 1 == KILL_THRESHOLD_J, the arithmetic the registration
        checks rather than asserts. 34/40 on each arm is the reachable state at
        this resolution (0.85 * 40 == 34, an integer).
        """
        assert pytest.approx(KILL_THRESHOLD_J) == 0.85 + 0.85 - 1.0
        assert 0.85 * 40 == 34.0
        assert ADEQUACY_CEILING == 0.85


# --------------------------------------------------------------------------- #
# 2. Clustering on the triplet is not optional
# --------------------------------------------------------------------------- #


class TestClusteringVersusPooling:
    def test_pooling_over_items_gives_a_different_interval_than_clustering_on_triplets(
        self,
    ) -> None:
        """Matched-triplet data with strong within-triplet correlation, scored
        two ways: once clustered on the triplet id (correct — what
        ``compute_phase0_result`` always does) and once with every item its own
        singleton cluster (the "pooled over files" shape defect nine on
        ``docs/STATUS.md`` names). If clustering did nothing, the two intervals
        would coincide; they must not.
        """
        rng = np.random.default_rng(11)
        n_triplets = 20
        triplet_ids: list[str] = []
        diffs: list[float] = []
        # A large per-triplet random effect plus small item-level noise: high
        # within-triplet correlation, the shape Track H's matched design has.
        for t in range(n_triplets):
            triplet_effect = rng.normal(loc=0.3, scale=0.4)
            for _repeat in (0, 1):
                triplet_ids.append(f"t{t:02d}")
                diffs.append(triplet_effect + rng.normal(scale=0.02))

        zeros = np.zeros(len(diffs), dtype=np.float64)
        treatment = np.array(diffs, dtype=np.float64)

        clustered = cluster_bootstrap_diff(
            control=zeros, treatment=treatment, clusters=triplet_ids, seed=99
        )
        # "Pooled over files": every item is its own cluster, which is exactly
        # what an item-level (ordinary) bootstrap does.
        item_level_clusters = list(range(len(diffs)))
        pooled = cluster_bootstrap_diff(
            control=zeros, treatment=treatment, clusters=item_level_clusters, seed=99
        )

        clustered_width = clustered.ci_high - clustered.ci_low
        pooled_width = pooled.ci_high - pooled.ci_low

        # Point estimates agree (same data, same mean); only the interval,
        # which is what clustering actually changes, differs.
        assert clustered.point_estimate == pytest.approx(pooled.point_estimate)
        assert clustered.n_clusters == n_triplets
        assert pooled.n_clusters == len(diffs)
        assert clustered_width > pooled_width * 1.3, (
            f"clustering on the triplet ({clustered_width:.4f}) did not read materially "
            f"wider than pooling over items ({pooled_width:.4f}); clustering would be "
            "doing nothing"
        )

    def test_compute_phase0_result_clusters_on_triplet_not_on_event(self) -> None:
        """`Phase0Result.n_clusters` must equal the triplet count, not the
        event count -- the public entry point never exposes an item-level
        clustering option, which is what stops a caller from pooling by
        accident.
        """
        events = _events(n_triplets=20, seed=3)
        battery = _passed_battery()
        result = _v1(events, battery, seed=5)

        assert result.n_clusters == 20
        assert result.n_sensitivity_events == 40
        assert result.n_specificity_events == 40


# --------------------------------------------------------------------------- #
# 3. The falsifier battery: known-good passes, known-bad refuses
# --------------------------------------------------------------------------- #


class TestFalsifierBattery:
    def test_known_good_extractor_passes_and_unlocks_a_result(self) -> None:
        """Standing rule 2: a falsifier must pass a known-good case before it
        may fail anything. Here the "known-good case" is an extractor that
        correctly reads two planted triplets -- obvious movement on governing,
        no movement on matched -- and the battery must score 1.0/1.0 and let
        `compute_phase0_result` proceed.
        """
        battery = _passed_battery()
        assert battery.passed
        assert battery.sensitivity == 1.0
        assert battery.specificity == 1.0
        assert battery.n_cases == 2

        events = _events(seed=4)
        result = _v1(events, battery, seed=1)
        assert result.j == pytest.approx(result.sensitivity + result.specificity - 1.0)

    def test_known_bad_extractor_fails_the_battery_and_no_j_is_reported(self) -> None:
        """A planted case where the extractor cannot see the governing
        movement it obviously should (q_governing left at q_base) fails
        sensitivity, and `compute_phase0_result` must refuse outright -- not
        emit a J with a caveat attached.
        """
        cases = [
            FalsifierCase(
                name="obvious-move-but-extractor-blind",
                q_base=10.0,
                q_governing=10.001,  # should have moved to ~100; extractor missed it
                q_matched=10.02,
                expect_governing_change=True,
                expect_matched_change=False,
            ),
            FalsifierCase(
                name="obvious-still",
                q_base=20.0,
                q_governing=90.0,
                q_matched=20.02,
                expect_governing_change=True,
                expect_matched_change=False,
            ),
        ]
        battery = run_falsifier_battery(cases, THRESHOLD)

        assert not battery.passed
        assert battery.sensitivity == pytest.approx(0.5)
        assert battery.specificity == 1.0

        events = _events(seed=5)
        with pytest.raises(FalsifierBatteryFailedError, match="extractor is the finding"):
            _v1(events, battery, seed=1)

    def test_known_bad_extractor_that_sees_movement_everywhere_fails_specificity(self) -> None:
        """The mirror-image known-bad case: an extractor that calls movement on
        the matched (non-governing) contrast it should have held still on.
        Specificity fails even though sensitivity is perfect, and the gate
        still refuses -- either half failing is enough.
        """
        cases = [
            FalsifierCase(
                name="obvious-move",
                q_base=10.0,
                q_governing=100.0,
                q_matched=95.0,  # matched should not have moved; extractor says it did
                expect_governing_change=True,
                expect_matched_change=False,
            ),
        ]
        battery = run_falsifier_battery(cases, THRESHOLD)

        assert not battery.passed
        assert battery.sensitivity == 1.0
        assert battery.specificity == 0.0

        with pytest.raises(FalsifierBatteryFailedError):
            _v1(_events(seed=6), battery, seed=1)

    def test_run_falsifier_battery_refuses_empty_cases(self) -> None:
        with pytest.raises(ValueError, match="at least one planted case"):
            run_falsifier_battery([], THRESHOLD)


# --------------------------------------------------------------------------- #
# 4. The movement threshold is derived from, and only from, base-arm records
# --------------------------------------------------------------------------- #


class TestThresholdDerivation:
    def test_base_repeat_pair_carries_no_governing_or_matched_field(self) -> None:
        """The type itself is the enforcement: there is no field on
        `BaseRepeatPair` a caller could accidentally fill with a
        governing/matched-arm quantity.
        """
        field_names = {f.name for f in dataclasses.fields(BaseRepeatPair)}
        assert field_names == {"triplet_id", "q_repeat0", "q_repeat1"}

    def test_threshold_is_the_max_relative_base_vs_base_difference(self) -> None:
        pairs = [
            BaseRepeatPair(triplet_id="t00", q_repeat0=10.0, q_repeat1=10.5),  # 0.05
            BaseRepeatPair(triplet_id="t01", q_repeat0=20.0, q_repeat1=20.2),  # 0.01
            BaseRepeatPair(triplet_id="t02", q_repeat0=5.0, q_repeat1=6.0),  # 0.20 <- max
        ]
        threshold = derive_movement_threshold(pairs)
        assert threshold.value == pytest.approx(0.20)
        assert threshold.max_triplet_id == "t02"
        assert threshold.n_base_pairs == 3

    def test_threshold_derivation_reads_only_the_base_arm_even_when_other_arms_are_present(
        self,
    ) -> None:
        """Simulates the real pipeline: a pool of raw extraction rows tagged by
        arm ("base" / "governing" / "matched"). A loader filters to "base" and
        pairs repeat 0 against repeat 1 per triplet -- exactly what
        `scripts/score_track_h.py`'s `load_base_pairs` does. Planting an
        extreme governing/matched value in the same pool must not move the
        derived threshold at all, because those rows are never turned into a
        `BaseRepeatPair` in the first place.
        """
        raw_records = [
            {"triplet_id": "t00", "arm": "base", "repeat": 0, "quantity": 10.0},
            {"triplet_id": "t00", "arm": "base", "repeat": 1, "quantity": 10.4},  # 0.04
            {"triplet_id": "t01", "arm": "base", "repeat": 0, "quantity": 8.0},
            {"triplet_id": "t01", "arm": "base", "repeat": 1, "quantity": 8.2},  # 0.025
            # Planted decoys: if these ever leaked into the derivation the
            # threshold would jump to ~9.0 (900% relative movement).
            {"triplet_id": "t00", "arm": "governing", "repeat": 0, "quantity": 100.0},
            {"triplet_id": "t01", "arm": "matched", "repeat": 1, "quantity": 0.5},
        ]

        def base_pairs_from(records: list[dict]) -> list[BaseRepeatPair]:
            by_triplet: dict[str, dict[int, float]] = {}
            for row in records:
                if row["arm"] != "base":
                    continue
                by_triplet.setdefault(row["triplet_id"], {})[row["repeat"]] = row["quantity"]
            return [
                BaseRepeatPair(triplet_id=tid, q_repeat0=reps[0], q_repeat1=reps[1])
                for tid, reps in sorted(by_triplet.items())
            ]

        pairs = base_pairs_from(raw_records)
        threshold = derive_movement_threshold(pairs)

        assert threshold.value == pytest.approx(0.04)
        assert threshold.max_triplet_id == "t00"

        # Removing the decoy rows entirely must give the identical threshold --
        # proof that they never contributed.
        base_only = [r for r in raw_records if r["arm"] == "base"]
        threshold_without_decoys = derive_movement_threshold(base_pairs_from(base_only))
        assert threshold_without_decoys.value == threshold.value
        assert threshold_without_decoys.max_triplet_id == threshold.max_triplet_id

    def test_derive_movement_threshold_refuses_empty_input(self) -> None:
        with pytest.raises(ValueError, match="at least one base-arm pair"):
            derive_movement_threshold([])


# --------------------------------------------------------------------------- #
# relative_movement / classify_movement: edge cases
# --------------------------------------------------------------------------- #


class TestRelativeMovementAndClassification:
    def test_relative_movement_is_symmetric_in_direction(self) -> None:
        assert relative_movement(10.0, 12.0) == pytest.approx(0.2)
        assert relative_movement(10.0, 8.0) == pytest.approx(0.2)

    def test_relative_movement_refuses_zero_base(self) -> None:
        with pytest.raises(ValueError, match="undefined when the base quantity is zero"):
            relative_movement(0.0, 5.0)

    def test_classify_movement_is_strict_not_at_or_above(self) -> None:
        """A contrast exactly at the threshold has not exceeded pure noise."""
        threshold = MovementThreshold(value=0.10, n_base_pairs=1, max_triplet_id="t00")
        assert classify_movement(10.0, 11.0, threshold) is False  # exactly 0.10
        assert classify_movement(10.0, 11.01, threshold) is True  # just above


# --------------------------------------------------------------------------- #
# Phase0Result.disposition(): every branch, min(sensitivity, specificity)
# --------------------------------------------------------------------------- #


class TestDisposition:
    def test_disposition_reports_min_not_just_j_when_kill_is_asymmetric(self) -> None:
        """(1.00, 0.75) reaches J = 0.75 -- above the kill, exactly like
        (0.85, 0.85) reaching 0.70 would be -- but is not "both arms adequate".
        The disposition must say so in those words. (0.75 rather than the
        registration's exact boundary 0.70 is a test-robustness choice, so the
        assertion is not riding a single floating-point rounding of a literal
        equality; it is comfortably on the kill side either way.)
        """
        events: list[TripletEvent] = []
        for t in range(20):
            triplet_id = f"t{t:02d}"
            for repeat in (0, 1):
                # Governing always moves (sensitivity 1.00).
                q_governing = 100.0
                # Matched moves on exactly 25% of events (specificity 0.75).
                q_matched = 100.0 if (t * 2 + repeat) % 4 == 0 else 10.001
                events.append(
                    TripletEvent(
                        triplet_id=triplet_id,
                        repeat=repeat,
                        q_base=10.0,
                        q_governing=q_governing,
                        q_matched=q_matched,
                    )
                )
        battery = _passed_battery()
        result = _v1(events, battery, seed=1)

        assert result.sensitivity == pytest.approx(1.0)
        assert result.specificity == pytest.approx(0.75)
        assert result.min_sens_spec == pytest.approx(0.75)
        assert result.j >= KILL_THRESHOLD_J
        assert result.kill is True

        text = result.disposition()
        assert "NOT both arms adequate" in text
        assert f"{result.min_sens_spec:.3f}" in text

    def test_disposition_reports_survives_when_j_below_kill(self) -> None:
        events = _events(sensitivity_rate=0.60, specificity_rate=0.55, seed=8)
        battery = _passed_battery()
        result = _v1(events, battery, seed=2)

        assert result.j < KILL_THRESHOLD_J
        assert result.kill is False
        assert "venue survives" in result.disposition()

    def test_disposition_reports_closes_when_both_arms_genuinely_adequate(self) -> None:
        events = []
        for t in range(20):
            for repeat in (0, 1):
                events.append(
                    TripletEvent(
                        triplet_id=f"t{t:02d}",
                        repeat=repeat,
                        q_base=10.0,
                        # Sensitivity 0.90, specificity 0.90: both above 0.85.
                        q_governing=100.0 if (t * 2 + repeat) % 10 < 9 else 10.001,
                        q_matched=10.001 if (t * 2 + repeat) % 10 < 9 else 100.0,
                    )
                )
        battery = _passed_battery()
        result = _v1(events, battery, seed=3)

        assert result.min_sens_spec >= ADEQUACY_CEILING
        assert result.kill is True
        assert "venue closes" in result.disposition()

    def test_compute_phase0_result_refuses_empty_events(self) -> None:
        with pytest.raises(ValueError, match="at least one triplet event"):
            compute_phase0_result([], THRESHOLD, _passed_battery(), base_pairs=_base_pairs())


# --------------------------------------------------------------------------- #
# fleiss_kappa across the three extractors: exists, used, not reimplemented
# --------------------------------------------------------------------------- #


class TestExtractorAgreement:
    def test_extractor_movement_agreement_delegates_to_fleiss_kappa(self) -> None:
        """Same input into the module's wrapper and into the raw
        `decision_evals.stats.agreement.fleiss_kappa` must give the identical
        result -- proof this is a pointer at the existing estimator, not a
        second implementation of chance-corrected agreement.
        """
        ratings: list[list[bool]] = [
            [True, True, True],
            [False, False, False],
            [True, True, False],
            [False, True, False],
            [True, False, False],
            [True, True, True],
            [False, False, True],
            [True, False, True],
        ]
        wrapped = extractor_movement_agreement(ratings)
        direct = fleiss_kappa(ratings)
        assert wrapped == direct


# --------------------------------------------------------------------------- #
# 5. The log movement scale, and the down-arm penalty it removes
# --------------------------------------------------------------------------- #


class TestLogMovement:
    def test_the_log_scale_is_symmetric_where_the_relative_scale_is_not(self) -> None:
        """A doubling and a halving are the same movement, and the relative rule
        says they are not. That asymmetry is a direction penalty dressed as a
        measurement, and removing it is why ``pooled_log_noise_v2`` exists.
        """
        assert relative_movement(10.0, 20.0) == pytest.approx(1.000)
        assert relative_movement(10.0, 5.0) == pytest.approx(0.500)
        assert log_movement(10.0, 20.0) == pytest.approx(log_movement(10.0, 5.0))

    def test_t04_and_t03_on_the_log_scale(self) -> None:
        """The arithmetic behind ``t04``'s blocked-pending-tau record, checked
        rather than asserted in prose. ``datasets/tailoring/index-pass2.yaml``
        blocks ``t04`` at a relative movement of 0.333, the smallest in the set,
        and records that down-arms sit lowest by construction. On the log scale
        6 -> 4 reads 0.405 against ``t03``'s 4 -> 8 at 0.693, so the gap narrows
        from 3.0x to 1.71x. That is the size of the penalty the rule removes.
        """
        t04 = log_movement(6.0, 4.0)
        t03 = log_movement(4.0, 8.0)
        assert t04 == pytest.approx(0.405, abs=5e-4)
        assert t03 == pytest.approx(0.693, abs=5e-4)
        assert t03 / t04 == pytest.approx(1.71, abs=5e-3)

        assert relative_movement(6.0, 4.0) == pytest.approx(1 / 3)
        assert relative_movement(4.0, 8.0) == pytest.approx(1.0)
        assert relative_movement(4.0, 8.0) / relative_movement(6.0, 4.0) == pytest.approx(3.0)

    @pytest.mark.parametrize(
        ("q_base", "q_variant"), [(0.0, 5.0), (5.0, 0.0), (-1.0, 5.0), (5.0, -1.0)]
    )
    def test_log_movement_refuses_a_non_positive_quantity(
        self, q_base: float, q_variant: float
    ) -> None:
        """Stricter than the relative rule's divide-by-zero guard, and it has to
        be: a non-positive elicited quantity has no log.
        """
        with pytest.raises(ValueError, match="two positive quantities"):
            log_movement(q_base, q_variant)


# --------------------------------------------------------------------------- #
# 6. The threshold carries its rule, and the rule is the enforcement
# --------------------------------------------------------------------------- #


def _pooled(k: float = 2.0, n_base_pairs: int = 20, sigma_hat: float = 0.05) -> MovementThreshold:
    return MovementThreshold(
        value=k * sigma_hat,
        n_base_pairs=n_base_pairs,
        rule="pooled_log_noise_v2",
        k=k,
        sigma_hat=sigma_hat,
    )


class TestThresholdRuleInvariants:
    def test_a_v1_threshold_is_refused_by_the_v2_scale_comparison(self) -> None:
        """The point of carrying the rule on the type. A ``max_relative_v1``
        value is a relative excursion; compared against a log movement it would
        still return a boolean, and the boolean would come from a different
        instrument than the one that was derived.
        """
        with pytest.raises(ValueError, match="cannot be compared against a log movement"):
            exceeds_log_threshold(10.0, 20.0, THRESHOLD)

    def test_a_v2_threshold_is_refused_by_the_v1_scale_comparison(self) -> None:
        with pytest.raises(ValueError, match="cannot be compared against a relative movement"):
            exceeds_relative_threshold(10.0, 20.0, _pooled())

    def test_classify_movement_dispatches_on_the_rule(self) -> None:
        """One contrast, two thresholds of identical numeric value, two answers.
        A halving is 0.500 on the relative scale and 0.693 on the log one, so at
        a threshold of 0.6 the dispatch is the whole verdict.
        """
        v1 = MovementThreshold(value=0.6, n_base_pairs=20, max_triplet_id="t00")
        v2 = _pooled(k=1.0, sigma_hat=0.6)
        assert classify_movement(10.0, 5.0, v1) is False
        assert classify_movement(10.0, 5.0, v2) is True

    @pytest.mark.parametrize(
        ("kwargs", "message"),
        [
            ({"value": -0.1, "n_base_pairs": 3, "max_triplet_id": "t00"}, "must be non-negative"),
            ({"value": 0.1, "n_base_pairs": 0, "max_triplet_id": "t00"}, "at least one base pair"),
            ({"value": 0.1, "n_base_pairs": 3}, "must name the triplet"),
            (
                {"value": 0.1, "n_base_pairs": 3, "max_triplet_id": "t00", "k": 2.0},
                "carries no k and no sigma_hat",
            ),
            (
                {"value": 0.1, "n_base_pairs": 3, "max_triplet_id": "t00", "sigma_hat": 0.05},
                "carries no k and no sigma_hat",
            ),
            (
                {"value": 0.1, "n_base_pairs": 3, "rule": "pooled_log_noise_v2", "k": 2.0},
                "must carry both k and sigma_hat",
            ),
            (
                {"value": 0.1, "n_base_pairs": 3, "rule": "pooled_log_noise_v2", "sigma_hat": 0.05},
                "must carry both k and sigma_hat",
            ),
            (
                {
                    "value": 0.1,
                    "n_base_pairs": 3,
                    "rule": "pooled_log_noise_v2",
                    "k": 2.0,
                    "sigma_hat": 0.05,
                    "max_triplet_id": "t00",
                },
                "no single triplet set it",
            ),
        ],
    )
    def test_a_field_set_contradicting_the_rule_is_refused(
        self, kwargs: dict, message: str
    ) -> None:
        with pytest.raises(ValueError, match=message):
            MovementThreshold(**kwargs)


# --------------------------------------------------------------------------- #
# 7. The pooled derivation: fixed in n, RMS about zero, k declared
# --------------------------------------------------------------------------- #


class TestPooledThresholdDerivation:
    def test_sigma_hat_is_the_rms_about_zero_not_the_sd_about_the_mean(self) -> None:
        """Three pairs whose log differences are +0.1, -0.1 and +0.4. Their mean
        is 0.133, so centring on it reports a smaller noise scale than the null
        the design registers, where the mean is known to be zero.
        """
        pairs = [
            BaseRepeatPair(triplet_id="t00", q_repeat0=1.0, q_repeat1=math.exp(0.1)),
            BaseRepeatPair(triplet_id="t01", q_repeat0=1.0, q_repeat1=math.exp(-0.1)),
            BaseRepeatPair(triplet_id="t02", q_repeat0=1.0, q_repeat1=math.exp(0.4)),
        ]
        threshold = derive_movement_threshold_pooled(pairs, k=2.0)

        expected = math.sqrt((0.1**2 + 0.1**2 + 0.4**2) / 3)
        assert threshold.sigma_hat == pytest.approx(expected)
        assert threshold.value == pytest.approx(2.0 * expected)
        assert threshold.rule == "pooled_log_noise_v2"
        assert threshold.k == 2.0
        assert threshold.n_base_pairs == 3
        assert threshold.max_triplet_id is None

        centred = float(np.std([0.1, -0.1, 0.4], ddof=1))
        assert threshold.sigma_hat != pytest.approx(centred)

    def test_the_estimand_moves_with_n_under_the_maximum_and_holds_under_the_rms(self) -> None:
        """The defect the rule change removes, as an estimand rather than a draw.

        Both statistics are averaged over 200 independent log-normal samples at
        each n, because the claim is about ``E[max of n]`` and a single sample is
        one realisation of it. The expected maximum climbs monotonically toward
        ``sup F``, so every row of a power table built on it is a different
        venue. ``E[sigma-hat]`` sits on sigma at every n.
        """
        rng = np.random.default_rng(20260825)
        sigma = 0.05
        sizes = (5, 10, 20, 40, 80)
        mean_max: list[float] = []
        mean_sigma: list[float] = []
        for n in sizes:
            maxima: list[float] = []
            sigmas: list[float] = []
            for _ in range(200):
                pairs = [
                    BaseRepeatPair(
                        triplet_id=f"t{i:03d}",
                        q_repeat0=10.0,
                        q_repeat1=10.0 * math.exp(float(rng.normal(0.0, sigma))),
                    )
                    for i in range(n)
                ]
                maxima.append(derive_movement_threshold(pairs).value)
                sigmas.append(float(derive_movement_threshold_pooled(pairs, k=2.0).sigma_hat or 0))
            mean_max.append(float(np.mean(maxima)))
            mean_sigma.append(float(np.mean(sigmas)))

        assert mean_max == sorted(mean_max), f"the expected maximum did not climb: {mean_max}"
        assert mean_max[-1] > 1.5 * mean_max[0]
        # Sigma-hat estimates a fixed parameter, so its expectation sits on that
        # parameter at every n rather than trending with the corpus size.
        assert all(0.9 * sigma < s < 1.1 * sigma for s in mean_sigma), mean_sigma
        sigma_trend = (max(mean_sigma) - min(mean_sigma)) / sigma
        max_trend = (mean_max[-1] - mean_max[0]) / mean_max[0]
        assert sigma_trend < 0.2 < max_trend

    def test_identical_repeats_give_a_zero_noise_scale_rather_than_a_refusal(self) -> None:
        """Integral elicited quantities tie constantly, and a bootstrap replicate
        that happens to draw only tied pairs must not take the whole run down.
        The fitted model then says the instrument produced no excursion at all,
        so any movement whatever exceeds the threshold.
        """
        pairs = [
            BaseRepeatPair(triplet_id=f"t{i:02d}", q_repeat0=6.0, q_repeat1=6.0) for i in range(3)
        ]
        threshold = derive_movement_threshold_pooled(pairs, k=2.0)
        assert threshold.value == 0.0
        assert classify_movement(6.0, 6.0, threshold) is False
        assert classify_movement(6.0, 6.001, threshold) is True

    def test_pooled_derivation_refuses_empty_input(self) -> None:
        with pytest.raises(ValueError, match="at least one base-arm pair"):
            derive_movement_threshold_pooled([], k=2.0)

    @pytest.mark.parametrize("k", [0.0, -1.0, math.nan, math.inf])
    def test_pooled_derivation_refuses_a_k_that_is_not_a_positive_multiple(self, k: float) -> None:
        pairs = [BaseRepeatPair(triplet_id="t00", q_repeat0=10.0, q_repeat1=10.5)]
        with pytest.raises(ValueError, match="finite positive multiple"):
            derive_movement_threshold_pooled(pairs, k=k)

    def test_pooled_derivation_refuses_a_non_positive_base_quantity(self) -> None:
        pairs = [BaseRepeatPair(triplet_id="t00", q_repeat0=0.0, q_repeat1=10.5)]
        with pytest.raises(ValueError, match="two positive quantities"):
            derive_movement_threshold_pooled(pairs, k=2.0)


# --------------------------------------------------------------------------- #
# 8. The specificity ceiling, and the inert-instrument signature
# --------------------------------------------------------------------------- #


class TestSpecificityCeiling:
    def test_the_v2_ceiling_is_a_function_of_k_alone(self) -> None:
        """sigma cancels, leaving ``2*Phi(k) - 1``. That is why k is swept rather
        than argued: it fixes how much of J the specificity arm can contribute
        before any data is seen.
        """
        assert specificity_ceiling(_pooled(k=1.0, sigma_hat=0.01)) == pytest.approx(
            0.6827, abs=1e-4
        )
        assert specificity_ceiling(_pooled(k=2.0, sigma_hat=0.01)) == pytest.approx(
            0.9545, abs=1e-4
        )
        assert specificity_ceiling(_pooled(k=3.0, sigma_hat=0.01)) == pytest.approx(
            0.9973, abs=1e-4
        )
        assert specificity_ceiling(_pooled(k=2.0, sigma_hat=0.01)) == specificity_ceiling(
            _pooled(k=2.0, sigma_hat=5.0)
        )

    def test_the_v1_ceiling_climbs_toward_one_with_the_corpus_size(self) -> None:
        """``tau`` is the maximum of n null excursions, so a fresh one exceeds it
        with probability ``1/(n+1)``. Adding triplets drives the false-movement
        rate toward zero, pins specificity near 1, and leaves J reading as
        sensitivity. The drift, stated as a number.
        """
        ceilings = [
            specificity_ceiling(MovementThreshold(value=0.1, n_base_pairs=n, max_triplet_id="t00"))
            for n in (5, 10, 20, 40)
        ]
        assert ceilings == pytest.approx([5 / 6, 10 / 11, 20 / 21, 40 / 41])
        assert ceilings == sorted(ceilings)
        assert ceilings[-1] > 0.97

    def test_a_specificity_at_its_ceiling_is_reported_as_inert(self) -> None:
        """Perfect specificity under ``max_relative_v1`` at 20 base pairs sits
        above the 0.952 ceiling, so J is reading as sensitivity alone and the
        disposition says so.
        """
        events = [
            TripletEvent(
                triplet_id=f"t{t:02d}", repeat=r, q_base=10.0, q_governing=100.0, q_matched=10.001
            )
            for t in range(20)
            for r in (0, 1)
        ]
        result = _v1(events, _passed_battery(), seed=4)

        assert result.specificity == pytest.approx(1.0)
        assert result.specificity_ceiling == pytest.approx(20 / 21)
        assert result.specificity_is_inert is True
        text = result.disposition()
        assert "structural ceiling 0.952" in text
        assert "reading as sensitivity alone" in text

    def test_a_specificity_below_its_ceiling_carries_no_inert_line(self) -> None:
        result = _v1(_events(seed=8), _passed_battery(), seed=4)
        assert result.specificity_is_inert is False
        assert "reading as sensitivity alone" not in result.disposition()


# --------------------------------------------------------------------------- #
# 9. Recomputing the threshold inside the bootstrap
# --------------------------------------------------------------------------- #


def _log_events(n_triplets: int = 20, *, seed: int = 0) -> list[TripletEvent]:
    """Events from a log-normal generator: base noise at 0.05, governing shifted."""
    rng = np.random.default_rng(seed)
    events: list[TripletEvent] = []
    for t in range(n_triplets):
        for repeat in (0, 1):
            events.append(
                TripletEvent(
                    triplet_id=f"t{t:02d}",
                    repeat=repeat,
                    q_base=10.0,
                    q_governing=10.0 * math.exp(0.6 + float(rng.normal(0.0, 0.05))),
                    q_matched=10.0 * math.exp(float(rng.normal(0.0, 0.05))),
                )
            )
    return events


class TestRecomputedThreshold:
    def test_the_v2_path_reports_the_threshold_it_scored_at(self) -> None:
        """The reported threshold is the full-sample refit, so the number printed
        beside J is the number J was computed at.
        """
        events = _log_events(seed=1)
        pairs = _base_pairs()
        passed_in = derive_movement_threshold_pooled(pairs, k=2.0)
        result = compute_phase0_result(
            events, passed_in, _passed_battery(), base_pairs=pairs, seed=3, n_resamples=400
        )

        assert result.rule == "pooled_log_noise_v2"
        assert result.threshold.value == pytest.approx(passed_in.value)
        assert result.threshold.k == 2.0
        assert result.j == pytest.approx(result.sensitivity + result.specificity - 1.0, abs=1e-12)
        assert result.specificity_ceiling == pytest.approx(0.9545, abs=1e-4)

    def test_recomputing_widens_the_interval_a_fixed_threshold_understates(self) -> None:
        """Defect B, measured. A plug-in threshold held fixed across replicates
        treats a random quantity as known, which the notebook records as a
        realised SD of 1.23x to 2.31x the closed form at coverage 0.61 to 0.85
        against a nominal 0.95. Refitting inside the replicate puts the variation
        back, and the wider standard error is what that looks like.
        """
        events = _log_events(n_triplets=20, seed=5)
        pairs = _base_pairs()
        threshold = derive_movement_threshold_pooled(pairs, k=1.0)

        refit = compute_phase0_result(
            events,
            threshold,
            _passed_battery(),
            base_pairs=pairs,
            recompute_threshold=True,
            seed=11,
            n_resamples=2000,
        )
        fixed = compute_phase0_result(
            events,
            threshold,
            _passed_battery(),
            base_pairs=pairs,
            recompute_threshold=False,
            seed=11,
            n_resamples=2000,
        )

        assert refit.j == pytest.approx(fixed.j)
        assert refit.standard_error > fixed.standard_error

    def test_a_v1_threshold_cannot_be_recomputed_inside_the_bootstrap(self) -> None:
        """A maximum is not Hadamard-differentiable, so its bootstrap is
        inconsistent at every sample size. Recomputing is the default, so the v1
        path is reachable only by asking for the fixed threshold in so many
        words.
        """
        with pytest.raises(ValueError, match="not Hadamard-differentiable"):
            compute_phase0_result(
                _events(seed=1),
                THRESHOLD,
                _passed_battery(),
                base_pairs=_base_pairs(),
                recompute_threshold=True,
            )

    def test_sigma_hat_is_weighted_by_triplet_even_when_repeats_are_uneven(self) -> None:
        """One triplet with three repeats against one with a single repeat.
        Weighting sigma-hat by event would let the busy triplet count three
        times; the definition is over base *pairs*, one per triplet.
        """
        events = [
            TripletEvent(triplet_id="t00", repeat=r, q_base=10.0, q_governing=30.0, q_matched=10.01)
            for r in (0, 1, 2)
        ] + [
            TripletEvent(triplet_id="t01", repeat=0, q_base=10.0, q_governing=30.0, q_matched=10.01)
        ]
        pairs = [
            BaseRepeatPair(triplet_id="t00", q_repeat0=1.0, q_repeat1=math.exp(0.02)),
            BaseRepeatPair(triplet_id="t01", q_repeat0=1.0, q_repeat1=math.exp(0.40)),
        ]
        threshold = derive_movement_threshold_pooled(pairs, k=1.0)
        result = compute_phase0_result(
            events, threshold, _passed_battery(), base_pairs=pairs, seed=2, n_resamples=200
        )

        assert result.threshold.sigma_hat == pytest.approx(math.sqrt((0.02**2 + 0.40**2) / 2))
        assert result.n_clusters == 2
        assert result.n_sensitivity_events == 4


# --------------------------------------------------------------------------- #
# 10. Unscorable events, and the base pairs the corpus must match
# --------------------------------------------------------------------------- #


class TestDroppedEventsAndBasePairs:
    def test_an_unscorable_event_is_dropped_from_both_arms_and_counted(self) -> None:
        """A non-positive quantity has no log, so the event leaves both arms
        together. Keeping its partner contrast would give the two arms different
        denominators, and J is a paired difference over the same items.
        """
        events = _log_events(n_triplets=5, seed=2)
        events[0] = dataclasses.replace(events[0], q_governing=0.0)
        pairs = _base_pairs(5)
        threshold = derive_movement_threshold_pooled(pairs, k=2.0)
        result = compute_phase0_result(
            events, threshold, _passed_battery(), base_pairs=pairs, seed=1, n_resamples=200
        )

        assert result.n_dropped_events == 1
        assert result.n_sensitivity_events == 9
        assert result.n_specificity_events == 9
        assert "1 events dropped as unscorable" in result.disposition()

    def test_a_zero_base_quantity_is_dropped_on_the_relative_scale_too(self) -> None:
        events = _events(n_triplets=5, seed=3)
        events[0] = dataclasses.replace(events[0], q_base=0.0)
        result = compute_phase0_result(
            events,
            THRESHOLD,
            _passed_battery(),
            base_pairs=_base_pairs(5),
            recompute_threshold=False,
            seed=1,
            n_resamples=200,
        )
        assert result.n_dropped_events == 1
        assert result.n_sensitivity_events == 9

    def test_all_events_unscorable_is_a_refusal_not_a_zero(self) -> None:
        events = [dataclasses.replace(e, q_matched=0.0) for e in _log_events(n_triplets=3, seed=4)]
        pairs = _base_pairs(3)
        threshold = derive_movement_threshold_pooled(pairs, k=2.0)
        with pytest.raises(ValueError, match="the extraction is the finding"):
            compute_phase0_result(events, threshold, _passed_battery(), base_pairs=pairs)

    def test_compute_phase0_result_refuses_empty_base_pairs(self) -> None:
        with pytest.raises(ValueError, match="needs the base-arm pairs"):
            compute_phase0_result(_events(seed=1), THRESHOLD, _passed_battery(), base_pairs=[])

    def test_a_duplicated_triplet_in_base_pairs_is_refused(self) -> None:
        pairs = [*_base_pairs(20), _base_pairs(1)[0]]
        with pytest.raises(ValueError, match="t00 appears twice"):
            compute_phase0_result(
                _events(seed=1),
                THRESHOLD,
                _passed_battery(),
                base_pairs=pairs,
                recompute_threshold=False,
            )

    def test_an_event_with_no_base_pair_is_refused(self) -> None:
        """The threshold and the events have to be the same corpus. The refusal
        fires on the fixed-threshold path too: a threshold derived elsewhere is
        wrong whether or not it is about to be refitted.
        """
        with pytest.raises(ValueError, match="no base pair for t18, t19"):
            compute_phase0_result(
                _events(seed=1),
                THRESHOLD,
                _passed_battery(),
                base_pairs=_base_pairs(18),
                recompute_threshold=False,
            )
