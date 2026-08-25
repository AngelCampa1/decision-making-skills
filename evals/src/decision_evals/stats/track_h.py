"""Track H Phase 0 scoring: the movement threshold, the falsifier gate, and J.

This module scores Phase 0 (H1) once a corpus and its extractions exist. It
does not author items and it does not call a model — see
``notebook/2026-08-19-prediction-track-h-phase-0.md`` for what Phase 0 is and
``docs/RESEARCH_PROGRAMME.md``'s H1 subsection for why it runs before Track H's
sub-agent tracks (C through F). Everything here is pure arithmetic over
extracted quantities the runner produces.

**The primary is Youden's J, and it is identically the programme's ``d``.**
``J = sensitivity + specificity − 1`` expands to
``P(change | governing) − P(change | matched)`` (the identity is asserted
numerically in ``tests/unit/test_track_h.py``), so there is one estimator, not
two, and it is a *paired* mean difference of two indicator vectors sharing an
item order. That is exactly the shape
:func:`decision_evals.stats.cluster.cluster_bootstrap_diff` takes, with
``control`` the matched-arm change indicators, ``treatment`` the governing-arm
change indicators, and ``clusters`` the triplet id — never the file, never the
response. Defect nine on ``docs/STATUS.md``'s broken-measurement list is a
pooled statistic used on a matched corpus, ranking positives against negatives
drawn from *other* triples and structurally blind to the rank held inside one;
Track H is a matched design of exactly that shape, so this module never offers
a code path that pools over files.

**The movement threshold is derived, not chosen.** Turning a continuous
elicited quantity into `change` / `no change` needs a threshold, and no number
for one exists anywhere in this repository — standing rule 1 forbids inventing
one. Every function here that classifies movement requires a
:class:`MovementThreshold` rather than a bare ``float``, so a threshold cannot
enter a governing/matched contrast except by having been derived from the base
arm first. The type is the enforcement, and it carries which *rule* derived it
so that a threshold cannot be scored against the wrong scale either.

**Two derivations exist, and the second replaced the first.** Nothing is
deleted for having been wrong, so both stay callable and one checkpoint can be
scored both ways.

``max_relative_v1`` is the original registration: relative movement,
``|q_variant − q_base| / |q_base|``, thresholded at the *maximum* of the 20
base-arm repeat-0 vs repeat-1 excursions.
``notebook/2026-08-19-h1-does-not-need-twenty-and-tau-drifts-with-n.md`` records
two defects in it. The maximum of ``n`` draws converges to ``sup F`` rather than
to any fixed functional, so the estimand moves with the corpus size and true J
was reconstructed at 0.843, 0.915, 0.956 and 0.977 as n went 5, 10, 20, 40 —
no two rows of a power table are the same venue. And the threshold is a plug-in
nuisance parameter held fixed across bootstrap replicates, which measured a
realised SD of 1.23 to 2.31 times the closed form at coverage 0.61 to 0.85
against a nominal 0.95. :func:`derive_movement_threshold` computes it.

``pooled_log_noise_v2`` is the rule that replaced it, and it is three changes
that only work together. Movement is measured on the **log** scale,
``|log q_variant − log q_base|``, because the relative rule is asymmetric in
direction: a doubling scores 1.000 and a halving 0.500, so down-arms sit lowest
by construction and ``t04`` in ``datasets/tailoring/index-pass2.yaml`` is
blocked at 0.333 for being one. The threshold is ``k · σ̂`` where ``σ̂`` is the
RMS of the base-arm log differences about zero, a fixed population parameter
estimated √n-consistently, so ``τ̂`` stabilises rather than climbing. And ``σ̂``
is smooth where a maximum is not, which is what makes recomputing the threshold
inside every bootstrap replicate valid rather than merely better.
:func:`derive_movement_threshold_pooled` computes it, and ``k`` is a declared
choice swept rather than argued — see :func:`specificity_ceiling` for the trap
that makes sweeping it necessary.

**No J is reported before the falsifier battery passes.** Standing rule 2: a
falsifier must be run against a known-good case before it may fail anything.
Two falsifiers in this repository's history were wrong the day they were
written and would have killed healthy venues, so :func:`compute_phase0_result`
*requires* a passed :class:`FalsifierBatteryResult` as an argument and raises
:class:`FalsifierBatteryFailedError` — not a caveat, no number — when it has
not passed. ``min(sensitivity, specificity)`` is carried on every
:class:`Phase0Result` and its :meth:`~Phase0Result.disposition` never reports
``J`` alone: ``J >= 0.70`` is *implied by* both arms at 0.85 but is not
equivalent to it, since J is a difference and ``(1.00, 0.70)`` reaches 0.70
too.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Final, Literal, cast

import numpy as np
import numpy.typing as npt

from decision_evals.stats.agreement import FleissKappaResult, fleiss_kappa
from decision_evals.stats.cluster import cluster_bootstrap_statistic

#: Which derivation produced a :class:`MovementThreshold`, and therefore which
#: scale a contrast must be measured on before it is compared against one.
MovementRule = Literal["max_relative_v1", "pooled_log_noise_v2"]

#: Pre-registered kill: unaided J at or above this closes the venue. Reached at
#: sensitivity 0.85 and specificity 0.85 — 0.85 is ``ADMISSIBILITY_CEILING`` in
#: ``scripts/probe_casefile.py``, this repository's one already-registered
#: adequacy constant. See the H1 prediction entry for the full arithmetic.
KILL_THRESHOLD_J: Final = 0.70

#: The adequacy level the kill's arithmetic is anchored to. J >= KILL_THRESHOLD_J
#: is implied by both arms reaching this but is not equivalent to it — a
#: disposition below this on either arm must say so explicitly rather than
#: report "both arms adequate".
ADEQUACY_CEILING: Final = 0.85


class FalsifierBatteryFailedError(RuntimeError):
    """No J may be reported: the falsifier battery has not passed.

    Standing rule 2 exists because two falsifiers in this repository were wrong
    the day they were written and would have killed a healthy venue. This is
    the refusal that makes the rule load-bearing rather than a comment: there is
    no code path in this module that reaches :class:`Phase0Result` without a
    :class:`FalsifierBatteryResult` whose :attr:`~FalsifierBatteryResult.passed`
    is ``True``.
    """


@dataclass(frozen=True, slots=True)
class BaseRepeatPair:
    """One triplet's repeat-0 vs repeat-1 elicited quantity, base file only.

    Deliberately carries no governing or matched quantity — there is nothing in
    this type for a caller to pass by mistake. That is what makes
    :func:`derive_movement_threshold`'s "reads only the base arm" property a
    fact about the API rather than a convention someone has to remember.

    Attributes:
        triplet_id: The triplet identifier. The cluster label everywhere else
            in this module.
        q_repeat0: The extracted quantity from the base file's first repeat.
        q_repeat1: The extracted quantity from the base file's second repeat,
            same file, same prompt, nothing perturbed.
    """

    triplet_id: str
    q_repeat0: float
    q_repeat1: float


@dataclass(frozen=True, slots=True)
class MovementThreshold:
    """A derived movement threshold, with the arithmetic that produced it.

    Constructed only by :func:`derive_movement_threshold` or
    :func:`derive_movement_threshold_pooled`. Every function here that turns a
    quantity pair into a change/no-change call takes one of these rather than a
    bare ``float``, so a threshold cannot be invented at a call site — it can
    only be carried forward from a derivation.

    :attr:`rule` carries the scale the threshold lives on, and the constructor
    refuses a field set that contradicts it. A ``max_relative_v1`` threshold
    holds a ``max_triplet_id`` and no ``k``; a ``pooled_log_noise_v2`` threshold
    holds ``k`` and ``sigma_hat`` and no ``max_triplet_id``. That is what stops
    a log-scale threshold being compared against a relative-scale movement,
    where the two numbers are both plausible and mean different things.

    Attributes:
        value: The threshold itself, on :attr:`rule`'s scale. A contrast counts
            as movement only when it *exceeds* this, not when it equals it.
        n_base_pairs: How many base repeat-0/repeat-1 pairs contributed. Equals
            the triplet count (20 in Phase 0).
        rule: Which derivation produced it, and therefore which scale a contrast
            must be measured on before being compared against it.
        max_triplet_id: ``max_relative_v1`` only. Which triplet set the bound,
            so a surprising threshold traces to one item rather than reading as
            an aggregate fact.
        k: ``pooled_log_noise_v2`` only. The declared multiple of the fitted
            noise scale. See :func:`specificity_ceiling`.
        sigma_hat: ``pooled_log_noise_v2`` only. The fitted noise scale itself,
            so ``value`` can be read back as ``k · σ̂`` rather than as a bare
            number.

    Raises:
        ValueError: On a negative ``value``, ``n_base_pairs < 1``, or a field
            set that contradicts ``rule``.
    """

    value: float
    n_base_pairs: int
    rule: MovementRule = "max_relative_v1"
    max_triplet_id: str | None = None
    k: float | None = None
    sigma_hat: float | None = None

    def __post_init__(self) -> None:
        if self.value < 0.0:
            raise ValueError(f"a movement threshold must be non-negative, got {self.value!r}")
        if self.n_base_pairs < 1:
            raise ValueError(
                f"a movement threshold needs at least one base pair, got {self.n_base_pairs!r}"
            )
        if self.rule == "max_relative_v1":
            if self.max_triplet_id is None:
                raise ValueError("a max_relative_v1 threshold must name the triplet that set it")
            if self.k is not None or self.sigma_hat is not None:
                raise ValueError(
                    "a max_relative_v1 threshold carries no k and no sigma_hat: it is a maximum "
                    "over observed excursions, not a multiple of a fitted noise scale"
                )
        elif self.k is None or self.sigma_hat is None:
            raise ValueError("a pooled_log_noise_v2 threshold must carry both k and sigma_hat")
        elif self.max_triplet_id is not None:
            raise ValueError(
                "a pooled_log_noise_v2 threshold is pooled over every base pair, so no single "
                "triplet set it"
            )


def relative_movement(q_base: float, q_variant: float) -> float:
    """``|q_variant - q_base| / |q_base|``. The ``max_relative_v1`` scale.

    Asymmetric in direction, which is the defect ``pooled_log_noise_v2`` was
    written to remove: a doubling scores 1.000 and a halving 0.500.

    Raises:
        ValueError: ``q_base`` is zero, where relative movement is undefined
            rather than infinite or zero. This is an implementation decision,
            not a registered parameter: the registration states the rule but
            does not anticipate a zero base quantity, and returning a
            placeholder here would silently manufacture a movement verdict the
            instrument never produced.
    """
    if q_base == 0.0:
        raise ValueError(
            "relative movement is undefined when the base quantity is zero "
            f"(q_variant={q_variant!r})"
        )
    return abs(q_variant - q_base) / abs(q_base)


def log_movement(q_base: float, q_variant: float) -> float:
    """``|log q_variant - log q_base|``. The ``pooled_log_noise_v2`` scale.

    Symmetric in direction, which is the whole reason it replaced
    :func:`relative_movement`: a doubling and a halving both score 0.693, so a
    down-arm is no longer penalised for being one. On ``t04``'s 6 → 4 this reads
    0.405 against ``t03``'s 4 → 8 at 0.693, a gap of 1.71× where the relative
    scale put the same two items 3.0× apart.

    Raises:
        ValueError: Either quantity is zero or negative. Stricter than
            :func:`relative_movement`'s divide-by-zero guard, and it has to be:
            a log-scale movement needs both quantities on the log scale, and a
            non-positive elicited quantity is a broken extraction rather than a
            small one.
    """
    if q_base <= 0.0 or q_variant <= 0.0:
        raise ValueError(
            "log movement needs two positive quantities, got "
            f"q_base={q_base!r}, q_variant={q_variant!r}"
        )
    return abs(math.log(q_variant) - math.log(q_base))


def derive_movement_threshold(base_pairs: Sequence[BaseRepeatPair]) -> MovementThreshold:
    """``max_relative_v1``: the maximum base-vs-base relative difference.

    The original registered rule, kept callable so a checkpoint can be scored
    under it and against ``pooled_log_noise_v2`` in the same reading. Its two
    defects are in the module docstring; :func:`derive_movement_threshold_pooled`
    is the rule that replaced it.

    Must be called, and its result carried forward, before any governing or
    matched contrast is examined — :class:`MovementThreshold` is the only way
    :func:`classify_movement` accepts a threshold, so that ordering is a type
    error to violate rather than a discipline to remember.

    Args:
        base_pairs: One :class:`BaseRepeatPair` per triplet, base-arm only.

    Returns:
        The derived :class:`MovementThreshold`, with ``rule="max_relative_v1"``.

    Raises:
        ValueError: ``base_pairs`` is empty, or via :func:`relative_movement`.
    """
    if not base_pairs:
        raise ValueError("derive_movement_threshold needs at least one base-arm pair")
    diffs = [
        (pair.triplet_id, relative_movement(pair.q_repeat0, pair.q_repeat1)) for pair in base_pairs
    ]
    max_triplet_id, max_value = max(diffs, key=lambda item: item[1])
    return MovementThreshold(
        value=max_value,
        n_base_pairs=len(base_pairs),
        rule="max_relative_v1",
        max_triplet_id=max_triplet_id,
    )


def derive_movement_threshold_pooled(
    base_pairs: Sequence[BaseRepeatPair], *, k: float
) -> MovementThreshold:
    """``pooled_log_noise_v2``: ``τ = k · σ̂`` over the base-arm log differences.

    ``σ̂ = sqrt( (1/n) Σᵢ (log q₁ᵢ − log q₀ᵢ)² )``. **RMS about zero, not SD
    about the mean.** Under the null nothing was perturbed, so the mean is known
    to be zero; centring would discard a degree of freedom to estimate a drift
    the design says does not exist.

    ``σ`` is a population parameter and ``σ̂`` is √n-consistent, so unlike the
    maximum this estimand does not move with the corpus size. It is also smooth,
    which is the precondition that lets :func:`compute_phase0_result` recompute
    it inside every bootstrap replicate.

    ``σ̂ = 0`` is returned rather than refused. It means every base pair
    reproduced its own quantity exactly, which on integral elicited quantities
    (months, weeks, days) is an ordinary outcome and a common one inside a
    bootstrap replicate. The fitted model then says the instrument produced no
    excursion at all, ``τ`` is zero, and any movement whatever exceeds it.

    Args:
        base_pairs: One :class:`BaseRepeatPair` per triplet, base-arm only.
        k: The declared multiple of the fitted noise scale. Keyword-only and
            without a default: no value for it has been derived anywhere in this
            repository, so a call site states one or does not run.

    Returns:
        The derived :class:`MovementThreshold`, with
        ``rule="pooled_log_noise_v2"``.

    Raises:
        ValueError: ``base_pairs`` is empty, ``k`` is not finite and positive,
            or via :func:`log_movement`.
    """
    if not base_pairs:
        raise ValueError("derive_movement_threshold_pooled needs at least one base-arm pair")
    if not math.isfinite(k) or k <= 0.0:
        raise ValueError(f"k must be a finite positive multiple of the noise scale, got {k!r}")
    squares = [log_movement(pair.q_repeat0, pair.q_repeat1) ** 2 for pair in base_pairs]
    sigma_hat = math.sqrt(sum(squares) / len(squares))
    return MovementThreshold(
        value=k * sigma_hat,
        n_base_pairs=len(base_pairs),
        rule="pooled_log_noise_v2",
        k=k,
        sigma_hat=sigma_hat,
    )


def exceeds_relative_threshold(
    q_base: float, q_variant: float, threshold: MovementThreshold
) -> bool:
    """Compare a contrast against a ``max_relative_v1`` threshold, or refuse.

    Raises:
        ValueError: ``threshold`` was derived under another rule. Its ``value``
            lives on the log scale, where it would still compare against a
            relative movement and still return a boolean, which is the failure
            this refusal exists to make impossible.
    """
    if threshold.rule != "max_relative_v1":
        raise ValueError(
            f"a {threshold.rule} threshold lives on the log scale and cannot be compared "
            "against a relative movement"
        )
    return relative_movement(q_base, q_variant) > threshold.value


def exceeds_log_threshold(q_base: float, q_variant: float, threshold: MovementThreshold) -> bool:
    """Compare a contrast against a ``pooled_log_noise_v2`` threshold, or refuse.

    Raises:
        ValueError: ``threshold`` was derived under another rule. A
            ``max_relative_v1`` value is a relative excursion, so comparing it
            against a log movement silently rescales the instrument.
    """
    if threshold.rule != "pooled_log_noise_v2":
        raise ValueError(
            f"a {threshold.rule} threshold lives on the relative scale and cannot be compared "
            "against a log movement"
        )
    return log_movement(q_base, q_variant) > threshold.value


def classify_movement(q_base: float, q_variant: float, threshold: MovementThreshold) -> bool:
    """Whether a contrast counts as movement: strictly exceeding the threshold.

    Dispatches on ``threshold.rule``, so a contrast is always measured on the
    scale its threshold was derived on. This is the call site everything else
    here uses; :func:`exceeds_relative_threshold` and
    :func:`exceeds_log_threshold` are the two scales it dispatches to, and they
    refuse a threshold belonging to the other one.

    Args:
        q_base: The base file's elicited quantity.
        q_variant: The governing- or matched-arm elicited quantity.
        threshold: A :class:`MovementThreshold` from either derivation.

    Returns:
        ``True`` iff the movement on ``threshold``'s own scale exceeds
        ``threshold.value``. Strict, not ``>=``: under ``max_relative_v1`` the
        threshold *is* the largest excursion the instrument produced with
        nothing perturbed, and under ``pooled_log_noise_v2`` a ``σ̂`` of zero
        would otherwise call every identical repeat a movement.
    """
    if threshold.rule == "max_relative_v1":
        return exceeds_relative_threshold(q_base, q_variant, threshold)
    return exceeds_log_threshold(q_base, q_variant, threshold)


def specificity_ceiling(threshold: MovementThreshold) -> float:
    """The largest specificity this threshold can produce, under its own model.

    **The trap this exists to make visible.** Any ``τ`` calibrated to a target
    false-movement rate fixes specificity near a constant and hands all of J's
    variation to sensitivity, at which point ``J ≈ sensitivity`` and the
    specificity arm is decoration. ``max_relative_v1`` has this in the limit: it
    targets ``α ≈ 0``, so specificity is pinned at ``≈ 1``. A reported
    specificity sitting at its structural ceiling is an inert instrument, and
    :meth:`Phase0Result.disposition` prints the ceiling beside the number so it
    reads as one.

    Under ``pooled_log_noise_v2`` the fitted noise model is
    ``log q_variant − log q_base ~ N(0, σ²)`` under the null, so the
    false-movement rate is ``P(|Z| > k) = 2(1 − Φ(k))`` and the ceiling is
    ``2Φ(k) − 1 = erf(k/√2)``. ``σ`` cancels: the ceiling is a function of the
    declared ``k`` alone, which is exactly why ``k`` is swept rather than
    argued.

    Under ``max_relative_v1`` the model is exchangeability rather than
    normality. ``τ`` is the maximum of ``n`` null excursions, so a fresh null
    excursion exceeds it with probability ``1/(n+1)`` and the ceiling is
    ``n/(n+1)``. That is the drift with ``n`` stated as a number: 0.952 at 20
    base pairs, 0.976 at 40.

    Both are ceilings rather than predictions because the matched arm carries at
    least the base arm's noise. A matched fact that moves the quantity at all
    pushes the realised specificity below this.

    Args:
        threshold: A :class:`MovementThreshold` from either derivation.

    Returns:
        The structural upper bound on specificity, in ``(0, 1)``.
    """
    if threshold.rule == "max_relative_v1":
        return threshold.n_base_pairs / (threshold.n_base_pairs + 1.0)
    # k is never None on a pooled_log_noise_v2 threshold: the constructor refuses it,
    # so the cast asserts nothing the type system has not already been told.
    return math.erf(cast("float", threshold.k) / math.sqrt(2.0))


@dataclass(frozen=True, slots=True)
class FalsifierCase:
    """One planted triplet's hand-written, hand-scored falsifier case.

    Attributes:
        name: A label for the planted triplet, for tracing a failure back to it.
        q_base: The hand-written base response's extracted quantity.
        q_governing: The hand-written governing-arm response's extracted
            quantity — constructed so movement is obvious.
        q_matched: The hand-written matched-arm response's extracted quantity —
            constructed so the *absence* of movement is obvious.
        expect_governing_change: Always ``True`` in the registered battery: the
            governing contrast obviously must move.
        expect_matched_change: Always ``False`` in the registered battery: the
            matched contrast obviously must not move. Carried as a field rather
            than hardcoded so a test can also exercise the case where the
            extractor is expected to be wrong.
    """

    name: str
    q_base: float
    q_governing: float
    q_matched: float
    expect_governing_change: bool
    expect_matched_change: bool


@dataclass(frozen=True, slots=True)
class FalsifierBatteryResult:
    """The falsifier battery's verdict on the extractor.

    Attributes:
        n_cases: Planted triplets scored. 2 in the registered battery.
        sensitivity: Share of cases where the governing contrast's movement
            call matched :attr:`FalsifierCase.expect_governing_change`.
        specificity: Share of cases where the matched contrast's movement call
            matched :attr:`FalsifierCase.expect_matched_change`.
        n_sensitivity_events: Denominator behind ``sensitivity`` — equals
            ``n_cases``, printed explicitly per the second guard: a plausible
            zero does not announce itself, so the raw counts travel with the
            rate.
        n_specificity_events: Denominator behind ``specificity``.
    """

    n_cases: int
    sensitivity: float
    specificity: float
    n_sensitivity_events: int
    n_specificity_events: int

    @property
    def passed(self) -> bool:
        """Whether the battery cleared the registered bar: both rates at 1.0."""
        return self.sensitivity == 1.0 and self.specificity == 1.0


def run_falsifier_battery(
    cases: Sequence[FalsifierCase], threshold: MovementThreshold
) -> FalsifierBatteryResult:
    """Score the extractor against the planted, hand-written falsifier cases.

    Args:
        cases: Planted :class:`FalsifierCase` records — 2 in the registered
            battery, one that obviously must move and one that obviously must
            not.
        threshold: The :class:`MovementThreshold`, from
            :func:`derive_movement_threshold`.

    Returns:
        A :class:`FalsifierBatteryResult`. Passing it to
        :func:`compute_phase0_result` is the only way to obtain a
        :class:`Phase0Result` — see :class:`FalsifierBatteryFailedError`.

    Raises:
        ValueError: ``cases`` is empty.
    """
    if not cases:
        raise ValueError("run_falsifier_battery needs at least one planted case")
    governing_correct = 0
    matched_correct = 0
    for case in cases:
        governing_changed = classify_movement(case.q_base, case.q_governing, threshold)
        matched_changed = classify_movement(case.q_base, case.q_matched, threshold)
        if governing_changed == case.expect_governing_change:
            governing_correct += 1
        if matched_changed == case.expect_matched_change:
            matched_correct += 1
    n = len(cases)
    return FalsifierBatteryResult(
        n_cases=n,
        sensitivity=governing_correct / n,
        specificity=matched_correct / n,
        n_sensitivity_events=n,
        n_specificity_events=n,
    )


@dataclass(frozen=True, slots=True)
class TripletEvent:
    """One ``(triplet, repeat)`` pair's elicited quantity across all three arms.

    40 of these exist in Phase 0: 20 triplets × 2 repeats. Each contributes
    exactly one sensitivity event (governing vs base) and one specificity event
    (matched vs base) — never pooled, always keyed by ``triplet_id`` for
    clustering.

    Attributes:
        triplet_id: The triplet identifier — the cluster label.
        repeat: 0 or 1.
        q_base: The base file's elicited quantity for this repeat.
        q_governing: The governing-fact-changed file's elicited quantity.
        q_matched: The matched-non-governing-fact-changed file's elicited
            quantity.
    """

    triplet_id: str
    repeat: int
    q_base: float
    q_governing: float
    q_matched: float


@dataclass(frozen=True, slots=True)
class Phase0Result:
    """Phase 0's disposition: J, its decomposition, and the raw counts.

    ``j`` and ``ci_low``/``ci_high`` come directly from
    :func:`~decision_evals.stats.cluster.cluster_bootstrap_statistic` — this is
    the identical number the module docstring's identity refers to, not a second
    computation of it.

    Attributes:
        j: Youden's J, identically ``d = P(change|governing) − P(change|matched)``.
        ci_low: Lower bound of the cluster-bootstrapped percentile interval.
        ci_high: Upper bound.
        standard_error: Bootstrap standard deviation.
        confidence: Nominal coverage, e.g. 0.95.
        sensitivity: ``P(change | governing)``.
        specificity: ``1 − P(change | matched)``.
        specificity_ceiling: The largest specificity :attr:`threshold` can
            structurally produce, from :func:`specificity_ceiling`. A
            :attr:`specificity` at or above it means the threshold produced the
            number and the instrument did not.
        min_sens_spec: ``min(sensitivity, specificity)`` — printed because
            ``J >= KILL_THRESHOLD_J`` is reachable asymmetrically, e.g.
            ``(1.00, 0.70)``, and that is not "both arms adequate".
        rule: The :data:`MovementRule` J was scored under. Two runs under
            different rules are two venues, so the rule travels with the number.
        n_sensitivity_events: Denominator behind ``sensitivity`` (40 in Phase 0).
        n_specificity_events: Denominator behind ``specificity`` (40 in Phase 0).
        n_dropped_events: Events that could not be put on :attr:`rule`'s scale
            and were excluded from both arms. A denominator that shrank quietly
            is the failure this field exists to prevent.
        n_governing_change: Raw count of governing contrasts scored as movement.
        n_matched_change: Raw count of matched contrasts scored as movement.
        n_clusters: Distinct triplets resampled (20 in Phase 0).
        n_resamples: Bootstrap replicates drawn.
        threshold: The :class:`MovementThreshold` this result was scored under.
            When the bootstrap recomputed the threshold, this is the full-sample
            recomputation rather than the one passed in, so the threshold
            printed is the threshold J was computed at.
        battery: The :class:`FalsifierBatteryResult` that authorised this
            result to exist at all.
    """

    j: float
    ci_low: float
    ci_high: float
    standard_error: float
    confidence: float
    sensitivity: float
    specificity: float
    specificity_ceiling: float
    min_sens_spec: float
    rule: MovementRule
    n_sensitivity_events: int
    n_specificity_events: int
    n_dropped_events: int
    n_governing_change: int
    n_matched_change: int
    n_clusters: int
    n_resamples: int
    threshold: MovementThreshold
    battery: FalsifierBatteryResult

    @property
    def kill(self) -> bool:
        """Whether the pre-registered kill fires: ``J >= KILL_THRESHOLD_J``."""
        return self.j >= KILL_THRESHOLD_J

    @property
    def specificity_is_inert(self) -> bool:
        """Whether specificity has reached the ceiling its threshold implies.

        At or above the ceiling, the threshold is producing the specificity and
        J reduces to sensitivity. The comparison is ``>=`` rather than ``==``
        because a ceiling is an upper bound on the *expected* rate and a finite
        run can land on top of it: 40 events under ``max_relative_v1`` at 20
        base pairs have a ceiling of 0.952 and a perfectly ordinary realised
        specificity of 1.000.
        """
        return self.specificity >= self.specificity_ceiling

    def disposition(self) -> str:
        """A one-paragraph disposition that never reports J alone.

        States ``min(sensitivity, specificity)`` beside J in every case, and
        when the kill fires with one arm below :data:`ADEQUACY_CEILING`, says
        so in those words rather than "both arms adequate" — the specific
        wording the registration requires.

        Three further things travel with the number, each because a J reported
        without it has already misled a reader here: the movement rule, the
        structural ceiling on specificity, and the count of events that could
        not be scored at all.
        """
        base = (
            f"J = {self.j:.3f} [{self.ci_low:.3f}, {self.ci_high:.3f}] over "
            f"{self.n_clusters} clusters (95% cluster bootstrap) under "
            f"{self.rule} — sensitivity {self.sensitivity:.3f} "
            f"({self.n_governing_change}/{self.n_sensitivity_events}), "
            f"specificity {self.specificity:.3f} "
            f"({self.n_specificity_events - self.n_matched_change}/{self.n_specificity_events}, "
            f"structural ceiling {self.specificity_ceiling:.3f}), "
            f"min(sensitivity, specificity) = {self.min_sens_spec:.3f}, "
            f"{self.n_dropped_events} events dropped as unscorable."
        )
        if self.specificity_is_inert:
            base = (
                f"{base} Specificity is at its structural ceiling, so the threshold produced it "
                "rather than the instrument and J is reading as sensitivity alone."
            )
        if not self.kill:
            return f"{base} J < {KILL_THRESHOLD_J:.2f}: the venue survives."
        if self.min_sens_spec < ADEQUACY_CEILING:
            return (
                f"{base} J >= {KILL_THRESHOLD_J:.2f}, but at least one arm is below "
                f"{ADEQUACY_CEILING:.2f} — this is NOT both arms adequate, and the kill's "
                "arithmetic (0.85 and 0.85) does not describe this result."
            )
        return (
            f"{base} J >= {KILL_THRESHOLD_J:.2f} with both arms at or above "
            f"{ADEQUACY_CEILING:.2f}: the venue closes."
        )


def _is_scorable(event: TripletEvent, rule: MovementRule) -> bool:
    """Whether both of an event's contrasts can be put on ``rule``'s scale.

    Scorability is judged per *event*, never per contrast. A governing contrast
    kept while its matched partner is dropped would leave the two arms with
    different denominators, and J is a paired difference of two means over the
    same items.
    """
    if rule == "max_relative_v1":
        return event.q_base != 0.0
    return event.q_base > 0.0 and event.q_governing > 0.0 and event.q_matched > 0.0


def _base_pair_by_triplet(
    base_pairs: Sequence[BaseRepeatPair], triplet_ids: Sequence[str]
) -> dict[str, BaseRepeatPair]:
    """One base pair per triplet, covering every triplet in ``triplet_ids``.

    Raises:
        ValueError: ``base_pairs`` names a triplet twice, or an event's triplet
            has no base pair. Either one means the threshold belongs to a corpus
            that is not the one being scored, which is a refusal whether or not
            the threshold is about to be recomputed.
    """
    by_triplet: dict[str, BaseRepeatPair] = {}
    for pair in base_pairs:
        if pair.triplet_id in by_triplet:
            raise ValueError(f"{pair.triplet_id} appears twice in base_pairs")
        by_triplet[pair.triplet_id] = pair
    missing = sorted({tid for tid in triplet_ids if tid not in by_triplet})
    if missing:
        raise ValueError(
            f"no base pair for {', '.join(missing)}: the threshold belongs to a different corpus "
            "than the one being scored"
        )
    return by_triplet


def compute_phase0_result(
    events: Sequence[TripletEvent],
    threshold: MovementThreshold,
    battery: FalsifierBatteryResult,
    *,
    base_pairs: Sequence[BaseRepeatPair],
    recompute_threshold: bool = True,
    confidence: float = 0.95,
    n_resamples: int = 10_000,
    seed: int | None = None,
) -> Phase0Result:
    """Score Phase 0: J via a cluster bootstrap on the triplet, plus its decomposition.

    **The threshold is recomputed inside every replicate by default.** ``τ`` is
    a nuisance parameter estimated from the data, so holding it fixed across
    replicates treats a random quantity as known and the interval under-covers:
    measured at a realised SD of 1.23 to 2.31 times the closed form and coverage
    0.61 to 0.85 against a nominal 0.95. Resampling the same clusters for the
    base pairs and for the indicators puts that variation back in.

    ``recompute_threshold=False`` restores the fixed-``τ`` path so a checkpoint
    can be scored both ways and the difference read off. It is the only way to
    score a ``max_relative_v1`` threshold, because a maximum is not
    Hadamard-differentiable and its bootstrap is inconsistent at every sample
    size.

    Args:
        events: One :class:`TripletEvent` per ``(triplet, repeat)`` pair — 40 in
            Phase 0. Never pass one row per file; a triplet's three files are
            three fields of one event, which is what stops the analysis from
            offering a pooled-over-files code path at all.
        threshold: The :class:`MovementThreshold`, derived before any of
            ``events`` was examined. When the threshold is recomputed, this
            supplies the rule and the declared ``k``; the reported threshold is
            the full-sample recomputation.
        battery: A passed :class:`FalsifierBatteryResult`. This is the gate:
            see :class:`FalsifierBatteryFailedError`.
        base_pairs: The base repeat-0/repeat-1 pairs ``threshold`` came from,
            one per triplet. Required rather than optional: an argument that
            defaulted to ``None`` would fall back to the fixed-``τ`` path
            silently, which is the undercoverage this signature exists to fix.
        recompute_threshold: Whether each replicate refits ``τ`` from the base
            pairs it drew.
        confidence: Nominal bootstrap coverage.
        n_resamples: Bootstrap replicates.
        seed: Seed for reproducibility — a report that moves between two
            readings of the same checkpoint is not a report.

    Returns:
        A :class:`Phase0Result`.

    Raises:
        FalsifierBatteryFailedError: ``battery.passed`` is ``False``. No J is
            computed; the extractor is the finding instead.
        ValueError: ``events`` or ``base_pairs`` is empty, every event was
            dropped as unscorable, ``recompute_threshold`` is set against a
            ``max_relative_v1`` threshold, ``base_pairs`` names a triplet twice
            or misses one the events carry, or via
            :func:`~decision_evals.stats.cluster.cluster_bootstrap_statistic`.
    """
    if not battery.passed:
        raise FalsifierBatteryFailedError(
            "the falsifier battery has not passed "
            f"(sensitivity={battery.sensitivity!r}, specificity={battery.specificity!r} "
            f"over {battery.n_cases} planted cases); standing rule 2 refuses any J until "
            "both read 1.0. The extractor is the finding, not a caveat on a number."
        )
    if not events:
        raise ValueError("compute_phase0_result needs at least one triplet event")
    if not base_pairs:
        raise ValueError("compute_phase0_result needs the base-arm pairs the threshold came from")
    if recompute_threshold and threshold.rule != "pooled_log_noise_v2":
        raise ValueError(
            f"a {threshold.rule} threshold is a maximum, which is not Hadamard-differentiable, "
            "so recomputing it inside each replicate gives an inconsistent bootstrap. Pass "
            "recompute_threshold=False to score it under the fixed-threshold path."
        )

    scorable = [event for event in events if _is_scorable(event, threshold.rule)]
    n_dropped = len(events) - len(scorable)
    if not scorable:
        raise ValueError(
            f"all {len(events)} events were unscorable on the {threshold.rule} scale; there is "
            "no J here, the extraction is the finding"
        )

    triplet_ids = [event.triplet_id for event in scorable]
    by_triplet = _base_pair_by_triplet(base_pairs, triplet_ids)
    # Cluster codes in the order cluster_bootstrap_statistic will produce them:
    # numpy sorts the unique labels, so sorting the base pairs the same way lines
    # a drawn cluster up with the base pair it must refit from.
    labels = sorted(set(triplet_ids))
    code_of = {label: index for index, label in enumerate(labels)}
    codes = np.array([code_of[tid] for tid in triplet_ids], dtype=np.intp)
    cluster_sizes = np.bincount(codes, minlength=len(labels)).astype(np.float64)
    statistic: Callable[[npt.NDArray[np.intp]], float]

    if recompute_threshold:
        squares = np.array(
            [
                log_movement(by_triplet[label].q_repeat0, by_triplet[label].q_repeat1) ** 2
                for label in labels
            ],
            dtype=np.float64,
        )
        k = cast("float", threshold.k)
        # Through log_movement rather than a vectorised np.log, so the movements
        # the bootstrap compares against tau are bit-for-bit the ones
        # classify_movement produces for the reported counts. A last-ulp
        # disagreement between the two would break the J = sens + spec - 1
        # identity at a boundary and nowhere else.
        log_governing = np.array(
            [log_movement(e.q_base, e.q_governing) for e in scorable], dtype=np.float64
        )
        log_matched = np.array(
            [log_movement(e.q_base, e.q_matched) for e in scorable], dtype=np.float64
        )

        def refit_j(picked: npt.NDArray[np.intp]) -> float:
            # Whole clusters come along, so an event count divided by the cluster
            # size is exactly how many times that cluster was drawn. That is what
            # keeps sigma-hat weighted by triplet, as its definition says, rather
            # than by event.
            drawn = np.bincount(codes[picked], minlength=len(labels)) / cluster_sizes
            tau = k * math.sqrt(float(drawn @ squares) / float(drawn.sum()))
            return float((log_governing[picked] > tau).mean() - (log_matched[picked] > tau).mean())

        statistic = refit_j
        sigma_hat_full = math.sqrt(float(squares.mean()))
        effective = MovementThreshold(
            value=k * sigma_hat_full,
            n_base_pairs=len(labels),
            rule="pooled_log_noise_v2",
            k=k,
            sigma_hat=sigma_hat_full,
        )
    else:
        effective = threshold
        governing = np.array(
            [classify_movement(e.q_base, e.q_governing, threshold) for e in scorable],
            dtype=np.float64,
        )
        matched = np.array(
            [classify_movement(e.q_base, e.q_matched, threshold) for e in scorable],
            dtype=np.float64,
        )

        def fixed_j(picked: npt.NDArray[np.intp]) -> float:
            return float(governing[picked].mean() - matched[picked].mean())

        statistic = fixed_j

    boot = cluster_bootstrap_statistic(
        triplet_ids,
        statistic,
        confidence=confidence,
        n_resamples=n_resamples,
        seed=seed,
    )

    n = len(scorable)
    n_governing_change = sum(
        classify_movement(e.q_base, e.q_governing, effective) for e in scorable
    )
    n_matched_change = sum(classify_movement(e.q_base, e.q_matched, effective) for e in scorable)
    sensitivity = n_governing_change / n
    specificity = 1.0 - (n_matched_change / n)

    return Phase0Result(
        j=boot.point_estimate,
        ci_low=boot.ci_low,
        ci_high=boot.ci_high,
        standard_error=boot.standard_error,
        confidence=boot.confidence,
        sensitivity=sensitivity,
        specificity=specificity,
        specificity_ceiling=specificity_ceiling(effective),
        min_sens_spec=min(sensitivity, specificity),
        rule=effective.rule,
        n_sensitivity_events=n,
        n_specificity_events=n,
        n_dropped_events=n_dropped,
        n_governing_change=n_governing_change,
        n_matched_change=n_matched_change,
        n_clusters=boot.n_clusters,
        n_resamples=boot.n_resamples,
        threshold=effective,
        battery=battery,
    )


def extractor_movement_agreement(ratings: Sequence[Sequence[bool]]) -> FleissKappaResult:
    """Fleiss' kappa across the three extractors' movement calls.

    A health check on the instrument, not a result — the registration is
    explicit that this is reported "beside" ``J``, never in place of it.
    Delegates directly to
    :func:`decision_evals.stats.agreement.fleiss_kappa`: Track H does not need
    a second implementation of chance-corrected agreement, it needs the
    existing one pointed at boolean movement calls (one call per extractor per
    response) instead of the discrete labels it was written for.

    Args:
        ratings: One sequence of three ``bool`` movement calls per response —
            120 responses in Phase 0, one row each.

    Returns:
        A :class:`~decision_evals.stats.agreement.FleissKappaResult`.

    Raises:
        ValueError: Via :func:`fleiss_kappa` — empty, ragged, or fewer than two
            raters.
        DegenerateAgreementError: Via :func:`fleiss_kappa` — every call fell in
            one category.
    """
    return fleiss_kappa(ratings)
