"""Explicit loaders for tabular input files.

CSV, JSON, and Excel ``.xlsx`` need no dependency; Parquet needs the optional
``pyarrow`` package. Loaders never guess at financial meaning: numeric text becomes ``int`` or
``Decimal`` exactly as written, blank cells become ``None``, and anything else
(``"1,000"``, ``"40%"``, ``"$5"``) stays text so rules report it as
non-numeric rather than silently rescaling it.
"""

from __future__ import annotations

import csv
import io
import json
import re
from decimal import Decimal
from os import PathLike
from pathlib import Path
from typing import Any

from finassert._xlsx import SheetError, column_letter, read_sheet
from finassert.core.exceptions import ColumnNotFoundError, InvalidDataError

INPUT_FORMATS = ("csv", "json", "xlsx", "parquet")
_EXTENSIONS = {
    "csv": "csv",
    "json": "json",
    "xlsx": "xlsx",
    "xlsm": "xlsx",
    "parquet": "parquet",
    "pq": "parquet",
}
_INTEGER = re.compile(r"^[+-]?\d+$")
_DECIMAL = re.compile(r"^[+-]?(\d+\.\d*|\.\d+|\d+(\.\d*)?[eE][+-]?\d+)$")


class TableSource:
    """Named columns with spreadsheet-style row labels.

    Implements the core ``ColumnSource`` protocol. Row labels are the row
    numbers a spreadsheet would show, with the header on row 1.

    Args:
        columns: Column values keyed by header text, in file order.
        labels: Row label for each position.
    """

    def __init__(self, columns: dict[str, list[Any]], labels: list[Any]) -> None:
        for name, values in columns.items():
            if len(values) != len(labels):
                raise InvalidDataError(f"column {name!r} does not match the row count")
        self._columns = columns
        self._labels = labels

    @property
    def column_names(self) -> tuple[str, ...]:
        """Return header names in file order."""
        return tuple(self._columns)

    @property
    def row_count(self) -> int:
        """Return the number of data rows."""
        return len(self._labels)

    def column(self, name: str) -> tuple[list[Any], list[Any]]:
        """Return a column's values and row labels."""
        if name not in self._columns:
            raise ColumnNotFoundError(name, self.column_names)
        return list(self._columns[name]), list(self._labels)

    def preview(self, rows: int = 5) -> list[dict[str, Any]]:
        """Return up to ``rows`` leading rows as mappings for display."""
        return [
            {name: values[index] for name, values in self._columns.items()}
            for index in range(min(rows, self.row_count))
        ]


def _integer(text: str) -> int | Decimal:
    # Python refuses int() on very long digit strings; Decimal keeps them exact.
    try:
        return int(text)
    except ValueError:
        return Decimal(text)


def parse_cell(text: str) -> Any:
    """Convert one CSV cell to ``None``, ``int``, ``Decimal``, or unchanged text."""
    stripped = text.strip()
    if not stripped:
        return None
    if _INTEGER.match(stripped):
        return _integer(stripped)
    if _DECIMAL.match(stripped):
        return Decimal(stripped)
    return text


def parse_csv(text: str) -> TableSource:
    """Parse comma-separated text whose first row holds unique column headers."""
    reader = csv.reader(io.StringIO(text.removeprefix("﻿"), newline=""), strict=True)
    try:
        header = next(reader)
    except StopIteration:
        raise InvalidDataError("the CSV file is empty; the first row must hold headers") from None
    except csv.Error as exc:
        raise InvalidDataError(f"the CSV header row could not be read: {exc}") from exc
    seen: set[str] = set()
    for position, name in enumerate(header, start=1):
        if not name.strip():
            raise InvalidDataError(f"CSV column {position} has no header text")
        if name in seen:
            raise InvalidDataError(f"CSV header {name!r} appears more than once")
        seen.add(name)

    columns: dict[str, list[Any]] = {name: [] for name in header}
    labels: list[int] = []
    try:
        # Spreadsheets give every record a row, blank ones included, and keep a
        # quoted multi-line cell in one row; the header is row 1.
        for spreadsheet_row, row in enumerate(reader, start=2):
            if not row:
                continue
            if len(row) != len(header):
                raise InvalidDataError(
                    f"CSV row {spreadsheet_row} has {len(row)} cell(s) but the header "
                    f"has {len(header)}"
                )
            for name, cell in zip(header, row, strict=True):
                columns[name].append(parse_cell(cell))
            labels.append(spreadsheet_row)
    except csv.Error as exc:
        raise InvalidDataError(f"the CSV file could not be read: {exc}") from exc
    return TableSource(columns, labels)


def parse_json(text: str) -> Any:
    """Parse a JSON column mapping or list of row objects, keeping decimals exact."""
    try:
        data = json.loads(text, parse_float=Decimal, parse_int=_integer)
    except json.JSONDecodeError as exc:
        raise InvalidDataError(f"the JSON input is not valid JSON: {exc}") from exc
    if isinstance(data, dict):
        return data
    if isinstance(data, list) and all(isinstance(row, dict) for row in data):
        return data
    raise InvalidDataError("JSON input must be an object of columns or a list of row objects")


def parse_xlsx(data: bytes, *, sheet: str | None = None) -> TableSource:
    """Read one worksheet of an Excel ``.xlsx`` workbook.

    The first non-empty row holds the headers. Numbers keep the exact decimal
    value Excel stored, whatever the cell displays; percentage cells keep their
    stored fraction (``0.4`` for 40%). Date cells become ``date``, ``datetime``,
    or ``time`` and are never read as day counts. Text cells follow the CSV
    rules: numeric text becomes a number and blank text is an empty cell. Rows
    with no values are skipped, and row labels are the sheet's own row numbers.

    Args:
        data: The workbook file contents.
        sheet: Worksheet name; required when the workbook has several sheets.

    Raises:
        InvalidDataError: If the workbook, sheet, or headers cannot be read,
            or a formula cell has no saved result.
    """
    worksheet = read_sheet(data, sheet)
    if not worksheet.rows:
        raise InvalidDataError(f"sheet {worksheet.name!r} is empty; row 1 must hold headers")
    header_row, header_cells = worksheet.rows[0]
    headers: dict[int, str] = {}
    for position, value in sorted(header_cells.items()):
        name = value if isinstance(value, str) else str(value)
        if not name.strip():
            raise InvalidDataError(f"cell {column_letter(position)}{header_row} has no header text")
        if name in headers.values():
            raise InvalidDataError(f"header {name!r} appears more than once")
        headers[position] = name
    columns: dict[str, list[Any]] = {name: [] for name in headers.values()}
    labels: list[int] = []
    for row_number, cells in worksheet.rows[1:]:
        for position in cells:
            if position not in headers:
                raise InvalidDataError(
                    f"cell {column_letter(position)}{row_number} has a value but its column "
                    "has no header"
                )
        for position, name in headers.items():
            value = cells.get(position)
            # Numbers stored as text read as numbers, exactly as in a CSV file.
            columns[name].append(parse_cell(value) if isinstance(value, str) else value)
        labels.append(row_number)
    return TableSource(columns, labels)


def read_parquet(path: str | PathLike[str]) -> TableSource:
    """Read a Parquet file; requires the optional ``pyarrow`` package.

    Values keep their stored types: decimal columns become ``Decimal``, floating
    columns stay ``float``, and nulls become ``None``. Row labels are positions
    starting at 0, as in a default pandas index.

    Raises:
        InvalidDataError: If pyarrow is missing or the file is not valid Parquet.
    """
    try:
        import pyarrow.parquet as parquet
    except ImportError as exc:
        raise InvalidDataError(
            "reading Parquet needs pyarrow; install 'finassert[parquet]'"
        ) from exc
    try:
        table = parquet.read_table(path)
    except OSError:
        raise
    except Exception as exc:
        raise InvalidDataError(f"the Parquet file could not be read: {exc}") from exc
    names = [str(name) for name in table.column_names]
    if len(set(names)) != len(names):
        raise InvalidDataError("the Parquet file has duplicate column names")
    columns = {name: table.column(index).to_pylist() for index, name in enumerate(names)}
    return TableSource(columns, list(range(table.num_rows)))


def input_format_for(path: Path) -> str:
    """Infer an input format from a file extension."""
    suffix = path.suffix.lower().lstrip(".")
    resolved = _EXTENSIONS.get(suffix)
    if resolved is not None:
        return resolved
    if suffix == "xls":
        raise InvalidDataError(
            f"{path.name!r} is an old-style Excel file; re-save it as .xlsx (Excel Workbook)"
        )
    raise InvalidDataError(
        f"cannot tell the format of {path.name!r}; pass a format of: {', '.join(INPUT_FORMATS)}"
    )


def load_input(
    path: str | PathLike[str],
    *,
    format: str | None = None,
    sheet: str | None = None,
) -> Any:
    """Read a CSV, JSON, Excel, or Parquet input file for validation.

    Args:
        path: Input file location.
        format: One of :data:`INPUT_FORMATS`; inferred from the extension when
            omitted.
        sheet: Worksheet to read from an Excel workbook.

    Raises:
        InvalidDataError: If the format is unknown, a sheet is given for a
            non-Excel file, or the content is malformed.
        OSError: If the file cannot be read.
    """
    location = Path(path)
    resolved = format or input_format_for(location)
    if resolved not in INPUT_FORMATS:
        raise InvalidDataError(
            f"unknown input format {resolved!r}; use one of: {', '.join(INPUT_FORMATS)}"
        )
    if sheet is not None and resolved != "xlsx":
        raise SheetError("a sheet can only be chosen for Excel (.xlsx) input", ())
    if resolved == "xlsx":
        return parse_xlsx(location.read_bytes(), sheet=sheet)
    if resolved == "parquet":
        return read_parquet(location)
    try:
        text = location.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        raise InvalidDataError(
            f"{location.name!r} is not UTF-8 text; re-save it as 'CSV UTF-8'"
        ) from exc
    return parse_csv(text) if resolved == "csv" else parse_json(text)
