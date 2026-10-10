from decimal import Decimal

import finassert as fa
from finassert.core.models import Outcome


def test_nonnegative_passes_for_zero_and_positive_values() -> None:
    result = fa.check({"value": [0, 1, Decimal("2.5")]}, [fa.non_negative(column="value")])

    assert result.passed
    assert result.results[0].observed == 0


def test_nonnegative_identifies_violating_rows() -> None:
    result = fa.check(
        [{"value": 10}, {"value": -2}, {"value": -3}],
        [fa.non_negative(column="value")],
    ).results[0]

    assert result.outcome is Outcome.FAILED
    assert result.metadata["violation_count"] == 2
    assert result.metadata["violations"] == [{"row": 1, "value": -2}, {"row": 2, "value": -3}]


def test_nonnegative_honors_absolute_tolerance() -> None:
    report = fa.check(
        {"value": [Decimal("-0.01")]}, [fa.non_negative(column="value", tolerance=Decimal("0.01"))]
    )

    assert report.passed


def test_nonnegative_null_policy_is_explicit() -> None:
    failed = fa.check({"value": [1, None]}, [fa.non_negative(column="value")])
    ignored = fa.check(
        {"value": [1, None]},
        [fa.non_negative(column="value", null_policy="ignore")],
    )
    skipped = fa.check(
        {"value": [1, None]},
        [fa.non_negative(column="value", null_policy="skip")],
    )

    assert not failed.passed
    assert ignored.passed
    assert skipped.results[0].outcome is Outcome.SKIPPED


def test_nonnegative_empty_dataset_passes_vacuously() -> None:
    report = fa.check({"value": []}, [fa.non_negative(column="value")])

    assert report.passed
    assert report.results[0].metadata["checked_count"] == 0


def test_nonnegative_non_finite_value_fails() -> None:
    report = fa.check({"value": [float("inf")]}, [fa.non_negative(column="value")])

    assert not report.passed
