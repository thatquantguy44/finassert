"""Read a range handed over by the Excel JavaScript API, and shape results for a sheet.

The Excel add-in reads the cells a person selected and passes them here as plain
JSON. They are read by the same rules as a saved workbook (``_xlsx.py``) and a CSV
file, so a check gives the same answer inside Excel as on a saved file:

* the first row holds the column names;
* numbers keep their shortest decimal text (``0.1``, not ``0.1000000000000000055``),
  and whole numbers become integers;
* a cell whose number format is a date is read as a date, never as a serial number;
* percentages are never rescaled: a cell showing 40% holds 0.4 and stays 0.4;
* numeric text is read as a number, and blank or spaces-only cells are blank;
* a cell showing an Excel error (``#N/A``, ``#DIV/0!``) is kept as that text, so it
  is an invalid value that fails the row. It is never read as blank or zero.

Row labels are the sheet's own row numbers, so a failing row in a report is the
row a person sees in Excel.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Any

from finassert._xlsx import _excel_date, _is_date_format, column_letter
from finassert.core.exceptions import InvalidDataError
from finassert.loaders import TableSource, parse_cell

MAX_CELLS = 5_000_000
"""Largest selection read, in cells."""

ERROR_VALUES = frozenset(
    [
        "#N/A",
        "#DIV/0!",
        "#VALUE!",
        "#REF!",
        "#NAME?",
        "#NUM!",
        "#NULL!",
        "#SPILL!",
        "#CALC!",
        "#GETTING_DATA",
        "#BLOCKED!",
        "#CONNECT!",
        "#FIELD!",
        "#UNKNOWN!",
        "#BUSY!",
    ]
)
_MAX_NOTE_EXAMPLES = 3
_MAX_DETAIL_ROWS = 200
_FORMULA_STARTS = ("=", "+", "-", "@", "\t", "\r")


def read_range(payload: Mapping[str, Any]) -> TableSource:
    """Convert a selected range into a table whose first row holds the headers.

    Args:
        payload: A mapping with ``values`` (rows of cells, the first row being the
            headers) and optionally ``numberFormats`` and ``valueTypes`` of the same
            shape (as Excel reports them), ``firstRow`` (the sheet row number of the
            first selected row, default 1), and ``date1904`` (whether the workbook
            counts dates from 1904, default false).

    Raises:
        InvalidDataError: If the selection is not rectangular, too large, has no
            header row, or has a blank or repeated header.
    """
    values = payload.get("values")
    if not isinstance(values, Sequence) or isinstance(values, str | bytes) or not values:
        raise InvalidDataError(
            "select a range whose first row holds the column names, followed by the data"
        )
    width = len(values[0]) if isinstance(values[0], Sequence) else 0
    if width == 0 or any(not isinstance(row, Sequence) or len(row) != width for row in values):
        raise InvalidDataError("the selection is not a rectangle of cells")
    if len(values) * width > MAX_CELLS:
        raise InvalidDataError(
            f"the selection has {len(values) * width:,} cells; select at most {MAX_CELLS:,}"
        )
    formats = _same_shape(payload.get("numberFormats"), values, "numberFormats")
    types = _same_shape(payload.get("valueTypes"), values, "valueTypes")
    first_row = payload.get("firstRow", 1)
    if type(first_row) is not int or first_row < 1:
        raise InvalidDataError("firstRow must be a whole number of 1 or more")
    date1904 = bool(payload.get("date1904", False))

    reader = _Reader(date1904)
    header = [
        reader.header(column, values[0][column], _cell(formats, 0, column), _cell(types, 0, column))
        for column in range(width)
    ]
    for position, name in enumerate(header):
        if name in header[:position]:
            raise InvalidDataError(f"the header {name!r} appears more than once")
    columns: dict[str, list[Any]] = {name: [] for name in header}
    labels: list[int] = []
    for index in range(1, len(values)):
        row = [
            reader.cell(
                values[index][column],
                _cell(formats, index, column),
                _cell(types, index, column),
                (first_row + index, header[column]),
            )
            for column in range(width)
        ]
        if all(
            _is_empty(raw, _cell(types, index, column)) for column, raw in enumerate(values[index])
        ):
            continue
        for name, cell in zip(header, row, strict=True):
            columns[name].append(cell)
        labels.append(first_row + index)
    return TableSource(columns, labels, reader.notes())


def results_table(artifact: Mapping[str, Any]) -> list[list[Any]]:
    """Return a report as rows of cells for a results sheet.

    The first row holds the headings. Each check gets a summary row, followed by one
    row for each listed problem (capped) naming the sheet row and what was found.
    Text that Excel could read as a formula is prefixed so it stays text.
    """
    report = artifact["report"]
    results = report["results"]
    described = (artifact.get("policy") or {}).get("rules") or []
    titles = [item.get("title") for item in described] if len(described) == len(results) else []
    rows: list[list[Any]] = [["Check", "Result", "Severity", "Row", "Details"]]
    for position, result in enumerate(results):
        title = (titles[position] if position < len(titles) else None) or result["rule_name"]
        rows.append([title, _label(result), result["severity"], "", result["message"]])
        rows.extend(_detail_rows(result.get("metadata") or {}, title))
    return [[_safe(cell) for cell in row] for row in rows]


RESULTS_WIDTH = 5
POLICY_FIRST_ROW = 3
"""Row of the policy sheet where the policy text starts (rows 1-2 explain the sheet)."""


def results_sheet(artifact: Mapping[str, Any]) -> tuple[list[list[Any]], list[int]]:
    """Return the full results sheet: a stamp describing the run, then the checks.

    The stamp records what was checked, with which policy (name and fingerprint), by
    which version of finassert, and when, so the sheet can be kept as evidence. Every
    row has :data:`RESULTS_WIDTH` cells. Also returns the zero-based rows to show in bold.
    """
    report = artifact["report"]
    policy = artifact.get("policy") or {}
    source = artifact.get("input") or {}
    warned = int(report.get("warnings", 0))
    outcome = "Failed" if not report["passed"] else "Passed with warnings" if warned else "Passed"
    counts = report["counts_by_outcome"]
    stamp: list[list[Any]] = [
        ["finassert results"],
        ["Outcome", outcome],
        ["Policy", policy.get("name") or "(unnamed)"],
        ["Policy fingerprint", policy.get("digest") or ""],
        ["Checked", source.get("locator") or ""],
        [
            "Counts",
            f"{counts['passed']} passed, {counts['failed']} failed, {counts['error']} could "
            f"not run, {counts['skipped']} skipped"
            + (f" ({warned} of the failures only warn)" if warned else ""),
        ],
        ["Generated (UTC)", artifact.get("generated_at") or ""],
        ["finassert version", (artifact.get("tool") or {}).get("version") or ""],
        ["Your data was not changed."],
        [],
    ]
    table = results_table(artifact)
    rows = [_pad(_safe_row(row)) for row in [*stamp, *table]]
    return rows, [0, len(stamp)]


def policy_sheet_rows(policy_text: str) -> list[list[Any]]:
    """Return a policy as rows for the policy sheet: two explanatory rows, then one line each.

    Lines go in one column, so the policy can be read and edited in Excel. Text that
    could be read as a formula is prefixed so it stays text.
    """
    rows: list[list[Any]] = [
        ["finassert policy"],
        ["The add-in reads column A from row 3 as the policy. Edit with care."],
    ]
    rows += [[_safe(line)] for line in policy_text.rstrip("\n").split("\n")]
    return rows


def policy_text_from_rows(values: Sequence[Sequence[Any]]) -> str:
    """Read a policy back from the policy sheet's cells (the inverse of :func:`policy_sheet_rows`).

    Raises:
        InvalidDataError: If the sheet holds no policy text.
    """
    # A leading apostrophe is the mark of text that could have been a formula; drop it.
    lines = [
        "" if row[0] is None else str(row[0]).removeprefix("'")
        for row in values[POLICY_FIRST_ROW - 1 :]
        if row
    ]
    while lines and not lines[-1].strip():
        lines.pop()
    if not lines:
        raise InvalidDataError(
            "the sheet 'finassert policy' holds no policy: the text starts in cell A3"
        )
    return "\n".join(lines) + "\n"


def _pad(row: list[Any]) -> list[Any]:
    return [*row, *([""] * (RESULTS_WIDTH - len(row)))]


def _safe_row(row: list[Any]) -> list[Any]:
    return [_safe(cell) for cell in row]


def _label(result: Mapping[str, Any]) -> str:
    outcome = str(result["outcome"])
    if outcome == "failed" and result.get("blocking") is False:
        return "Warning"
    return {"error": "Could not run"}.get(outcome, outcome.capitalize())


def _detail_rows(metadata: Mapping[str, Any], title: str) -> list[list[Any]]:
    rows: list[list[Any]] = []
    for key, value in metadata.items():
        if not isinstance(value, list):
            continue
        for item in value:
            if isinstance(item, Mapping):
                label = item.get("row")
                if label is None and isinstance(item.get("rows"), list) and item["rows"]:
                    label = item["rows"][0]
                detail = "; ".join(
                    f"{name}: {_text(entry)}"
                    for name, entry in item.items()
                    if name not in {"row", "rows"}
                )
                rows.append([title, "", "", _scalar(label), detail])
            elif key in {"invalid_rows", "missing_rows", "blank_rows"}:
                rows.append([title, "", "", _scalar(item), key.replace("_", " ")])
            if len(rows) >= _MAX_DETAIL_ROWS:
                return rows
    return rows


def _scalar(value: Any) -> Any:
    return "" if value is None else value if isinstance(value, int | str) else str(value)


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, Mapping):
        return ", ".join(f"{key} {_text(item)}" for key, item in value.items())
    if isinstance(value, list):
        return ", ".join(_text(item) for item in value)
    return str(value)


def _safe(cell: Any) -> Any:
    # A leading apostrophe makes Excel keep "=1+1" as text instead of a formula.
    if isinstance(cell, str) and cell.startswith(_FORMULA_STARTS):
        return "'" + cell
    return cell


def _is_empty(value: Any, value_type: Any) -> bool:
    # Excel reports an empty cell as "" (or Empty); a cell holding spaces is not empty.
    return value is None or value == "" or value_type == "Empty"


def _same_shape(grid: Any, values: Sequence[Any], name: str) -> Sequence[Any] | None:
    if grid is None:
        return None
    if (
        not isinstance(grid, Sequence)
        or len(grid) != len(values)
        or any(len(row) != len(values[0]) for row in grid)
    ):
        raise InvalidDataError(f"{name} must have the same shape as values")
    return grid


def _cell(grid: Sequence[Any] | None, row: int, column: int) -> Any:
    return None if grid is None else grid[row][column]


class _Reader:
    def __init__(self, date1904: bool) -> None:
        self._date1904 = date1904
        self._errors: list[tuple[int, str, str]] = []
        self._error_count = 0
        self._unconverted = 0

    def header(self, column: int, value: Any, number_format: Any, value_type: Any) -> str:
        cell = self.cell(value, number_format, value_type, None)
        if cell is None or (isinstance(cell, str) and not cell.strip()):
            raise InvalidDataError(f"the header of column {column_letter(column)} is blank")
        if isinstance(cell, str) and cell in ERROR_VALUES:
            raise InvalidDataError(
                f"the header of column {column_letter(column)} shows the Excel error {cell}"
            )
        return cell if isinstance(cell, str) else _plain(cell)

    def cell(
        self, value: Any, number_format: Any, value_type: Any, where: tuple[int, str] | None
    ) -> Any:
        if _is_empty(value, value_type):
            return None
        if value_type == "Error" or (isinstance(value, str) and value in ERROR_VALUES):
            if where is not None:
                self._error_count += 1
                if len(self._errors) < _MAX_NOTE_EXAMPLES:
                    self._errors.append((where[0], where[1], str(value)))
            return str(value)
        if isinstance(value, bool):
            return value
        if isinstance(value, int | float):
            number = _number(value)
            if isinstance(number_format, str) and _is_date_format(number_format):
                try:
                    return _excel_date(number, self._date1904)
                except (ValueError, OverflowError):
                    self._unconverted += 1
            return number
        return parse_cell(str(value))

    def notes(self) -> list[str]:
        notes = []
        if self._error_count:
            examples = ", ".join(
                f"{error} in column {name!r}, row {row}" for row, name, error in self._errors
            )
            notes.append(
                f"{self._error_count} cell(s) show Excel errors (for example {examples}). "
                "They are read as invalid values and fail any check on their column."
            )
        if self._unconverted:
            notes.append(
                f"{self._unconverted} cell(s) have a date format but hold a value that is not a "
                "valid date, so they were read as plain numbers."
            )
        return notes


def _number(value: int | float) -> int | Decimal:
    if isinstance(value, int):
        return value
    if not math.isfinite(value):
        raise InvalidDataError(f"the selection holds a value that is not a number: {value!r}")
    number = Decimal(repr(value))
    # Whole numbers become integers, as in a saved workbook.
    return int(number) if number == number.to_integral_value() and abs(number) < 10**15 else number


def _plain(value: Any) -> str:
    return value.isoformat() if hasattr(value, "isoformat") else str(value)
