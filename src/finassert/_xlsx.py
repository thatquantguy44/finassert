"""Minimal, dependency-free reader for Excel ``.xlsx`` workbooks.

Only cell values are read: no formatting beyond what is needed to recognise
dates, no charts, no evaluation of formulas. Values keep the exact decimal text
Excel stored, so nothing is rounded to what a cell happened to display.
"""

from __future__ import annotations

import io
import posixpath
import re
import zipfile
import zlib
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Any
from xml.etree import ElementTree

from finassert.core.exceptions import InvalidDataError

_MAIN = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
_REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
_PKG_REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"
_MAX_MEMBER_BYTES = 256 * 1024 * 1024
_CELL_REF = re.compile(r"^([A-Z]{1,3})(\d+)$")
_INTEGER = re.compile(r"^[+-]?\d+$")
# Built-in number formats that display dates or times (ECMA-376 18.8.30).
_DATE_FORMAT_IDS = frozenset([*range(14, 23), *range(27, 37), *range(45, 48), *range(50, 59)])
_FORMAT_NOISE = re.compile(r'"[^"]*"|\\.|\[[^\]]*\]')


class SheetError(InvalidDataError):
    """Raised when the worksheet to read is ambiguous or does not exist.

    Attributes:
        sheets: Worksheet names in tab order, so callers can offer a choice.
    """

    def __init__(self, message: str, sheets: tuple[str, ...]) -> None:
        super().__init__(message)
        self.sheets = sheets


@dataclass(frozen=True, slots=True)
class Sheet:
    """Cell values of one worksheet.

    Args:
        name: Worksheet name as shown on its tab.
        rows: Each non-empty row's Excel row number and its values by column
            position (0 for column A).
    """

    name: str
    rows: tuple[tuple[int, dict[int, Any]], ...]


def sheet_names(data: bytes) -> tuple[str, ...]:
    """Return worksheet names in tab order."""
    with _open(data) as archive:
        return tuple(name for name, _ in _sheets(archive))


def read_sheet(data: bytes, sheet: str | None = None) -> Sheet:
    """Read one worksheet's values.

    Args:
        data: The ``.xlsx`` file contents.
        sheet: Worksheet name. Required when the workbook has several sheets.

    Raises:
        InvalidDataError: If the file is not a readable workbook, the sheet is
            ambiguous or missing, or a formula has no saved result.
    """
    with _open(data) as archive:
        sheets = _sheets(archive)
        names = tuple(name for name, _ in sheets)
        if sheet is None:
            if len(sheets) != 1:
                raise SheetError(
                    f"the workbook has {len(sheets)} sheets ({_listed(names)}); choose one",
                    names,
                )
            name, path = sheets[0]
        else:
            matches = [(name, path) for name, path in sheets if name == sheet]
            if not matches:
                raise SheetError(
                    f"the workbook has no sheet {sheet!r}; it has {_listed(names)}", names
                )
            name, path = matches[0]
        strings = _shared_strings(archive)
        date_styles, date1904 = _date_styles(archive), _uses_1904_dates(archive)
        root = _xml(archive, path)
    rows: list[tuple[int, dict[int, Any]]] = []
    last_row = 0
    for row in root.iter(f"{_MAIN}row"):
        number = int(row.get("r") or last_row + 1)
        last_row = number
        values: dict[int, Any] = {}
        last_column = -1
        for cell in row.iter(f"{_MAIN}c"):
            column = _column_index(cell.get("r"), last_column)
            last_column = column
            value = _cell_value(cell, strings, date_styles, date1904, name)
            if isinstance(value, str) and not value.strip():
                value = None  # blank text counts as an empty cell, as in CSV
            if value is not None:
                values[column] = value
        if values:
            rows.append((number, values))
    return Sheet(name=name, rows=tuple(rows))


def column_letter(index: int) -> str:
    """Return the Excel column letters for a zero-based column index."""
    letters = ""
    index += 1
    while index:
        index, remainder = divmod(index - 1, 26)
        letters = chr(65 + remainder) + letters
    return letters


def _open(data: bytes) -> zipfile.ZipFile:
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile as exc:
        raise InvalidDataError(
            "the file is not an .xlsx workbook; older .xls files must be re-saved as .xlsx"
        ) from exc
    for info in archive.infolist():
        if info.file_size > _MAX_MEMBER_BYTES:
            archive.close()
            raise InvalidDataError(f"the workbook part {info.filename!r} is too large to read")
    return archive


def _xml(archive: zipfile.ZipFile, path: str) -> ElementTree.Element:
    try:
        return ElementTree.fromstring(archive.read(path))
    except KeyError as exc:
        raise InvalidDataError(f"the workbook is missing {path!r}") from exc
    except (zipfile.BadZipFile, zlib.error, EOFError, NotImplementedError, RuntimeError) as exc:
        # Corrupt, truncated, encrypted, or unusually compressed parts.
        raise InvalidDataError(f"the workbook part {path!r} cannot be read: {exc}") from exc
    except ElementTree.ParseError as exc:
        raise InvalidDataError(f"the workbook part {path!r} is not valid XML") from exc


def _sheets(archive: zipfile.ZipFile) -> list[tuple[str, str]]:
    workbook = _xml(archive, "xl/workbook.xml")
    relations = _xml(archive, "xl/_rels/workbook.xml.rels")
    # Chart sheets and dialog sheets are tabs too, but hold no cells to check.
    targets = {
        rel.get("Id"): rel.get("Target", "")
        for rel in relations.iter(f"{_PKG_REL}Relationship")
        if rel.get("Type", "worksheet").rsplit("/", 1)[-1] == "worksheet"
    }
    sheets = []
    for sheet in workbook.iter(f"{_MAIN}sheet"):
        target = targets.get(sheet.get(f"{_REL}id"))
        if not target:
            continue
        path = target.lstrip("/") if target.startswith("/") else posixpath.normpath(f"xl/{target}")
        sheets.append((sheet.get("name", ""), path))
    if not sheets:
        raise InvalidDataError("the workbook has no worksheets")
    return sheets


def _shared_strings(archive: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []
    root = _xml(archive, "xl/sharedStrings.xml")
    return [_text_of(item) for item in root.iter(f"{_MAIN}si")]


def _text_of(element: ElementTree.Element) -> str:
    # Plain strings hold one <t>; rich text holds runs (<r><t>). Phonetic
    # guides (<rPh>) are reading aids, not content, so they are skipped.
    parts = []
    for child in element:
        if child.tag == f"{_MAIN}t":
            parts.append(child.text or "")
        elif child.tag == f"{_MAIN}r":
            parts.extend(text.text or "" for text in child.iter(f"{_MAIN}t"))
    return "".join(parts)


def _date_styles(archive: zipfile.ZipFile) -> frozenset[int]:
    if "xl/styles.xml" not in archive.namelist():
        return frozenset()
    root = _xml(archive, "xl/styles.xml")
    custom_dates = {
        int(fmt.get("numFmtId", "-1"))
        for fmt in root.iter(f"{_MAIN}numFmt")
        if _is_date_format(fmt.get("formatCode", ""))
    }
    cell_formats = root.find(f"{_MAIN}cellXfs")
    if cell_formats is None:
        return frozenset()
    return frozenset(
        index
        for index, xf in enumerate(cell_formats.iter(f"{_MAIN}xf"))
        if (fmt := int(xf.get("numFmtId", "0"))) in _DATE_FORMAT_IDS or fmt in custom_dates
    )


def _is_date_format(code: str) -> bool:
    stripped = _FORMAT_NOISE.sub("", code).lower()
    return stripped != "general" and any(token in stripped for token in "ydhms")


def _uses_1904_dates(archive: zipfile.ZipFile) -> bool:
    properties = _xml(archive, "xl/workbook.xml").find(f"{_MAIN}workbookPr")
    return properties is not None and properties.get("date1904") in {"1", "true"}


def _column_index(reference: str | None, previous: int) -> int:
    if not reference:
        return previous + 1
    match = _CELL_REF.match(reference)
    if match is None:
        raise InvalidDataError(f"the workbook has an unreadable cell reference {reference!r}")
    index = 0
    for letter in match.group(1):
        index = index * 26 + ord(letter) - 64
    return index - 1


def _cell_value(
    cell: ElementTree.Element,
    strings: list[str],
    date_styles: frozenset[int],
    date1904: bool,
    sheet: str,
) -> Any:
    kind = cell.get("t", "n")
    value = cell.find(f"{_MAIN}v")
    text = value.text if value is not None else None
    if kind == "inlineStr":
        inline = cell.find(f"{_MAIN}is")
        return None if inline is None else _text_of(inline)
    if text is None and kind == "str":
        return ""  # a formula whose saved result is empty text, such as =IF(..., "")
    if text is None:
        if cell.find(f"{_MAIN}f") is not None:
            raise InvalidDataError(
                f"cell {sheet}!{cell.get('r', '?')} holds a formula with no saved result; "
                "open the workbook in Excel and save it again"
            )
        return None
    if kind == "s":
        try:
            return strings[int(text)]
        except (ValueError, IndexError) as exc:
            raise InvalidDataError(f"cell {cell.get('r', '?')} refers to a missing string") from exc
    if kind in {"str", "e"}:
        return text
    if kind == "b":
        return text.strip() == "1"
    if kind == "d":
        try:
            return datetime.fromisoformat(text)
        except ValueError:
            return text
    number = _number(text)
    if int(cell.get("s", "0")) in date_styles:
        try:
            return _excel_date(number, date1904)
        except (OverflowError, ValueError) as exc:
            raise InvalidDataError(
                f"cell {sheet}!{cell.get('r', '?')} is formatted as a date but holds "
                f"{text}, which is not a valid date"
            ) from exc
    return number


def _number(text: str) -> int | Decimal:
    stripped = text.strip()
    if _INTEGER.match(stripped):
        try:
            return int(stripped)
        except ValueError:
            return Decimal(stripped)
    try:
        number = Decimal(stripped)
    except ArithmeticError as exc:
        raise InvalidDataError(f"the workbook has an unreadable number {text!r}") from exc
    # Excel writes whole numbers in exponent form only when they are huge.
    return int(number) if number == number.to_integral_value() and abs(number) < 10**15 else number


def _excel_date(serial: int | Decimal, date1904: bool) -> date | datetime | time:
    # Excel keeps times to the millisecond; exact arithmetic avoids float drift.
    milliseconds = int((Decimal(serial) * 86_400_000).to_integral_value())
    if milliseconds < 0:
        raise ValueError("negative date serial")
    if milliseconds < 86_400_000 and not date1904:
        # In the 1900 system a serial below 1 is a time of day with no date
        # (Excel shows 1900-01-00); in the 1904 system serial 0 is 1 Jan 1904.
        return (datetime.min + timedelta(milliseconds=milliseconds)).time()
    if date1904:
        base = datetime(1904, 1, 1)
    elif serial >= 61:
        # The 1900 system counts a fictitious 29 Feb 1900 (serial 60), so from
        # 1 March 1900 onwards serials are one day ahead of the calendar.
        base = datetime(1899, 12, 30)
    elif serial >= 60:
        raise ValueError("29 February 1900 does not exist")
    else:
        base = datetime(1899, 12, 31)
    moment = base + timedelta(milliseconds=milliseconds)
    if moment.time() == datetime.min.time():
        return moment.date()
    return moment


def _listed(names: Sequence[str]) -> str:
    return ", ".join(repr(name) for name in names)
