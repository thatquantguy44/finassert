from __future__ import annotations

import copy
from collections.abc import Callable
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from openpyxl import Workbook

import finassert as fa
from finassert.adapters import PandasDataFrameAdapter
from finassert.adapters._column import extract_column, extract_columns
from finassert.core.exceptions import InvalidDataError
from finassert.loaders import TableSource
from finassert.workbook import WorkbookSource, read_workbook

Builder = Callable[[dict[str, list[Any]]], Any]


def workbook_source(columns: dict[str, list[Any]], path: Path) -> WorkbookSource:
    book = Workbook()
    sheet = book.active
    sheet.title = "Data"
    sheet.append(list(columns))
    for row in zip(*columns.values(), strict=True):
        sheet.append(list(row))
    book.save(path)
    book.close()
    return read_workbook(path, sheet="Data")


@pytest.fixture(params=["mapping", "records", "pandas", "pandas_adapter", "table", "workbook"])
def source(request: pytest.FixtureRequest, tmp_path: Path) -> Builder:
    def build(columns: dict[str, list[Any]]) -> Any:
        values = copy.deepcopy(columns)
        size = len(next(iter(values.values())))
        if request.param == "mapping":
            return values
        if request.param == "records":
            return [
                dict(zip(values, row, strict=True)) for row in zip(*values.values(), strict=True)
            ]
        if request.param == "pandas":
            return pd.DataFrame(values)
        if request.param == "pandas_adapter":
            return PandasDataFrameAdapter(pd.DataFrame(values))
        if request.param == "table":
            return TableSource(values, list(range(2, size + 2)))
        return workbook_source(values, tmp_path / "shared.xlsx")

    return build


def test_pass_fail_decimal_and_non_mutation(source: Builder) -> None:
    data = source({"weight": [Decimal("0.1"), Decimal("0.9")], "v": [1, -1]})
    before = [extract_column(data, name) for name in ("weight", "v")]
    report = fa.check(data, [fa.weights_sum_to_one(tolerance=0), fa.non_negative(column="v")])
    assert [item.outcome for item in report.results] == [fa.Outcome.PASSED, fa.Outcome.FAILED]
    assert report.results[0].observed == Decimal(1)
    assert [extract_column(data, name) for name in ("weight", "v")] == before


@pytest.mark.parametrize(
    "policy, outcome", [("fail", "failed"), ("ignore", "passed"), ("skip", "skipped")]
)
def test_null_policy(source: Builder, policy: str, outcome: str) -> None:
    # The ID keeps the blank weight row present in workbook input.
    data = source({"id": ["a", "b"], "weight": [None, Decimal(1)]})
    result = fa.check(data, [fa.weights_sum_to_one(null_policy=policy)]).results[0]
    assert result.outcome.value == outcome


def test_empty_population(source: Builder) -> None:
    data = source({"weight": [], "v": []})
    results = fa.check(data, [fa.weights_sum_to_one(), fa.non_negative(column="v")]).results
    assert [item.outcome for item in results] == [fa.Outcome.FAILED, fa.Outcome.PASSED]


def test_missing_column_is_error(source: Builder) -> None:
    result = fa.check(source({"v": [1]}), [fa.non_negative(column="absent")]).results[0]
    assert result.outcome is fa.Outcome.ERROR


def test_invalid_value_after_ignored_null_keeps_native_row(source: Builder) -> None:
    data = source({"id": ["blank", "bad", "good"], "weight": [None, "bad", 1]})
    _, labels = extract_column(data, "weight")
    result = fa.check(data, [fa.weights_sum_to_one(null_policy="ignore")]).results[0]
    assert result.outcome is fa.Outcome.FAILED
    assert result.metadata["invalid_rows"] == [labels[1]]


def test_duplicate_explicit_labels_and_aligned_columns(source: Builder) -> None:
    data = source({"id": ["same", "same"], "a": [1, 2], "b": [3, 4]})
    columns, labels = extract_columns(data, ["a", "b"], row_key="id")
    assert labels == ["same", "same"]
    assert columns == {"a": [1, 2], "b": [3, 4], "id": ["same", "same"]}


def test_group_failure_has_identity_and_cap(source: Builder) -> None:
    data = source({"book": ["A", "B", "C"], "weight": [Decimal("0.5")] * 3})
    result = fa.check(data, [fa.weights_sum_to_one(group_by=["book"], max_violations=1)]).results[0]
    assert result.metadata["failed_group_count"] == 3
    assert result.metadata["failed_groups"][0]["group"] == {"book": "A"}
    assert len(result.metadata["failed_groups"]) == 1
    assert result.metadata["failed_groups_truncated"]


def test_cash_sign_date_currency_and_materiality_contract(source: Builder) -> None:
    columns = {
        "id": ["usd-today", "usd-next", "eur-today", "eur-next"],
        "book": ["A"] * 4,
        "asof": ["2026-11-13", "2026-11-14"] * 2,
        "ccy": ["USD", "USD", "EUR", "EUR"],
        "open": [Decimal("100")] * 4,
        "in": [Decimal("10")] * 4,
        "out": [Decimal("5")] * 4,
        "close": [Decimal("105.01")] * 4,
    }

    def rule(sign: str) -> fa.Rule:
        return fa.cash_reconciles(
            outflow_sign=sign,
            opening_cash="open",
            inflows="in",
            outflows="out",
            closing_cash="close",
            group_by=["book", "asof"],
            currency="ccy",
            row_key="id",
            tolerance=Decimal("0.01"),
        )

    assert fa.check(source(columns), [rule("positive")]).passed
    negative = {**columns, "out": [Decimal("-5")] * 4}
    assert fa.check(source(negative), [rule("negative")]).passed
    broken = {**columns, "close": [Decimal("105.01")] * 3 + [Decimal("105.02")]}
    result = fa.check(source(broken), [rule("positive")]).results[0]
    assert result.metadata["failed_group_count"] == 1
    observation = result.diagnostics[0].observations[0]
    assert observation["group"] == {"book": "A", "asof": "2026-11-14", "currency": "EUR"}
    assert observation["rows"] == ["eur-next"]


def test_nav_signed_liabilities_and_currency_partitioning(source: Builder) -> None:
    columns = {
        "id": ["usd-asset", "usd-liability", "eur-asset", "eur-liability"],
        "book": ["A"] * 4,
        "ccy": ["USD", "USD", "EUR", "EUR"],
        "mv": [Decimal("100"), Decimal("-20"), Decimal("200"), Decimal("-20")],
        "nav": [Decimal("80"), None, Decimal("180"), None],
    }
    rule = fa.nav_reconciles(
        market_value="mv", nav="nav", group_by=["book"], currency="ccy", row_key="id"
    )
    assert fa.check(source(columns), [rule]).passed
    # Equal and opposite breaks remain visible in separate currencies.
    broken = {**columns, "nav": [Decimal("81"), None, Decimal("179"), None]}
    result = fa.check(source(broken), [rule]).results[0]
    assert result.metadata["failed_group_count"] == 2
    assert [item["group"]["currency"] for item in result.diagnostics[0].observations] == [
        "USD",
        "EUR",
    ]


@pytest.mark.parametrize("values,labels", [([1], []), ([], [0]), ([1], [0, 1])])
def test_malformed_column_source_cannot_pass(values: list[Any], labels: list[Any]) -> None:
    class BrokenSource:
        def column(self, name: str) -> tuple[list[Any], list[Any]]:
            return values, labels

    for rule in [fa.weights_sum_to_one(), fa.non_negative(column="v")]:
        result = fa.check(BrokenSource(), [rule]).results[0]
        assert result.outcome is fa.Outcome.ERROR
        assert "row labels" in result.message


def test_workbook_source_rejects_malformed_construction() -> None:
    with pytest.raises(InvalidDataError, match="row count"):
        WorkbookSource({"v": [1]}, [])


@given(
    st.lists(
        st.decimals(min_value=-10, max_value=10, places=4, allow_nan=False, allow_infinity=False),
        min_size=1,
        max_size=12,
    )
)
@settings(max_examples=25, deadline=None)
def test_generated_workbook_pandas_mapping_equivalence(values: list[Decimal]) -> None:
    # Exact four-place decimals fit the Excel numeric representation in this range.
    # Each example owns its directory; no function-scoped Hypothesis fixture is reused.
    columns = {"id": list(range(len(values))), "v": values}
    with TemporaryDirectory(prefix="finassert-contract-") as directory:
        workbook = workbook_source(columns, Path(directory) / "data.xlsx")
        sources = [columns, pd.DataFrame(columns), workbook]
        results = [fa.check(data, [fa.non_negative(column="v")]).results[0] for data in sources]
        assert len({item.outcome for item in results}) == 1
        assert len({item.metadata["violation_count"] for item in results}) == 1
        _, labels = extract_columns(workbook, ["v"], row_key="id")
        assert labels == list(range(len(values)))
