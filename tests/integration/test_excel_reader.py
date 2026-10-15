from __future__ import annotations

import datetime as dt
import sys
from decimal import Decimal
from pathlib import Path

import pytest

import finassert as fa
from finassert.core.exceptions import ColumnNotFoundError, InvalidDataError
from finassert.core.protocols import ColumnSource
from finassert.excel import ExcelError, read_workbook

openpyxl = pytest.importorskip("openpyxl")


def _make(path: Path, rows: list[list[object]], *, sheet: str = "Positions") -> Path:
    book = openpyxl.Workbook()
    ws = book.active
    ws.title = sheet
    for row in rows:
        ws.append(row)
    book.save(path)
    return path


def test_reads_columns_with_worksheet_row_labels(tmp_path: Path) -> None:
    path = _make(tmp_path / "w.xlsx", [["id", "weight"], ["a", 0.1], ["b", 0.9]])
    source = read_workbook(path, sheet="Positions")
    assert isinstance(source, ColumnSource)
    values, labels = source.column("weight")
    assert values == [Decimal("0.1"), Decimal("0.9")]
    assert labels == [2, 3]


def test_header_row_offset_and_whitespace_trim(tmp_path: Path) -> None:
    path = _make(tmp_path / "w.xlsx", [["title"], [" MV (USD) ", None, "x"], [5, None, 1]])
    source = read_workbook(path, sheet="Positions", header_row=2)
    assert source.headers == ("MV (USD)", "x")
    assert source.column("MV (USD)") == ([Decimal(5)], [3])


def test_blank_none_errors_and_dates(tmp_path: Path) -> None:
    path = _make(
        tmp_path / "w.xlsx",
        [["v", "d"], [None, dt.datetime(2026, 1, 2)], ["#N/A", dt.datetime(2026, 1, 2, 9, 30)]],
    )
    book = openpyxl.load_workbook(path)
    book.active["A3"].data_type = "e"
    book.save(path)
    source = read_workbook(path, sheet="Positions")
    values, _ = source.column("v")
    assert values == [None, ExcelError("#N/A")]
    dates, _ = source.column("d")
    assert dates == [dt.date(2026, 1, 2), dt.datetime(2026, 1, 2, 9, 30)]


def test_trailing_blank_rows_dropped_and_max_row(tmp_path: Path) -> None:
    path = _make(tmp_path / "w.xlsx", [["v"], [1], [None], [2], ["total"], [None], [None]])
    assert read_workbook(path, sheet="Positions").column("v")[1] == [2, 3, 4, 5]
    assert read_workbook(path, sheet="Positions", max_row=4).column("v")[1] == [2, 3, 4]


@pytest.mark.parametrize(
    ("rows", "kwargs"),
    [
        ([["a", "a"], [1, 2]], {}),
        ([[None, None], [1, 2]], {}),
        ([["a"], [1]], {"sheet": "Nope"}),
        ([["a"], [1]], {"header_row": 0}),
        ([["a"], [1]], {"max_row": 1}),
    ],
)
def test_input_errors(tmp_path: Path, rows: list[list[object]], kwargs: dict[str, object]) -> None:
    path = _make(tmp_path / "w.xlsx", rows)
    options: dict[str, object] = {"sheet": "Positions", **kwargs}
    with pytest.raises(InvalidDataError):
        read_workbook(path, **options)  # type: ignore[arg-type]


def test_missing_column_and_corrupt_file(tmp_path: Path) -> None:
    path = _make(tmp_path / "w.xlsx", [["a"], [1]])
    with pytest.raises(ColumnNotFoundError):
        read_workbook(path, sheet="Positions").column("zzz")
    bad = tmp_path / "bad.xlsx"
    bad.write_bytes(b"not a zip")
    with pytest.raises(InvalidDataError):
        read_workbook(bad, sheet="Positions")
    with pytest.raises(FileNotFoundError):
        read_workbook(tmp_path / "none.xlsx", sheet="Positions")


def test_formula_without_cached_value_is_error(tmp_path: Path) -> None:
    path = _make(tmp_path / "w.xlsx", [["a", "b"], [1, "=A2*2"]])
    with pytest.raises(InvalidDataError, match="B2"):
        read_workbook(path, sheet="Positions")


def test_file_not_modified(tmp_path: Path) -> None:
    path = _make(tmp_path / "w.xlsx", [["a"], [1]])
    before = path.read_bytes()
    read_workbook(path, sheet="Positions")
    assert path.read_bytes() == before


def test_matches_pandas_adapter_through_rules(tmp_path: Path) -> None:
    pd = pytest.importorskip("pandas")
    rows: list[list[object]] = [["w"], [0.25], [0.25], [0.5]]
    path = _make(tmp_path / "w.xlsx", rows)
    rule = fa.weights_sum_to_one(column="w")
    excel_report = fa.check(read_workbook(path, sheet="Positions"), [rule])
    frame = pd.DataFrame({"w": [Decimal("0.25"), Decimal("0.25"), Decimal("0.5")]})
    assert excel_report.passed == fa.check(frame, [rule]).passed


def test_core_import_does_not_load_openpyxl() -> None:
    import subprocess

    code = "import sys, finassert; sys.exit('openpyxl' in sys.modules)"
    assert subprocess.run([sys.executable, "-c", code], check=False).returncode == 0
