from datetime import date
from decimal import Decimal
from typing import Any

import pytest

import finassert as fa
from finassert import excel
from finassert.core.exceptions import InvalidDataError
from finassert.excel import read_range, results_table
from finassert.policy import parse_policy
from finassert.reporting import build_artifact


def payload(values: list[list[Any]], **extra: Any) -> dict[str, Any]:
    return {"values": values, **extra}


def column(table: Any, name: str) -> list[Any]:
    return table.column(name)[0]


def test_the_first_row_is_the_header_and_labels_are_the_sheets_row_numbers() -> None:
    table = read_range(payload([["ticker", "weight"], ["AAA", 0.4], ["BBB", 0.6]], firstRow=5))

    assert table.column_names == ("ticker", "weight")
    assert table.column("weight") == ([Decimal("0.4"), Decimal("0.6")], [6, 7])
    assert column(table, "ticker") == ["AAA", "BBB"]


def test_numbers_keep_their_shortest_decimal_text_and_whole_numbers_become_integers() -> None:
    table = read_range(
        payload(
            [["x"], [0.1], [5.0], [3], [-2.50], [1e21], [123456789012345.0], [1.0000000000000002]]
        )
    )

    values = column(table, "x")
    assert values[:3] == [Decimal("0.1"), 5, 3]
    assert isinstance(values[1], int) and isinstance(values[2], int)
    assert values[3] == Decimal("-2.5")
    assert values[4] == Decimal("1e21") and isinstance(values[4], Decimal)
    assert values[5] == 123456789012345 and isinstance(values[5], int)
    assert values[6] == Decimal("1.0000000000000002")


def test_a_decimal_read_from_excel_adds_up_exactly() -> None:
    table = read_range(payload([["w"], [0.1], [0.2], [0.7]]))

    assert fa.check(table, [fa.weights_sum_to_one(column="w", tolerance=0)]).passed


def test_date_formats_become_dates_and_other_numbers_do_not() -> None:
    table = read_range(
        payload(
            [["when", "amount"], [46023, 46023], [46024, 5]],
            numberFormats=[["General", "General"], ["yyyy-mm-dd", "#,##0"], ["d-mmm-yy", "0.00"]],
        )
    )

    assert column(table, "when") == [date(2026, 1, 1), date(2026, 1, 2)]
    assert column(table, "amount") == [46023, 5]


def test_the_1904_date_system_is_honoured() -> None:
    table = read_range(
        payload(
            [["when"], [44561]],
            numberFormats=[["General"], ["yyyy-mm-dd"]],
            date1904=True,
        )
    )

    assert column(table, "when") == [date(2026, 1, 1)]


def test_percentages_are_never_rescaled() -> None:
    table = read_range(payload([["w"], [0.4]], numberFormats=[["General"], ["0.0%"]]))

    assert column(table, "w") == [Decimal("0.4")]


def test_text_numbers_blanks_booleans_and_empty_rows() -> None:
    table = read_range(
        payload(
            [["a", "b"], ["12", "x"], ["  ", ""], ["", None], ["1.50", True]],
            valueTypes=[
                ["String"] * 2,
                ["String"] * 2,
                ["String", "Empty"],
                ["Empty"] * 2,
                ["String"] * 2,
            ],
            firstRow=2,
        )
    )

    assert column(table, "a") == [12, None, Decimal("1.50")]
    assert column(table, "b") == ["x", None, True]
    assert table.column("a")[1] == [3, 4, 6]  # the fully blank row 5 is skipped, labels kept


def test_excel_errors_are_invalid_values_never_blank_or_zero() -> None:
    table = read_range(
        payload(
            [["name", "w"], ["A", 0.5], ["B", "#N/A"], ["C", "#DIV/0!"], ["D", 0.5]],
            valueTypes=[
                ["String"] * 2,
                ["String", "Double"],
                ["String", "Error"],
                ["String", "Error"],
                ["String", "Double"],
            ],
        )
    )

    assert column(table, "w") == [Decimal("0.5"), "#N/A", "#DIV/0!", Decimal("0.5")]
    assert len(table.notes) == 1
    assert "2 cell(s) show Excel errors" in table.notes[0]
    assert "#N/A in column 'w', row 3" in table.notes[0]
    result = fa.check(table, [fa.non_negative(column="w")]).results[0]
    assert result.outcome.value == "failed"
    assert result.metadata["invalid_rows"] == [3, 4]


def test_error_text_is_recognised_without_value_types() -> None:
    table = read_range(payload([["w"], ["#REF!"]]))

    assert column(table, "w") == ["#REF!"]
    assert table.notes


def test_a_date_format_on_a_non_date_value_is_reported() -> None:
    table = read_range(payload([["d"], [-5]], numberFormats=[["General"], ["yyyy-mm-dd"]]))

    assert column(table, "d") == [-5]
    assert "not a valid date" in table.notes[0]


@pytest.mark.parametrize(
    ("values", "message"),
    [
        ([], "first row holds the column names"),
        ("abc", "first row holds the column names"),
        ([[]], "not a rectangle"),
        ([["a", "b"], ["x"]], "not a rectangle"),
        ([["a", ""], [1, 2]], "header of column B is blank"),
        ([["a", None], [1, 2]], "header of column B is blank"),
        ([["a", "#REF!"], [1, 2]], "shows the Excel error #REF!"),
    ],
)
def test_a_bad_selection_is_explained(values: Any, message: str) -> None:
    with pytest.raises(InvalidDataError, match=message):
        read_range(payload(values))


def test_a_repeated_header_is_rejected_like_a_csv() -> None:
    with pytest.raises(InvalidDataError, match="more than once"):
        read_range(payload([["a", "a"], [1, 2]]))


def test_numeric_and_date_headers_become_text() -> None:
    table = read_range(
        payload([[2025, 46023], [1, 2]], numberFormats=[["0", "yyyy-mm-dd"], ["0", "0"]])
    )

    assert table.column_names == ("2025", "2026-01-01")


@pytest.mark.parametrize(
    "extra",
    [{"numberFormats": [["a"]]}, {"valueTypes": [["a", "b"]]}, {"firstRow": 0}, {"firstRow": "2"}],
)
def test_inconsistent_extras_are_rejected(extra: dict[str, Any]) -> None:
    with pytest.raises(InvalidDataError):
        read_range(payload([["a"], [1]], **extra))


def test_a_huge_selection_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(excel, "MAX_CELLS", 3)

    with pytest.raises(InvalidDataError, match="select at most 3"):
        read_range(payload([["a", "b"], [1, 2]]))


def test_non_finite_numbers_are_refused() -> None:
    with pytest.raises(InvalidDataError, match="not a number"):
        read_range(payload([["a"], [float("inf")]]))


# Results sheet ---------------------------------------------------------------------


def artifact_for(severity: str = "error") -> dict[str, Any]:
    policy = parse_policy(
        {
            "version": 1,
            "rules": [
                {"rule": "non_negative", "column": "w", "severity": severity},
                {"rule": "weights_sum_to_one", "column": "w", "tolerance": 1},
            ],
        }
    )
    table = read_range(payload([["w"], [0.5], [-0.25], [0.75]], firstRow=3))
    return build_artifact(policy.check(table), policy=policy)


def test_the_results_sheet_lists_each_check_and_each_problem_row() -> None:
    rows = results_table(artifact_for())

    assert rows[0] == ["Check", "Result", "Severity", "Row", "Details"]
    assert rows[1][:3] == ["No negative values", "Failed", "error"]
    assert rows[2][:4] == ["No negative values", "", "", 5]
    assert "value: -0.25" in rows[2][4]
    assert [row[1] for row in rows[1:] if row[1]] == ["Failed", "Passed"]


def test_a_check_that_only_warns_is_labelled_a_warning() -> None:
    rows = results_table(artifact_for("warning"))

    assert rows[1][1] == "Warning"


def test_results_cells_that_could_be_formulas_are_kept_as_text() -> None:
    artifact = {
        "report": {
            "results": [
                {
                    "rule_name": "=HYPERLINK(1)",
                    "outcome": "error",
                    "severity": "error",
                    "message": "+cmd|calc",
                    "metadata": {},
                }
            ]
        }
    }

    (_, row) = results_table(artifact)

    assert row == ["'=HYPERLINK(1)", "Could not run", "error", "", "'+cmd|calc"]


def test_detail_rows_are_capped() -> None:
    artifact = {
        "report": {
            "results": [
                {
                    "rule_name": "x",
                    "outcome": "failed",
                    "severity": "error",
                    "message": "m",
                    "metadata": {"violations": [{"row": n, "value": n} for n in range(1000)]},
                }
            ]
        }
    }

    assert len(results_table(artifact)) == 1 + 1 + excel._MAX_DETAIL_ROWS


def test_row_labels_in_lists_and_groups_are_used() -> None:
    artifact = {
        "report": {
            "results": [
                {
                    "rule_name": "x",
                    "outcome": "failed",
                    "severity": "error",
                    "message": "m",
                    "metadata": {
                        "invalid_rows": [7, 9],
                        "failed_groups": [{"group": {"p": "A"}, "rows": [4, 5], "observed": 1}],
                    },
                }
            ]
        }
    }

    rows = results_table(artifact)

    assert [row[3] for row in rows[2:]] == [7, 9, 4]
    assert rows[4][4] == "group: p A; observed: 1"
