"""Workbook edge cases retain physical row identity and never recalculate."""

import datetime as dt
import json
import zipfile
from pathlib import Path

import pytest

from finassert import cli
from finassert.core.exceptions import InvalidDataError
from finassert.excel import read_workbook
from finassert.loaders import load_input

openpyxl = pytest.importorskip("openpyxl")


def workbook(path: Path):
    book = openpyxl.Workbook()
    sheet = book.active
    sheet.title = "Data"
    sheet.append(["value", "date"])
    sheet.append([2, dt.datetime(2024, 2, 29)])
    sheet.append([3, dt.datetime(2024, 3, 1)])
    book.save(path)
    return book, sheet


def readers(path, **options):
    return [read_workbook(path, sheet="Data", **options), load_input(path, sheet="Data", **options)]


@pytest.mark.parametrize("epoch", [dt.datetime(1899, 12, 30), dt.datetime(1904, 1, 1)])
def test_dates_and_cached_formulas_match_both_readers(tmp_path, epoch):
    path = tmp_path / "cached.xlsx"
    book, sheet = workbook(path)
    book.epoch = epoch
    sheet["A2"] = "=1+1"
    book.save(path)
    # Author a real OOXML cached result; openpyxl never evaluates formulas.
    with zipfile.ZipFile(path) as original:
        members = {name: original.read(name) for name in original.namelist()}
    members["xl/worksheets/sheet1.xml"] = (
        members["xl/worksheets/sheet1.xml"]
        .replace(b"<f>1+1</f><v />", b"<f>1+1</f><v>2</v>")
        .replace(b"<f>1+1</f><v></v>", b"<f>1+1</f><v>2</v>")
    )
    with zipfile.ZipFile(path, "w") as target:
        for name, data in members.items():
            target.writestr(name, data)
    before = path.read_bytes()
    for source in readers(path):
        assert source.column("value") == ([2, 3], [2, 3])
        assert source.column("date") == ([dt.date(2024, 2, 29), dt.date(2024, 3, 1)], [2, 3])
    assert path.read_bytes() == before


@pytest.mark.parametrize("region", ["row", "column", "sheet"])
def test_hidden_inputs_are_included_or_explicitly_rejected(tmp_path, region):
    path = tmp_path / "hidden.xlsx"
    book, sheet = workbook(path)
    if region == "row":
        sheet.row_dimensions[2].hidden = True
    elif region == "column":
        sheet.column_dimensions["A"].hidden = True
    else:
        book.create_sheet("Visible")
        sheet.sheet_state = "veryHidden"
    book.save(path)
    before = path.read_bytes()
    for source in readers(path):
        assert source.column("value") == ([2, 3], [2, 3])
        metadata = source.workbook_metadata
        assert metadata["hidden_region_policy"] == "include"
        if region == "row":
            assert metadata["hidden_rows"]["examples"] == [2]
        if region == "column":
            assert metadata["hidden_columns"]["examples"] == ["A"]
        metadata["sheet_state"] = "mutated"
        assert source.workbook_metadata["sheet_state"] != "mutated"
    for read in (read_workbook, load_input):
        with pytest.raises(InvalidDataError, match="hidden"):
            read(path, sheet="Data", hidden="reject")
    assert path.read_bytes() == before


def test_visibility_is_bounded_and_ignores_rows_outside_selection(tmp_path):
    path = tmp_path / "many.xlsx"
    book, sheet = workbook(path)
    for number in range(3, 100):
        sheet.cell(number, 1, number)
        sheet.row_dimensions[number].hidden = True
    book.save(path)
    for source in readers(path):
        hidden = source.workbook_metadata["hidden_rows"]
        assert hidden == {"count": 97, "examples": list(range(3, 23)), "truncated": True}
    for source in readers(path, max_row=2, hidden="reject"):
        assert source.column("value")[1] == [2]


def test_merged_headers_and_uncached_header_formulas_are_errors(tmp_path):
    path = tmp_path / "merged.xlsx"
    book, sheet = workbook(path)
    sheet.merge_cells("A1:B1")
    book.save(path)
    for read in (read_workbook, load_input):
        with pytest.raises(InvalidDataError, match="merged header"):
            read(path, sheet="Data")
    sheet.unmerge_cells("A1:B1")
    sheet["A1"] = "=1+1"
    book.save(path)
    for read in (read_workbook, load_input):
        with pytest.raises(InvalidDataError, match="A1"):
            read(path, sheet="Data")


def test_cli_records_visibility_and_rejects_without_writing_report(tmp_path):
    path = tmp_path / "input.xlsx"
    book, sheet = workbook(path)
    sheet.row_dimensions[2].hidden = True
    book.save(path)
    policy = tmp_path / "policy.json"
    policy.write_text(
        json.dumps({"version": 1, "rules": [{"rule": "non_negative", "column": "value"}]})
    )
    output = tmp_path / "report.json"
    args = [
        "check",
        "--config",
        str(policy),
        "--input",
        str(path),
        "--sheet",
        "Data",
        "--output",
        str(output),
    ]
    assert cli.main(args) == 0
    assert json.loads(output.read_text())["input"]["workbook"]["hidden_rows"]["count"] == 1
    output.unlink()
    assert cli.main([*args, "--hidden", "reject"]) == 4
    assert not output.exists()
