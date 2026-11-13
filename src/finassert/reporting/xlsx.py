"""Optional, atomic Excel report export with literal text cells."""

from __future__ import annotations

import io
import json
import re
from os import PathLike
from pathlib import Path
from typing import Any

from finassert._files import write_atomic
from finassert.core.models import ValidationReport
from finassert.reporting.artifact import build_artifact


def write_report_xlsx(
    report: ValidationReport,
    path: str | PathLike[str],
    *,
    artifact: dict[str, Any] | None = None,
) -> None:
    """Write Summary, Results, and bounded Diagnostics sheets atomically.

    Decimal values and formula-like strings are literal text. This creates a
    separate report and never modifies an input workbook. Requires the ``excel``
    extra. An optional matching artifact preserves the run's original context.
    """
    try:
        from openpyxl import Workbook
    except ImportError as exc:
        raise ImportError("XLSX reports require 'finassert[excel]'") from exc
    context = artifact if artifact is not None else build_artifact(report)
    if context.get("report") != report.to_dict():
        raise ValueError("artifact report does not match the supplied report")
    book = Workbook()
    summary = book.active
    summary.title = "Summary"
    rows: list[list[Any]] = [
        ["Outcome", "Count"],
        *[[key, value] for key, value in report.counts_by_outcome.items()],
        ["Report passed", report.passed],
        ["Schema version", context["schema_version"]],
        ["Tool version", context["tool"]["version"]],
        ["Generated (UTC)", context["generated_at"]],
        ["Input", (context.get("input") or {}).get("locator")],
        ["Policy digest", (context.get("policy") or {}).get("digest")],
    ]
    _rows(summary, rows)
    results = book.create_sheet("Results")
    headings = [
        "rule_id",
        "rule_name",
        "outcome",
        "severity",
        "message",
        "observed",
        "expected",
        "tolerance",
        "metadata",
    ]
    _rows(
        results,
        [headings, *[[result.to_dict()[key] for key in headings] for result in report.results]],
    )
    diagnostics = book.create_sheet("Diagnostics")
    details: list[list[Any]] = [["rule_id", "kind", "count", "limit", "truncated", "observation"]]
    for result in report.results:
        for collection in result.diagnostics:
            if collection.count == 0:
                continue
            observations = collection.to_dict()["observations"]
            for observation in observations or [None]:
                details.append(
                    [
                        result.rule_id,
                        collection.kind,
                        collection.count,
                        collection.limit,
                        collection.truncated,
                        observation,
                    ]
                )
    _rows(diagnostics, details)
    try:
        buffer = io.BytesIO()
        book.save(buffer)
        write_atomic(Path(path), buffer.getvalue())
    finally:
        book.close()


def _rows(sheet: Any, rows: list[list[Any]]) -> None:
    for row in rows:
        sheet.append([_cell(value) for value in row])
        for cell in sheet[sheet.max_row]:
            if isinstance(cell.value, str):
                cell.data_type = "s"
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions


def _cell(value: Any) -> Any:
    if isinstance(value, dict | list):
        value = json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)
    if isinstance(value, str):
        if len(value) > 32767:
            raise ValueError("report cell text exceeds Excel's 32767-character limit")
        if re.search(r"[\x00-\x08\x0b-\x0c\x0e-\x1f]", value):
            raise ValueError("report cell text contains characters Excel cannot store")
    return value
