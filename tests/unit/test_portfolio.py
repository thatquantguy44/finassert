from decimal import Decimal

import pytest

import finassert as fa
from finassert.core.models import Outcome


def test_weights_sum_to_one_with_decimal_values() -> None:
    report = fa.check(
        {"weight": [Decimal("0.10"), Decimal("0.25"), Decimal("0.65")]},
        [fa.weights_sum_to_one(tolerance=Decimal("0"))],
    )

    assert report.passed
    assert report.results[0].observed == Decimal("1.00")


def test_weights_failure_explains_observed_total() -> None:
    result = fa.check({"weight": [0.2, 0.7]}, [fa.weights_sum_to_one()]).results[0]

    assert result.outcome is Outcome.FAILED
    assert result.observed == pytest.approx(0.9)
    assert result.expected == 1


def test_weights_missing_column_is_evaluation_error() -> None:
    result = fa.check({"allocation": [1]}, [fa.weights_sum_to_one()]).results[0]

    assert result.outcome is Outcome.ERROR
    assert result.metadata["exception_type"] == "ColumnNotFoundError"


def test_weights_missing_values_fail_by_default() -> None:
    result = fa.check({"weight": [0.5, None, 0.5]}, [fa.weights_sum_to_one()]).results[0]

    assert result.outcome is Outcome.FAILED
    assert result.metadata["missing_rows"] == [1]


def test_weights_can_ignore_missing_values_explicitly() -> None:
    report = fa.check(
        {"weight": [0.5, None, 0.5]},
        [fa.weights_sum_to_one(null_policy="ignore")],
    )

    assert report.passed


def test_weights_empty_dataset_fails() -> None:
    report = fa.check({"weight": []}, [fa.weights_sum_to_one()])

    assert not report.passed


def test_weights_non_finite_value_fails() -> None:
    report = fa.check({"weight": [float("nan"), 1]}, [fa.weights_sum_to_one()])

    assert not report.passed
