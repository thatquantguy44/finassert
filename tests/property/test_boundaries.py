"""Exact finite Decimal arithmetic; scaling stays below context precision."""

from decimal import Decimal

from hypothesis import given
from hypothesis import strategies as st

import finassert as fa
from finassert.numerical import Tolerance

from .strategies import amounts, cash_ledgers, duplicated_labels, fund_values, nullable_amounts
from .test_financial_properties import _cash_rule


@given(amounts, st.integers(0, 100_000), st.sampled_from([-1, 1]))
def test_absolute_tolerance_is_inclusive(expected, cents, sign):
    bound = Decimal(cents) / 100
    tolerance = Tolerance(absolute=bound)
    assert tolerance.is_close(expected + sign * bound, expected)
    assert not tolerance.is_close(expected + sign * (bound + Decimal("0.01")), expected)


@given(st.integers(1, 1000), st.integers(1, 9))
def test_relative_tolerance_exact_boundary(scale, numerator):
    # actual is the larger magnitude: difference = r * max(|actual|, |expected|).
    actual = Decimal(scale * 10)
    expected = Decimal(scale * (10 - numerator))
    tolerance = Tolerance(relative=Decimal(numerator) / 10)
    assert tolerance.is_close(actual, expected)
    assert not tolerance.is_close(actual, expected - Decimal("0.01"))


@given(amounts, amounts, amounts.map(abs), st.integers(1, 1000))
def test_positive_scaling_preserves_tolerance_decision(actual, expected, absolute, multiplier):
    relative = Decimal("0.001")
    assert Tolerance(absolute, relative).is_close(actual, expected) == Tolerance(
        absolute * multiplier, relative
    ).is_close(actual * multiplier, expected * multiplier)


@given(cash_ledgers(), st.integers(1, 100))
def test_cash_identity_survives_currency_unit_scaling(ledger, scale):
    scaled = {
        key: [v * scale for v in values] if key in {"open", "in", "out", "close"} else values
        for key, values in ledger.items()
    }
    assert fa.check(scaled, [_cash_rule()]).passed


@given(fund_values, st.integers(1, 100))
def test_nav_identity_and_a_localized_break_survive_scaling(funds, scale):
    rows = [
        {"fund": fund, "mv": value * scale, "nav": sum(values) * scale}
        for fund, values in funds.items()
        for value in values
    ]
    rule = fa.nav_reconciles(market_value="mv", nav="nav", group_by=["fund"])
    assert fa.check(rows, [rule]).passed
    broken = rows[0]["fund"]
    for row in rows:
        if row["fund"] == broken:
            row["nav"] += Decimal("0.01") * scale
    result = fa.check(rows, [rule]).results[0]
    assert result.outcome is fa.Outcome.FAILED
    assert [entry["group"] for entry in result.metadata["failed_groups"]] == [{"fund": broken}]


class LabeledColumn:
    def __init__(self, values, labels):
        self.values, self.labels = values, labels

    def column(self, name):
        return self.values, self.labels


@given(duplicated_labels(), st.integers(0, 5))
def test_duplicate_row_labels_preserve_failure_order_and_total(labels, cap):
    result = fa.check(
        LabeledColumn([-1] * len(labels), labels), [fa.non_negative(column="v", max_violations=cap)]
    ).results[0]
    assert result.metadata["violation_count"] == len(labels)
    assert [v["row"] for v in result.metadata["violations"]] == labels[:cap]
    assert result.metadata["violations_truncated"] == (len(labels) > cap)


@given(nullable_amounts)
def test_null_policy_never_turns_missing_values_into_zero(values):
    fail = fa.check({"v": values}, [fa.non_negative(column="v")]).results[0]
    ignore = fa.check({"v": values}, [fa.non_negative(column="v", null_policy="ignore")]).results[0]
    assert fail.metadata["invalid_row_count"] == values.count(None)
    assert ignore.metadata["invalid_row_count"] == 0
    assert (
        fail.metadata["violation_count"]
        == ignore.metadata["violation_count"]
        == sum(value is not None and value < 0 for value in values)
    )
