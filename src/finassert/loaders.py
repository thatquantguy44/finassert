"""Explicit, dependency-free loaders for tabular input files.

Loaders never guess at financial meaning: numeric text becomes ``int`` or
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

from finassert.core.exceptions import ColumnNotFoundError, InvalidDataError

INPUT_FORMATS = ("csv", "json")
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


def input_format_for(path: Path) -> str:
    """Infer an input format from a file extension."""
    suffix = path.suffix.lower().lstrip(".")
    if suffix in INPUT_FORMATS:
        return suffix
    raise InvalidDataError(
        f"cannot tell the format of {path.name!r}; pass a format of: {', '.join(INPUT_FORMATS)}"
    )


def load_input(path: str | PathLike[str], *, format: str | None = None) -> Any:
    """Read a CSV or JSON input file for validation.

    Args:
        path: Input file location.
        format: ``"csv"`` or ``"json"``; inferred from the extension when omitted.

    Raises:
        InvalidDataError: If the format is unknown or the content malformed.
        OSError: If the file cannot be read.
    """
    location = Path(path)
    resolved = format or input_format_for(location)
    if resolved not in INPUT_FORMATS:
        raise InvalidDataError(
            f"unknown input format {resolved!r}; use one of: {', '.join(INPUT_FORMATS)}"
        )
    try:
        text = location.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        raise InvalidDataError(
            f"{location.name!r} is not UTF-8 text; re-save it as 'CSV UTF-8'"
        ) from exc
    return parse_csv(text) if resolved == "csv" else parse_json(text)
