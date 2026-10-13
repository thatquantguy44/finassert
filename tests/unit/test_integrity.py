from decimal import Decimal
from typing import Any

import pandas as pd
import pytest

import finassert as fa
from finassert.core.models import Outcome
from finassert.loaders import parse_csv


def only(data: Any, rule: Any) -> fa.ValidationResult:
    return fa.check(data, [rule]).results[0]


# Grouped weights -------------------------------------------------------------


def portfolios(**overrides: Any) -> dict[str, list[Any]]:
    data: dict[str, list[Any]] = {
        "portfolio": ["P1", "P1", "P2", "P2", "P3"],
        "w": [0.6, 0.4, 0.5, 0.3, 1.0],
    }
    data.update(overrides)
    return data


def grouped(**overrides: Any) -> Any:
    arguments: dict[str, Any] = {"column": "w", "group_by": ["portfolio"], "tolerance": 1e-9}
    arguments.update(overrides)
    return fa.weights_sum_to_one(**arguments)


def test_each_portfolio_must_add_up_to_one() -> None:
    result = only(portfolios(), grouped())

    assert result.outcome is Outcome.FAILED
    assert result.message == "1 of 3 group(s) do not add up to 1."
    assert result.metadata["equation"] == "sum(weight) = 1"
    failure = result.metadata["failed_groups"][0]
    assert failure["group"] == {"portfolio": "P2"}
    assert failure["reason"] == "weights_do_not_sum_to_one"
    assert failure["observed"] == pytest.approx(0.8)
    assert failure["rows"] == [2, 3]


def test_grouped_weights_use_exact_decimals_and_two_group_keys() -> None:
    table = parse_csv(
        "portfolio,date,w\nP1,2026-01-01,0.1\nP1,2026-01-01,0.2\nP1,2026-01-01,0.7\n"
        "P1,2026-01-02,1.0\n"
    )
    rule = fa.weights_sum_to_one(column="w", group_by=["portfolio", "date"], tolerance=0)
    result = only(table, rule)
    assert result.passed and result.metadata["group_count"] == 2
    assert result.metadata["group_keys"] == ["portfolio", "date"]


def test_grouping_does_not_change_ungrouped_results() -> None:
    data = {"w": [Decimal("0.5"), Decimal("0.5")]}
    result = only(data, fa.weights_sum_to_one(column="w"))
    assert result.observed == Decimal("1.0") and result.expected == Decimal(1)
    assert "group_by" not in result.metadata


def test_blank_weights_follow_the_null_policy_per_group() -> None:
    data = portfolios(w=[0.6, None, 0.5, 0.5, 1.0])
    failed = only(data, grouped())
    assert failed.outcome is Outcome.FAILED
    assert failed.metadata["unusable_rows"] == [{"row": 1, "blank": ["weight"]}]
    skipped = only(data, grouped(null_policy="skip"))
    assert skipped.outcome is Outcome.SKIPPED
    ignored = only(data, grouped(null_policy="ignore"))
    assert ignored.metadata["failed_groups"][0]["group"] == {"portfolio": "P1"}
    all_blank = only(portfolios(w=[None, None, 0.5, 0.5, 1.0]), grouped(null_policy="ignore"))
    assert all_blank.metadata["failed_groups"][0]["reason"] == "no_weights"


def test_non_numeric_weights_and_blank_group_keys() -> None:
    result = only(portfolios(w=[0.6, "n/a", 0.5, 0.5, 1.0]), grouped())
    assert result.metadata["unusable_rows"] == [{"row": 1, "invalid": ["weight"]}]
    errored = only(portfolios(portfolio=["P1", None, "P2", "P2", "P3"]), grouped())
    assert errored.outcome is Outcome.ERROR


def test_grouped_weights_match_across_inputs_and_cap_failures() -> None:
    data = portfolios()
    records = [dict(zip(data, row, strict=True)) for row in zip(*data.values(), strict=True)]
    assert only(data, grouped()) == only(records, grouped()) == only(pd.DataFrame(data), grouped())
    many = {"portfolio": [f"P{i}" for i in range(30)], "w": [0.5] * 30}
    capped = only(many, grouped(max_violations=3)).metadata
    assert capped["failed_group_count"] == 30 and len(capped["failed_groups"]) == 3
    assert capped["failed_groups_truncated"] is True


@pytest.mark.parametrize(
    ("overrides", "error", "message"),
    [
        ({"group_by": "portfolio"}, TypeError, "list of column names"),
        ({"group_by": ["w"]}, ValueError, "must not include the weight column"),
        ({"group_by": ["portfolio", "portfolio"]}, ValueError, "group key"),
        ({"max_violations": -1}, ValueError, "non-negative"),
    ],
)
def test_grouped_weights_reject_bad_configuration(
    overrides: dict[str, Any], error: type[Exception], message: str
) -> None:
    with pytest.raises(error, match=message):
        grouped(**overrides)


# No duplicates ---------------------------------------------------------------


def holdings(**overrides: Any) -> dict[str, list[Any]]:
    data: dict[str, list[Any]] = {
        "portfolio": ["P1", "P1", "P2", "P2"],
        "ticker": ["AAA", "BBB", "AAA", "AAA"],
    }
    data.update(overrides)
    return data


def test_duplicates_are_found_per_combination_with_their_rows() -> None:
    result = only(holdings(), fa.no_duplicates(columns=["portfolio", "ticker"]))
    assert result.outcome is Outcome.FAILED
    assert result.message == "1 portfolio/ticker combination(s) appear on more than one row."
    assert result.metadata["duplicates"] == [
        {"key": {"portfolio": "P2", "ticker": "AAA"}, "count": 2, "rows": [2, 3]}
    ]
    assert result.observed == 1 and result.expected == 0
    assert (
        only(holdings(), fa.no_duplicates(columns=["ticker"])).metadata["duplicate_row_count"] == 3
    )


def test_unique_keys_pass() -> None:
    result = only(
        holdings(ticker=["AAA", "BBB", "AAA", "BBB"]),
        fa.no_duplicates(columns=["portfolio", "ticker"]),
    )
    assert result.passed
    assert result.message == "All 4 row(s) have a unique portfolio/ticker."


def test_comparison_is_exact_and_numbers_match_across_types() -> None:
    assert only(
        holdings(ticker=["AAA", "aaa", "AAA ", "BBB"]), fa.no_duplicates(columns=["ticker"])
    ).passed
    numbers = {"id": [1, Decimal("1.0"), 2]}
    assert only(numbers, fa.no_duplicates(columns=["id"])).metadata["duplicate_key_count"] == 1


def test_blank_keys_follow_the_null_policy() -> None:
    data = holdings(ticker=["AAA", None, "AAA", "  "])
    failed = only(data, fa.no_duplicates(columns=["ticker"]))
    assert failed.outcome is Outcome.FAILED
    assert failed.metadata["blank_rows"] == [1, 3]
    assert "2 row(s) have a blank key" in failed.message
    ignored = only(data, fa.no_duplicates(columns=["ticker"], null_policy="ignore"))
    assert ignored.metadata["duplicate_key_count"] == 1
    assert "blank_rows" not in ignored.metadata and ignored.metadata["blank_row_count"] == 2
    assert only(data, fa.no_duplicates(columns=["ticker"], null_policy="skip")).outcome is (
        Outcome.SKIPPED
    )


def test_unhashable_values_are_reported_not_crashed() -> None:
    result = only({"k": [[1], [1], "a"]}, fa.no_duplicates(columns=["k"]))
    assert result.outcome is Outcome.FAILED
    assert result.metadata["unusable_rows"] == [0, 1]


def test_duplicates_empty_missing_column_and_cap() -> None:
    assert only({"k": []}, fa.no_duplicates(columns=["k"])).outcome is Outcome.SKIPPED
    assert only({"x": [1]}, fa.no_duplicates(columns=["k"])).outcome is Outcome.ERROR
    capped = only(
        {"k": [i // 2 for i in range(40)]}, fa.no_duplicates(columns=["k"], max_violations=4)
    )
    assert capped.metadata["duplicate_key_count"] == 20
    assert len(capped.metadata["duplicates"]) == 4 and capped.metadata["duplicates_truncated"]


def test_duplicates_report_csv_row_numbers() -> None:
    table = parse_csv("ticker,qty\nAAA,1\nBBB,2\nAAA,3\n")
    assert only(table, fa.no_duplicates(columns=["ticker"])).metadata["duplicates"][0]["rows"] == [
        2,
        4,
    ]


# Required fields -------------------------------------------------------------


def test_blank_cells_are_listed_per_column() -> None:
    data = {"ticker": ["A", "", "C", None], "qty": [1, 0, None, 4], "px": [1, 2, 3, 4]}
    result = only(data, fa.required_fields(columns=["ticker", "qty", "px"]))

    assert result.outcome is Outcome.FAILED
    assert result.message == "3 required cell(s) are blank: ticker (2), qty (1)."
    assert result.metadata["blank_cells"] == [
        {"column": "ticker", "blank_count": 2, "rows": [1, 3], "rows_truncated": False},
        {"column": "qty", "blank_count": 1, "rows": [2], "rows_truncated": False},
    ]
    assert result.observed == 3


def test_zero_and_false_are_values_and_complete_files_pass() -> None:
    data = {"qty": [0, 0.0, Decimal(0), False], "flag": ["x", "y", "z", "w"]}
    result = only(data, fa.required_fields(columns=["qty", "flag"]))
    assert result.passed and result.metadata["blank_cell_count"] == 0


def test_required_fields_edge_cases() -> None:
    assert only({"a": []}, fa.required_fields(columns=["a"])).outcome is Outcome.SKIPPED
    assert only({"a": [1]}, fa.required_fields(columns=["b"])).outcome is Outcome.ERROR
    capped = only({"a": [None] * 30}, fa.required_fields(columns=["a"], max_violations=5))
    assert len(capped.metadata["blank_cells"][0]["rows"]) == 5
    assert capped.metadata["blank_cells"][0]["rows_truncated"] is True
    assert capped.metadata["blank_cell_count"] == 30
    frame = pd.DataFrame({"a": [1.0, float("nan")], "b": ["x", " "]})
    assert only(frame, fa.required_fields(columns=["a", "b"])).metadata["blank_cell_count"] == 2


@pytest.mark.parametrize("factory", [fa.no_duplicates, fa.required_fields])
@pytest.mark.parametrize(
    ("columns", "error", "message"),
    [
        ("ticker", TypeError, "list of column names"),
        ([], ValueError, "at least one column"),
        (["a", "a"], ValueError, "more than once"),
        (["a", " "], ValueError, "non-empty text"),
    ],
)
def test_integrity_rules_reject_bad_columns(
    factory: Any, columns: Any, error: type[Exception], message: str
) -> None:
    with pytest.raises(error, match=message):
        factory(columns=columns)
    with pytest.raises(ValueError, match="non-negative"):
        factory(columns=["a"], max_violations=-1)
