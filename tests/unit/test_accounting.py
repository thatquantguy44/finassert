from datetime import date
from decimal import Decimal
from typing import Any

import pandas as pd
import pytest

import finassert as fa
from finassert.adapters import ColumnMapping, FieldAggregation, GroupKey
from finassert.core.models import Outcome
from finassert.loaders import parse_csv
from finassert.numerical import Tolerance
from finassert.rules import CashReconciliationRule, OutflowSign


def summary(**overrides: Any) -> dict[str, list[Any]]:
    data: dict[str, list[Any]] = {
        "portfolio": ["A", "B"],
        "ccy": ["USD", "EUR"],
        "open": [100, 100],
        "in": [10, 5],
        "out": [5, 3],
        "pnl": [1, -2],
        "close": [106, 99],
    }
    data.update(overrides)
    return data


def cash_rule(**overrides: Any) -> CashReconciliationRule:
    arguments: dict[str, Any] = {
        "outflow_sign": "positive",
        "opening_cash": "open",
        "inflows": "in",
        "outflows": "out",
        "cash_pnl": "pnl",
        "closing_cash": "close",
        "group_by": ["portfolio"],
        "currency": "ccy",
    }
    arguments.update(overrides)
    return fa.cash_reconciles(**arguments)


def only(data: Any, rule: Any) -> fa.ValidationResult:
    return fa.check(data, [rule]).results[0]


# Cash reconciliation ---------------------------------------------------------


def test_cash_failure_names_the_group_rows_and_difference() -> None:
    result = only(summary(), cash_rule())

    assert result.outcome is Outcome.FAILED
    assert result.message == "1 of 2 group(s) do not reconcile."
    assert result.metadata["equation"] == (
        "closing_cash = opening_cash + inflows - outflows + cash_pnl"
    )
    assert result.metadata["currency"] == "reconciled separately for each value of 'ccy'"
    assert result.metadata["failed_groups"] == [
        {
            "group": {"portfolio": "B", "currency": "EUR"},
            "reason": "does_not_reconcile",
            "observed": 99,
            "expected": 100,
            "difference": -1,
            "row_count": 1,
            "rows": [1],
        }
    ]


def test_negative_outflows_are_added() -> None:
    data = summary(out=[-5, -3], close=[106, 100])
    assert only(data, cash_rule(outflow_sign="negative")).passed
    assert not only(data, cash_rule(outflow_sign="positive")).passed
    assert "+ outflows" in only(data, cash_rule(outflow_sign="negative")).metadata["equation"]


def test_cash_pnl_is_optional() -> None:
    data = summary(close=[105, 102])
    rule = cash_rule(cash_pnl=None)
    assert only(data, rule).passed
    assert rule.equation == "closing_cash = opening_cash + inflows - outflows"


def test_decimal_tolerance_and_exact_boundary() -> None:
    data = summary(
        open=[Decimal("100.00")] * 2,
        **{"in": [Decimal("0")] * 2},
        out=[Decimal("0")] * 2,
        pnl=[Decimal("0")] * 2,
        close=[Decimal("99.99"), Decimal("100.01")],
    )
    assert only(data, cash_rule(tolerance=Decimal("0.01"))).passed
    assert not only(data, cash_rule(tolerance=Decimal("0.009"))).passed


def test_whole_file_reconciles_without_group_columns() -> None:
    rule = cash_rule(group_by=[], currency=None)
    single = {key: values[:1] for key, values in summary().items()}
    result = only(single, rule)
    assert result.passed and result.message == "The file reconciles."
    assert result.metadata["currency"].startswith("not grouped by currency")


def test_summary_grain_rejects_conflicting_repeated_rows() -> None:
    data = summary(portfolio=["A", "A"], ccy=["USD", "USD"], open=[100, 101], close=[106, 106])
    failure = only(data, cash_rule()).metadata["failed_groups"][0]
    assert failure["reason"] == "inconsistent_rows"
    assert "more than one distinct value" in failure["detail"]


def transactions(**overrides: Any) -> dict[str, list[Any]]:
    data: dict[str, list[Any]] = {
        "portfolio": ["A", "A", "A"],
        "ccy": ["USD"] * 3,
        "when": ["2026-01-03", "2026-01-01", "2026-01-02"],
        "open": [104, 100, 107],
        "in": [0, 10, 0],
        "out": [4, 3, 3],
        "pnl": [0, 0, 0],
        "close": [100, 107, 104],
    }
    data.update(overrides)
    return data


def test_transactions_take_balances_by_ordering_column_not_row_order() -> None:
    rule = cash_rule(grain="transactions", order_by="when")
    result = only(transactions(), rule)
    assert result.passed, result.metadata
    assert result.metadata["aggregations"]["opening_cash"] == "first"
    assert result.metadata["order_by"] == "when"


def test_transactions_accept_dates_numbers_and_iso_text() -> None:
    rule = cash_rule(grain="transactions", order_by="when")
    as_dates = transactions(when=[date(2026, 1, 3), date(2026, 1, 1), date(2026, 1, 2)])
    as_numbers = transactions(when=[3, 1, 2])
    assert only(as_dates, rule).passed
    assert only(as_numbers, rule).passed


def test_transactions_reject_ambiguous_ordering_text() -> None:
    rule = cash_rule(grain="transactions", order_by="when")
    result = only(transactions(when=["1/10/2026", "1/9/2026", "1/11/2026"]), rule)
    assert result.outcome is Outcome.FAILED
    assert result.metadata["unusable_rows"][0] == {"row": 0, "invalid": ["order"]}


def test_ties_on_the_ordering_column_with_different_balances_fail() -> None:
    rule = cash_rule(grain="transactions", order_by="when")
    tied = transactions(when=["2026-01-02", "2026-01-01", "2026-01-02"])
    failure = only(tied, rule).metadata["failed_groups"][0]
    assert failure["reason"] == "inconsistent_rows"
    assert "tie on the ordering column" in failure["detail"]


def test_mixed_ordering_kinds_fail_the_group() -> None:
    rule = cash_rule(grain="transactions", order_by="when")
    failure = only(transactions(when=[3, "2026-01-01", 2]), rule).metadata["failed_groups"][0]
    assert "mixes numbers and dates" in failure["detail"]


def test_first_and_last_need_an_ordering_column() -> None:
    with pytest.raises(ValueError, match="need order_by"):
        cash_rule(grain="transactions")
    mapping = ColumnMapping(
        {"opening_cash": "o", "inflows": "i", "outflows": "x", "closing_cash": "c"},
        aggregations={
            "opening_cash": FieldAggregation.FIRST,
            "inflows": FieldAggregation.SUM,
            "outflows": FieldAggregation.SUM,
            "closing_cash": FieldAggregation.LAST,
        },
    )
    with pytest.raises(ValueError, match="need an ordering column"):
        fa.cash_reconciles(outflow_sign="positive", mapping=mapping)


def test_explicit_mapping_and_its_validation() -> None:
    mapping = ColumnMapping(
        {"opening_cash": "o", "inflows": "i", "outflows": "x", "closing_cash": "c"},
        group_keys=(GroupKey("portfolio", "p"),),
        row_key="id",
        aggregations={name: FieldAggregation.SUM for name in ("inflows", "outflows")}
        | {"opening_cash": FieldAggregation.REQUIRE_UNIQUE},
    )
    with pytest.raises(KeyError, match="closing_cash"):
        fa.cash_reconciles(outflow_sign="positive", mapping=mapping)
    with pytest.raises(ValueError, match="either mapping or column names"):
        fa.cash_reconciles(outflow_sign="positive", mapping=mapping, opening_cash="o")


@pytest.mark.parametrize(
    ("overrides", "error", "message"),
    [
        ({"outflow_sign": "plus"}, ValueError, "plus"),
        ({"closing_cash": None}, ValueError, "name the column for: closing_cash"),
        ({"null_policy": "ignore"}, ValueError, "changes the totals"),
        ({"max_violations": -1}, ValueError, "non-negative"),
        ({"group_by": "portfolio"}, TypeError, "list of column names"),
        ({"group_by": ["ccy"]}, ValueError, "group key columns must be unique"),
    ],
)
def test_invalid_configuration_is_rejected(
    overrides: dict[str, Any], error: type[Exception], message: str
) -> None:
    with pytest.raises(error, match=message):
        cash_rule(**overrides)


def test_blank_values_fail_or_skip_by_policy_and_list_rows_in_order() -> None:
    data = summary(**{"in": [None, 5]}, close=[106, "n/a"])
    failed = only(data, cash_rule())
    assert failed.outcome is Outcome.FAILED
    assert failed.metadata["unusable_rows"] == [
        {"row": 0, "blank": ["inflows"]},
        {"row": 1, "invalid": ["closing_cash"]},
    ]
    skipped = only(summary(**{"in": [None, 5]}), cash_rule(null_policy="skip"))
    assert skipped.outcome is Outcome.SKIPPED
    assert skipped.metadata["blank_rows"] == [{"row": 0, "blank": ["inflows"]}]


def test_row_key_labels_rows() -> None:
    data = summary(id=["cash-1", "cash-2"], close=[106, 1])
    result = only(data, cash_rule(row_key="id"))
    assert result.metadata["failed_groups"][0]["rows"] == ["cash-2"]


def test_blank_group_key_is_an_evaluation_error() -> None:
    result = only(summary(ccy=[None, "EUR"]), cash_rule())
    assert result.outcome is Outcome.ERROR
    assert "blank value in a grouping column" in result.message


def test_empty_file_is_skipped() -> None:
    result = only({column: [] for column in summary()}, cash_rule())
    assert result.outcome is Outcome.SKIPPED
    assert result.metadata["group_count"] == 0


def test_failed_group_list_is_capped() -> None:
    count = 30
    data = {
        "portfolio": [f"P{index}" for index in range(count)],
        "ccy": ["USD"] * count,
        "open": [0] * count,
        "in": [0] * count,
        "out": [0] * count,
        "pnl": [0] * count,
        "close": [1] * count,
    }
    metadata = only(data, cash_rule(max_violations=5)).metadata
    assert metadata["failed_group_count"] == 30
    assert len(metadata["failed_groups"]) == 5
    assert metadata["failed_groups_truncated"] is True


def test_cash_results_match_across_mappings_records_and_pandas() -> None:
    data = summary()
    records = [dict(zip(data, row, strict=True)) for row in zip(*data.values(), strict=True)]
    frame = pd.DataFrame(data)
    rule = cash_rule()
    results = [only(source, rule) for source in (data, records, frame)]
    assert results[0] == results[1] == results[2]


# NAV reconciliation ----------------------------------------------------------


def holdings(**overrides: Any) -> dict[str, list[Any]]:
    data: dict[str, list[Any]] = {
        "fund": ["F1", "F1", "F1", "F2"],
        "mv": [60, 50, -10, 7],
        "nav": [100, None, 100, 8],
    }
    data.update(overrides)
    return data


def nav_rule(**overrides: Any) -> Any:
    arguments: dict[str, Any] = {"market_value": "mv", "nav": "nav", "group_by": ["fund"]}
    arguments.update(overrides)
    return fa.nav_reconciles(**arguments)


def test_nav_sums_signed_market_values_and_allows_nav_on_some_rows() -> None:
    result = only(holdings(), nav_rule())
    assert result.metadata["equation"] == "sum(market_value) = nav"
    assert result.metadata["failed_groups"] == [
        {
            "group": {"fund": "F2"},
            "reason": "does_not_reconcile",
            "observed": 7,
            "expected": 8,
            "difference": -1,
            "row_count": 1,
            "rows": [3],
        }
    ]
    assert only(holdings(nav=[100, None, 100, 7]), nav_rule()).passed


def test_nav_must_agree_within_a_group_and_be_given() -> None:
    conflicting = only(holdings(nav=[100, 99, None, 7]), nav_rule()).metadata["failed_groups"]
    assert conflicting[0]["reason"] == "inconsistent_rows"
    missing = only(holdings(nav=[None, None, None, 7]), nav_rule()).metadata["failed_groups"]
    assert missing[0]["reason"] == "no_reported_nav"


def test_blank_market_value_is_not_treated_as_zero() -> None:
    result = only(holdings(mv=[60, None, -10, 7]), nav_rule())
    assert result.outcome is Outcome.FAILED
    assert result.metadata["unusable_rows"] == [{"row": 1, "blank": ["market_value"]}]


def test_nav_reconciles_from_csv_with_exact_decimals() -> None:
    table = parse_csv("fund,mv,nav\nF1,0.1,1.0\nF1,0.2,\nF1,0.7,1.0\n")
    assert only(table, nav_rule(tolerance=0)).passed
    failure = only(parse_csv("fund,mv,nav\nF1,0.1,1\nF1,0.2,\n"), nav_rule())
    assert failure.metadata["failed_groups"][0]["rows"] == [2, 3]


def test_nav_currency_grouping() -> None:
    data = holdings(ccy=["USD", "USD", "EUR", "EUR"], nav=[110, 110, -3, 4])
    result = only(data, nav_rule(currency="ccy"))
    assert result.metadata["group_keys"] == ["fund", "currency"]
    assert result.metadata["failed_group_count"] == 2


def test_nav_rule_guards_its_aggregations() -> None:
    from finassert.rules import NavReconciliationRule

    mapping = ColumnMapping(
        {"market_value": "mv", "nav": "nav"},
        aggregations={"market_value": FieldAggregation.LAST, "nav": FieldAggregation.SUM},
    )
    with pytest.raises(ValueError, match="market_value must be summed"):
        NavReconciliationRule(mapping=mapping)
    assert Tolerance(absolute=0).to_dict() == nav_rule().tolerance.to_dict()
    assert OutflowSign("negative") is OutflowSign.NEGATIVE


def test_currency_note_follows_an_explicit_mapping() -> None:
    mapping = ColumnMapping(
        {"opening_cash": "open", "inflows": "in", "outflows": "out", "closing_cash": "close"},
        group_keys=(GroupKey("currency", "ccy"),),
        aggregations={
            name: FieldAggregation.REQUIRE_UNIQUE
            for name in ("opening_cash", "inflows", "outflows", "closing_cash")
        },
    )
    rule = fa.cash_reconciles(outflow_sign="positive", mapping=mapping)
    assert only(summary(), rule).metadata["currency"] == (
        "reconciled separately for each value of 'ccy'"
    )


def test_ordering_column_is_ignored_unless_first_or_last_is_used() -> None:
    mapping = ColumnMapping(
        {"opening_cash": "open", "inflows": "in", "outflows": "out", "closing_cash": "close"},
        group_keys=(GroupKey("portfolio", "portfolio"),),
        aggregations={
            name: FieldAggregation.REQUIRE_UNIQUE
            for name in ("opening_cash", "inflows", "outflows", "closing_cash")
        },
        order_key="when",
    )
    rule = fa.cash_reconciles(outflow_sign="positive", mapping=mapping)
    data = summary(close=[105, 102], when=["not a date", None])
    assert only(data, rule).passed
    with pytest.raises(ValueError, match="only used with grain='transactions'"):
        cash_rule(order_by="when")


def test_date_ties_explain_the_fix() -> None:
    rule = cash_rule(grain="transactions", order_by="when")
    tied = transactions(when=["2026-01-02", "2026-01-01", "2026-01-02"])
    detail = only(tied, rule).metadata["failed_groups"][0]["detail"]
    assert "unique within each group" in detail and "2026-01-02" in detail


def test_skip_never_hides_non_numeric_values() -> None:
    data = summary(**{"in": [None, "abc"]})
    result = only(data, cash_rule(null_policy="skip"))
    assert result.outcome is Outcome.FAILED
    assert result.metadata["unusable_rows"] == [
        {"row": 0, "blank": ["inflows"]},
        {"row": 1, "invalid": ["inflows"]},
    ]
    assert only(summary(**{"in": [None, 5]}), cash_rule(null_policy="skip")).outcome is (
        Outcome.SKIPPED
    )


def test_text_blanks_from_json_or_pandas_count_as_blank() -> None:
    data = holdings(nav=[100, " ", 100, 8])
    assert only(data, nav_rule()).metadata["failed_group_count"] == 1  # only F2 breaks
    skipped = only(holdings(mv=[60, " ", -10, 7]), nav_rule(null_policy="skip"))
    assert skipped.outcome is Outcome.SKIPPED
    errored = only(holdings(fund=["F1", " ", "F1", "F2"]), nav_rule())
    assert errored.outcome is Outcome.ERROR
    assert "blank value in a grouping column" in errored.message
