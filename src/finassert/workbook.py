"""Optional Excel workbook reader.

Importing this module does not import openpyxl; the dependency is loaded when a
workbook is read. Workbooks are opened for reading only and never modified.
"""

from __future__ import annotations

import copy
import datetime as dt
import os
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from finassert._workbook_region import workbook_region
from finassert.core.exceptions import ColumnNotFoundError, InvalidDataError
from finassert.core.models import CellError


@dataclass(frozen=True, slots=True)
class ExcelError(CellError):
    """A worksheet error cell such as ``#N/A`` or ``#DIV/0!``.

    Column extraction raises an evaluation error when a rule requests this cell.
    """


class WorkbookSource:
    """Expose one worksheet through the core ``ColumnSource`` protocol.

    Row labels are 1-based worksheet row numbers, as Excel displays them.
    """

    def __init__(
        self,
        columns: dict[str, list[Any]],
        labels: list[int],
        *,
        workbook_metadata: dict[str, Any] | None = None,
    ) -> None:
        for name, values in columns.items():
            if len(values) != len(labels):
                raise InvalidDataError(f"column {name!r} does not match the row count")
        self._columns = columns
        self._labels = labels
        self._workbook_metadata = copy.deepcopy(workbook_metadata)

    @property
    def workbook_metadata(self) -> dict[str, Any] | None:
        """Return a detached visibility description of the selected region."""
        return copy.deepcopy(self._workbook_metadata)

    @property
    def headers(self) -> tuple[str, ...]:
        """Return header names in worksheet order."""
        return tuple(self._columns)

    def column(self, name: str) -> tuple[list[Any], list[Any]]:
        """Return a column's values and worksheet row numbers."""
        if name not in self._columns:
            raise ColumnNotFoundError(name)
        return list(self._columns[name]), list(self._labels)


def read_workbook(
    path: str | os.PathLike[str],
    *,
    sheet: str,
    header_row: int = 1,
    max_row: int | None = None,
    hidden: str = "include",
) -> WorkbookSource:
    """Read a worksheet into a ``ColumnSource`` without modifying the file.

    Cached formula results are read; a formula cell with no cached value (the
    workbook was never calculated by Excel) is an error naming the cell. Numeric
    cells become ``Decimal`` from their shortest round-trip representation, blank
    cells become ``None``, error cells become ``ExcelError``, and midnight
    datetimes become ``date``. Fully blank trailing rows are dropped.

    Args:
        path: ``.xlsx`` file to read.
        sheet: Worksheet name; required so the choice is never implicit.
        header_row: 1-based row containing column headers.
        max_row: Optional last 1-based row to read, for data followed by totals.
        hidden: Include hidden cells (default), or reject hidden selected regions.

    Raises:
        InvalidDataError: Unreadable file, missing sheet, bad header row, empty
            or duplicate headers, or a formula cell without a cached value.
    """
    if hidden not in {"include", "reject"}:
        raise InvalidDataError("hidden must be 'include' or 'reject'")
    if type(header_row) is not int or header_row < 1:
        raise InvalidDataError("header_row must be at least 1")
    if max_row is not None and (type(max_row) is not int or max_row <= header_row):
        raise InvalidDataError("max_row must be greater than header_row")
    try:
        import openpyxl
    except ImportError as exc:  # pragma: no cover - exercised only without the extra
        raise ImportError(
            "read_workbook requires openpyxl; install with 'pip install finassert[excel]'"
        ) from exc

    values_book = _load(openpyxl, path, data_only=True)
    try:
        if sheet not in values_book.sheetnames:
            raise InvalidDataError(f"sheet {sheet!r} not found")
        rows = _read_rows(values_book[sheet], header_row, max_row)
        header_formula = _uncached_formulas(
            openpyxl,
            path,
            sheet,
            rows[:1],
            dict.fromkeys(range(len(rows[0][1]) if rows else 0), "header"),
        )
        if header_formula:
            raise InvalidDataError(f"formula cell {header_formula} has no cached value")
        headers = _headers(rows[0][1] if rows else [], header_row)
        data = rows[1:]
        uncached = _uncached_formulas(openpyxl, path, sheet, data, headers)
    finally:
        values_book.close()
    if uncached:
        raise InvalidDataError(
            f"formula cell {uncached} has no cached value; open and save the workbook in Excel"
        )

    metadata = workbook_region(
        path,
        sheet=sheet,
        header_row=header_row,
        max_row=max_row or (rows[-1][0] if rows else header_row),
        columns=set(headers),
        hidden=hidden,
    )
    while data and all(_cell_value(cell) is None for cell in data[-1][1]):
        data.pop()
    labels = [number for number, _ in data]
    columns = {name: [_convert(row[index]) for _, row in data] for index, name in headers.items()}
    return WorkbookSource(
        dict(zip(headers.values(), columns.values(), strict=True)),
        labels,
        workbook_metadata=metadata,
    )


def _load(openpyxl: Any, path: str | os.PathLike[str], *, data_only: bool) -> Any:
    try:
        return openpyxl.load_workbook(path, read_only=True, data_only=data_only)
    except FileNotFoundError:
        raise
    except Exception as exc:
        raise InvalidDataError(f"cannot read workbook {os.fspath(path)!r}: {exc}") from exc


def _read_rows(worksheet: Any, header_row: int, max_row: int | None) -> list[tuple[int, list[Any]]]:
    rows: list[tuple[int, list[Any]]] = []
    for number, row in enumerate(
        worksheet.iter_rows(min_row=header_row, max_row=max_row), start=header_row
    ):
        rows.append((number, list(row)))
    return rows


def _headers(cells: list[Any], header_row: int) -> dict[int, str]:
    if not cells:
        raise InvalidDataError(f"header row {header_row} is empty")
    headers: dict[int, str] = {}
    for index, cell in enumerate(cells):
        value = _cell_value(cell)
        if value is None:
            continue
        name = str(value).strip()
        if not name:
            continue
        if name in headers.values():
            raise InvalidDataError(f"duplicate header {name!r} in row {header_row}")
        headers[index] = name
    if not headers:
        raise InvalidDataError(f"header row {header_row} is empty")
    return headers


def _cell_value(cell: Any) -> Any:
    return getattr(cell, "value", None)


def _uncached_formulas(
    openpyxl: Any,
    path: str | os.PathLike[str],
    sheet: str,
    data: list[tuple[int, list[Any]]],
    headers: dict[int, str],
) -> str | None:
    blanks = [
        (number, index)
        for number, row in data
        for index in headers
        if index >= len(row) or _cell_value(row[index]) is None
    ]
    if not blanks:
        return None
    formulas_book = _load(openpyxl, path, data_only=False)
    try:
        worksheet = formulas_book[sheet]
        for number, index in blanks:
            value = worksheet.cell(row=number, column=index + 1).value
            if isinstance(value, str) and value.startswith("="):
                return str(worksheet.cell(row=number, column=index + 1).coordinate)
    finally:
        formulas_book.close()
    return None


def _convert(cell: Any) -> Any:
    if cell is None:
        return None
    value = _cell_value(cell)
    if value is None:
        return None
    if getattr(cell, "data_type", None) == "e":
        return ExcelError(str(value))
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float):
        return Decimal(repr(value))
    if isinstance(value, dt.datetime) and value.time() == dt.time(0):
        return value.date()
    return value
