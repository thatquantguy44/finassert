"""Inspect worksheet visibility without loading a writable workbook."""

from __future__ import annotations

import io
import os
import re
import zipfile
from typing import Any
from xml.etree import ElementTree as ET

from finassert._xlsx import _MAIN, _sheets, _xml, column_letter
from finassert.core.exceptions import InvalidDataError


def workbook_region(
    source: bytes | str | os.PathLike[str],
    *,
    sheet: str,
    header_row: int,
    max_row: int,
    columns: set[int],
    hidden: str,
) -> dict[str, Any]:
    """Describe the selected region; include all cells or reject hidden inputs."""
    if hidden not in {"include", "reject"}:
        raise InvalidDataError("hidden must be 'include' or 'reject'")
    hidden_rows: list[int] = []
    row_count = 0
    hidden_columns: set[int] = set()
    try:
        with zipfile.ZipFile(
            io.BytesIO(source) if isinstance(source, bytes) else source
        ) as archive:
            path = dict(_sheets(archive))[sheet]
            workbook = _xml(archive, "xl/workbook.xml")
            state = next(
                item.get("state", "visible")
                for item in workbook.iter(f"{_MAIN}sheet")
                if item.get("name") == sheet
            )
            with archive.open(path) as handle:
                for _, element in ET.iterparse(handle, events=("end",)):
                    if element.tag == f"{_MAIN}row" and element.get("hidden") in {"1", "true"}:
                        number = int(element.attrib["r"])
                        if header_row <= number <= max_row:
                            row_count += 1
                            if len(hidden_rows) < 20:
                                hidden_rows.append(number)
                    elif element.tag == f"{_MAIN}col" and element.get("hidden") in {"1", "true"}:
                        first, last = int(element.attrib["min"]), int(element.attrib["max"])
                        hidden_columns.update(i for i in columns if first <= i + 1 <= last)
                    elif element.tag == f"{_MAIN}mergeCell":
                        ref = element.attrib["ref"]
                        match = re.fullmatch(r"[A-Z]+(\d+):[A-Z]+(\d+)", ref)
                        if match is None:
                            raise InvalidDataError(f"invalid merged range {ref!r}")
                        if int(match[1]) <= header_row <= int(match[2]):
                            raise InvalidDataError(
                                f"merged header range {ref} is ambiguous; use unmerged headers"
                            )
                    element.clear()
    except (KeyError, ValueError, ET.ParseError, zipfile.BadZipFile) as exc:
        raise InvalidDataError(f"cannot inspect workbook region: {exc}") from exc
    if hidden == "reject" and (state != "visible" or row_count or hidden_columns):
        raise InvalidDataError("selected workbook region contains hidden sheet, rows or columns")
    letters = [column_letter(i) for i in sorted(hidden_columns)]
    return {
        "hidden_region_policy": hidden,
        "sheet_state": state,
        "hidden_rows": {"count": row_count, "examples": hidden_rows, "truncated": row_count > 20},
        "hidden_columns": {
            "count": len(letters),
            "examples": letters[:20],
            "truncated": len(letters) > 20,
        },
    }
