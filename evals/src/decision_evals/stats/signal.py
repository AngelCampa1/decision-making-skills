"""Separating discrimination from response bias on a two-option answer key.

Accuracy on a balanced two-option key adds together two different things: how
well a model tells the cases apart, and how often it picks one option whatever
the case. A model answering ``expedite`` to nine items in ten scores near 0.63
on a set that wants ``expedite`` half the time, and none of that 0.63 is
discrimination. Reading it as difficulty is how a template that measures a
preference gets mistaken for a hard one, which is what happened here on
2026-08-28 to ``hrd-002-shipping-escalation``.

Signal detection separates the two. :func:`informedness` — Youden's J,
sensitivity plus specificity minus one — is zero for any constant-answer policy
at any base rate and is unmoved by a pure shift in preference. :func:`skew`
names the other half directly: the rate the model answers an option minus the
rate the items called for it.

Both read the ``expected`` and ``parsed`` fields the runner already writes on
every record, so they recompute over runs that are finished and published
without costing a call.

*J does not depend on which option is called positive.* Swapping the labels
exchanges sensitivity with specificity and leaves their sum alone, so a
per-template choice of positive that nobody can make principally does not have
to be made. Skew is not symmetric that way and never could be: it is a
statement about one named option, and on a two-option key the other option's
skew is its negation.
"""

from __future__ import annotations

from collections.abc import Hashable, Sequence
from dataclasses import dataclass


class DegenerateSignalError(ValueError):
    """A signal statistic was asked for where it has no value.

    Informedness needs both classes present: with no negative items there is no
    specificity to measure, and returning zero would be indistinguishable from
    a model that discriminates not at all. The 2026-08-28 screen hit this on two
    templates whose items at one seed drew a single answer class, and recording
    those as zero would have put two undefined cells into a mean.
    """


@dataclass(frozen=True, slots=True)
class SignalResult:
    """Discrimination on a two-option key, and the parts it decomposes into.

    Attributes:
        positive: The label counted as positive. Reported because sensitivity
            and specificity are stated relative to it, even though
            ``informedness`` is not.
        n_positive: Items whose answer key is ``positive``.
        n_negative: Items whose answer key is anything else.
        sensitivity: Share of positive items answered ``positive``.
        specificity: Share of negative items not answered ``positive``.
        informedness: ``sensitivity + specificity - 1``. Zero for any
            constant-answer policy, one for a perfect one, negative for a model
            answering against the key.
    """

    positive: Hashable
    n_positive: int
    n_negative: int
    sensitivity: float
    specificity: float
    informedness: float


def _paired(expected: Sequence[Hashable], parsed: Sequence[Hashable]) -> None:
    """Reject inputs that are not two same-length, non-empty answer columns."""
    if len(expected) != len(parsed):
        raise ValueError(
            f"expected and parsed must be the same length, got {len(expected)} and {len(parsed)}"
        )
    if not expected:
        raise ValueError("expected must not be empty")


def informedness(
    expected: Sequence[Hashable],
    parsed: Sequence[Hashable],
    *,
    positive: Hashable,
) -> SignalResult:
    """Youden's J over one template's items, with the parts it is built from.

    Call this per template and average over templates. Pooling items first lets
    whichever template minted the most items decide the answer, and template
    counts here differ by a factor of two.

    Rows the model did not answer are the caller's to drop. A parse failure is
    not a wrong answer and this cannot tell them apart: everything not equal to
    ``positive`` counts as a negative response, so an unparsed row would be
    scored as a confident negative. Filter on ``parse_status`` first.

    Args:
        expected: The answer key, one label per item.
        parsed: The model's answers, in the same item order.
        positive: The label counted as positive. The returned ``informedness``
            is the same whichever of the two options is passed.

    Returns:
        A :class:`SignalResult`.

    Raises:
        ValueError: On mismatched lengths or empty input.
        DegenerateSignalError: If the key holds no positive or no negative item,
            which leaves sensitivity or specificity with no items to average.
    """
    _paired(expected, parsed)

    positives = [got for want, got in zip(expected, parsed, strict=True) if want == positive]
    negatives = [got for want, got in zip(expected, parsed, strict=True) if want != positive]

    if not positives:
        raise DegenerateSignalError(
            f"no item in the key expects {positive!r}, so sensitivity has nothing to average"
        )
    if not negatives:
        raise DegenerateSignalError(
            f"every item in the key expects {positive!r}, so specificity has nothing to average"
        )

    sensitivity = sum(got == positive for got in positives) / len(positives)
    specificity = sum(got != positive for got in negatives) / len(negatives)

    return SignalResult(
        positive=positive,
        n_positive=len(positives),
        n_negative=len(negatives),
        sensitivity=sensitivity,
        specificity=specificity,
        informedness=sensitivity + specificity - 1.0,
    )


def skew(
    expected: Sequence[Hashable],
    parsed: Sequence[Hashable],
    *,
    option: Hashable,
) -> float:
    """How much more often the model answers ``option`` than the key wants it.

    Positive means the model leans toward ``option``; zero means it answers it
    at exactly the rate the items called for. On a two-option key the other
    option's skew is this negated, so a reported skew has to name its option or
    it says nothing.

    Unlike :func:`informedness` this stays defined when the key holds a single
    answer class, because both rates are still counts over the same items. It is
    also blind to whether the model got any individual item right: a model
    answering at the right overall rate and wrong every time scores zero here,
    which is the division of labour between the two functions.

    Args:
        expected: The answer key, one label per item.
        parsed: The model's answers, in the same item order.
        option: The option to measure the lean toward.

    Returns:
        Answered rate minus wanted rate, in ``[-1, 1]``.

    Raises:
        ValueError: On mismatched lengths or empty input.
    """
    _paired(expected, parsed)

    answered = sum(got == option for got in parsed) / len(parsed)
    wanted = sum(want == option for want in expected) / len(expected)
    return answered - wanted
