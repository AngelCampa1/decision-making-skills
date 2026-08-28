"""Example-based tests for the signal-detection layer.

The identities live in ``tests/property/test_stats_properties.py``. What is here
is the input validation and the two cases that come from real readings: a key
holding one answer class, and the difference between a statistic that is
undefined and one that is zero.
"""

from __future__ import annotations

import pytest

from decision_evals.stats import DegenerateSignalError, informedness, skew


class TestRefusals:
    """Every branch that declines to return a number, and why it declines."""

    def test_a_key_with_no_positive_item_refuses(self) -> None:
        with pytest.raises(DegenerateSignalError, match="sensitivity"):
            informedness(["a", "a"], ["a", "b"], positive="b")

    def test_a_key_with_no_negative_item_refuses(self) -> None:
        with pytest.raises(DegenerateSignalError, match="specificity"):
            informedness(["a", "a"], ["a", "b"], positive="a")

    def test_columns_of_different_lengths_refuse(self) -> None:
        with pytest.raises(ValueError, match="same length"):
            informedness(["a", "b"], ["a"], positive="a")
        with pytest.raises(ValueError, match="same length"):
            skew(["a", "b"], ["a"], option="a")

    def test_an_empty_key_refuses(self) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            informedness([], [], positive="a")
        with pytest.raises(ValueError, match="must not be empty"):
            skew([], [], option="a")


class TestTheOneSidedTemplate:
    """`hrd-002-shipping-escalation` as measured on 2026-08-28, in miniature.

    Twelve items, half wanting each option, and a model answering the first
    option to all but one. Accuracy reads a little over half and looks like
    difficulty; sensitivity is perfect, specificity is near zero, and J says the
    model is barely reading the item.
    """

    EXPECTED = ["expedite"] * 6 + ["leave_standard"] * 6
    PARSED = ["expedite"] * 11 + ["leave_standard"]

    def test_accuracy_and_discrimination_disagree(self) -> None:
        accuracy = sum(
            want == got for want, got in zip(self.EXPECTED, self.PARSED, strict=True)
        ) / len(self.EXPECTED)
        result = informedness(self.EXPECTED, self.PARSED, positive="expedite")

        assert accuracy == pytest.approx(7 / 12)
        assert result.sensitivity == pytest.approx(1.0)
        assert result.specificity == pytest.approx(1 / 6)
        assert result.informedness == pytest.approx(1 / 6)

    def test_the_skew_is_what_the_accuracy_was_reading(self) -> None:
        assert skew(self.EXPECTED, self.PARSED, option="expedite") == pytest.approx(5 / 12)

    def test_the_result_reports_the_counts_behind_it(self) -> None:
        result = informedness(self.EXPECTED, self.PARSED, positive="expedite")
        assert result.positive == "expedite"
        assert result.n_positive == 6
        assert result.n_negative == 6


class TestSkewWhereJIsUndefined:
    """A single answer class leaves skew defined and informedness not.

    Two templates in the 2026-08-28 screen drew one answer class at the seed
    they ran on. Recording their J as zero would have put two undefined cells
    into a mean of ten.
    """

    def test_skew_returns_where_informedness_refuses(self) -> None:
        assert skew(["a", "a"], ["a", "b"], option="a") == pytest.approx(-0.5)
        with pytest.raises(DegenerateSignalError):
            informedness(["a", "a"], ["a", "b"], positive="a")
