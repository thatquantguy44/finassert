from decimal import Decimal
from pathlib import Path

import pytest

import finassert as fa
from finassert.core.exceptions import ColumnNotFoundError, InvalidDataError
from finassert.loaders import TableSource, load_input, parse_cell, parse_csv, parse_json


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("", None),
        ("   ", None),
        ("42", 42),
        ("-7", -7),
        ("0.40", Decimal("0.40")),
        (" 1.5 ", Decimal("1.5")),
        (".5", Decimal(".5")),
        ("1e-3", Decimal("1e-3")),
        ("1,000", "1,000"),
        ("40%", "40%"),
        ("$5", "$5"),
        ("NaN", "NaN"),
        ("inf", "inf"),
        ("AAA", "AAA"),
    ],
)
def test_parse_cell_never_rescales(text: str, expected: object) -> None:
    value = parse_cell(text)
    assert value == expected
    assert type(value) is type(expected)


def test_csv_rows_are_labelled_like_a_spreadsheet() -> None:
    source = parse_csv('﻿ticker,weight\nAAA,0.4\n"B, Inc.",0.6\n\n')

    assert source.column_names == ("ticker", "weight")
    assert source.row_count == 2
    assert source.column("ticker") == (["AAA", "B, Inc."], [2, 3])
    assert source.column("weight") == ([Decimal("0.4"), Decimal("0.6")], [2, 3])
    assert source.preview(1) == [{"ticker": "AAA", "weight": Decimal("0.4")}]


def test_csv_decimals_sum_exactly() -> None:
    source = parse_csv("weight\n0.1\n0.2\n0.7\n")
    result = fa.check(source, [fa.weights_sum_to_one(tolerance=0)]).results[0]
    assert result.passed
    assert result.observed == Decimal("1.0")


def test_csv_text_values_fail_rather_than_convert() -> None:
    source = parse_csv("weight\n40%\n60%\n")
    result = fa.check(source, [fa.weights_sum_to_one()]).results[0]
    assert not result.passed
    assert result.metadata["invalid_rows"] == [2, 3]


def test_csv_blank_cells_are_missing_values() -> None:
    source = parse_csv("market_value\n10\n\n5\n")
    # Fully blank lines are skipped; a blank cell in a wider row is missing.
    assert source.row_count == 2
    wider = parse_csv("a,b\n1,\n")
    result = fa.check(wider, [fa.non_negative(column="b")]).results[0]
    assert result.metadata["invalid_rows"] == [2]


def test_missing_column_lists_alternatives() -> None:
    source = parse_csv("Weight,mv\n1,2\n")
    with pytest.raises(ColumnNotFoundError) as caught:
        source.column("weight")
    assert str(caught.value) == (
        "column 'weight' was not found; available columns: 'Weight', 'mv'; did you mean 'Weight'?"
    )


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("", "empty"),
        ("a,a\n1,2\n", "appears more than once"),
        ("a,\n1,2\n", "column 2 has no header"),
        ("a,b\n1\n", "row 2 has 1 cell"),
        ('a\n"unterminated\n', "could not be read"),
    ],
)
def test_malformed_csv_is_rejected(text: str, message: str) -> None:
    with pytest.raises(InvalidDataError, match=message):
        parse_csv(text)


def test_table_source_rejects_misaligned_columns() -> None:
    with pytest.raises(InvalidDataError):
        TableSource({"a": [1, 2]}, [2])


def test_parse_json_accepts_columns_and_records_with_exact_decimals() -> None:
    assert parse_json('{"weight": [0.1, 0.9]}') == {"weight": [Decimal("0.1"), Decimal("0.9")]}
    assert parse_json('[{"weight": 1}]') == [{"weight": 1}]
    with pytest.raises(InvalidDataError, match="object of columns"):
        parse_json("[1, 2]")
    with pytest.raises(InvalidDataError, match="not valid JSON"):
        parse_json("{")


def test_load_input_infers_format(tmp_path: Path) -> None:
    csv_path = tmp_path / "positions file.CSV"
    csv_path.write_text("weight\n1\n", encoding="utf-8")
    json_path = tmp_path / "positions.json"
    json_path.write_text('{"weight": [1]}', encoding="utf-8")

    assert isinstance(load_input(csv_path), TableSource)
    assert load_input(json_path) == {"weight": [1]}
    assert isinstance(load_input(json_path, format="json"), dict)
    with pytest.raises(InvalidDataError, match="cannot tell the format"):
        load_input(tmp_path / "positions.ods")
    with pytest.raises(InvalidDataError, match=r"re-save it as \.xlsx"):
        load_input(tmp_path / "positions.xls")
    with pytest.raises(InvalidDataError, match="unknown input format"):
        load_input(csv_path, format="xls")
    with pytest.raises(InvalidDataError, match="only be chosen for Excel"):
        load_input(csv_path, sheet="Sheet1")


def test_load_input_rejects_non_utf8(tmp_path: Path) -> None:
    path = tmp_path / "latin.csv"
    path.write_bytes("name\nCaf\xe9\n".encode("latin-1"))
    with pytest.raises(InvalidDataError, match="CSV UTF-8"):
        load_input(path)


def test_mapping_column_errors_also_list_alternatives() -> None:
    report = fa.check({"weights": [1]}, [fa.weights_sum_to_one()])
    assert "did you mean 'weights'?" in report.results[0].message


def test_row_labels_count_blank_lines_and_multiline_cells_like_a_spreadsheet() -> None:
    blank = parse_csv("weight\n0.5\n\n0.5\n-1\n")
    assert blank.column("weight")[1] == [2, 4, 5]
    multiline = parse_csv('note,v\n"two\nlines",1\nok,2\n')
    assert multiline.column("v") == ([1, 2], [2, 3])


def test_very_long_integers_stay_exact_instead_of_crashing() -> None:
    digits = "9" * 5000
    assert parse_csv(f"a\n{digits}\n").column("a")[0] == [Decimal(digits)]
    assert parse_json(f'{{"a": [{digits}]}}') == {"a": [Decimal(digits)]}
