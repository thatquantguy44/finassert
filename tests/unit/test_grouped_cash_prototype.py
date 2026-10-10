from decimal import Decimal

import finassert as fa
from finassert.adapters import ColumnMapping, GroupKey
from finassert.core.models import Outcome
from finassert.numerical import Tolerance
from finassert.rules._cash_reconciliation import _GroupedCashReconciliationRule


def cash_mapping(*, row_key: str | None = None) -> ColumnMapping:
    return ColumnMapping(
        {
            "opening_cash": "open",
            "inflows": "in",
            "outflows": "out",
            "cash_pnl": "pnl",
            "closing_cash": "close",
        },
        group_keys=(GroupKey("portfolio", "portfolio_id"), GroupKey("currency", "ccy")),
        row_key=row_key,
    )


def test_grouped_cash_reconciliation_aggregates_additive_slices() -> None:
    data = {
        "portfolio_id": ["A", "A", "B"],
        "ccy": ["USD", "USD", "EUR"],
        "open": [100, 50, 100],
        "in": [10, 0, 5],
        "out": [5, 1, 3],
        "pnl": [1, 0, -2],
        "close": [106, 49, 99],
    }

    result = fa.check(data, [_GroupedCashReconciliationRule(cash_mapping())]).results[0]

    assert result.outcome is Outcome.FAILED
    assert result.metadata["group_count"] == 2
    assert result.metadata["failed_group_count"] == 1
    assert result.metadata["failed_groups"] == [
        {
            "group": {"portfolio": "B", "currency": "EUR"},
            "observed": 99,
            "expected": 100,
            "difference": -1,
            "row_count": 1,
        }
    ]


def test_grouped_cash_reconciliation_preserves_decimal_tolerance() -> None:
    data = {
        "portfolio_id": ["A"],
        "ccy": ["USD"],
        "open": [Decimal("100.00")],
        "in": [Decimal("0.00")],
        "out": [Decimal("0.00")],
        "pnl": [Decimal("0.00")],
        "close": [Decimal("99.99")],
    }
    rule = _GroupedCashReconciliationRule(
        cash_mapping(),
        tolerance=Tolerance(absolute=Decimal("0.01")),
    )

    assert fa.check(data, [rule]).passed


def test_grouped_cash_reconciliation_uses_configured_row_key() -> None:
    data = {
        "record_id": ["cash-001"],
        "portfolio_id": ["A"],
        "ccy": ["USD"],
        "open": [100],
        "in": [None],
        "out": [0],
        "pnl": [0],
        "close": [100],
    }

    result = fa.check(
        data,
        [_GroupedCashReconciliationRule(cash_mapping(row_key="record_id"))],
    ).results[0]

    assert result.outcome is Outcome.FAILED
    assert result.metadata["invalid_rows"] == [{"row": "cash-001", "fields": ["inflows"]}]


def test_grouped_cash_reconciliation_errors_on_missing_group_key() -> None:
    data = {
        "portfolio_id": ["A"],
        "ccy": [None],
        "open": [100],
        "in": [0],
        "out": [0],
        "pnl": [0],
        "close": [100],
    }

    result = fa.check(data, [_GroupedCashReconciliationRule(cash_mapping())]).results[0]

    assert result.outcome is Outcome.ERROR
    assert result.metadata["exception_type"] == "InvalidDataError"


def test_grouped_cash_reconciliation_errors_on_unaligned_columns() -> None:
    data = {
        "portfolio_id": ["A"],
        "ccy": ["USD"],
        "open": [100, 200],
        "in": [0],
        "out": [0],
        "pnl": [0],
        "close": [100],
    }

    result = fa.check(data, [_GroupedCashReconciliationRule(cash_mapping())]).results[0]

    assert result.outcome is Outcome.ERROR
    assert "aligned row labels" in result.message


def test_grouped_cash_reconciliation_skips_empty_input() -> None:
    data = {column: [] for column in ["portfolio_id", "ccy", "open", "in", "out", "pnl", "close"]}

    result = fa.check(data, [_GroupedCashReconciliationRule(cash_mapping())]).results[0]

    assert result.outcome is Outcome.SKIPPED
    assert result.metadata["group_count"] == 0
