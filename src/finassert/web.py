"""JSON-in, JSON-out bridge used by the in-browser application.

The browser application runs this module under Pyodide. Every function takes
and returns JSON text so the JavaScript side holds no validation logic: rules,
policy checking, reports, and policy export all go through the same code paths
as the command line. This module is support code for that application, not a
stable public API.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from decimal import Decimal
from pathlib import Path
from typing import Any

from finassert._xlsx import SheetError
from finassert.core.exceptions import InvalidDataError, PolicyError
from finassert.excel import read_range, results_table
from finassert.loaders import TableSource, input_format_for, parse_csv, parse_json, parse_xlsx
from finassert.policy import (
    ParameterKind,
    default_catalog,
    dump_policy,
    get_template,
    parse_policy,
    parse_policy_text,
    policy_templates,
)
from finassert.policy.io import policy_format_for
from finassert.policy.suggest import TemplateFit, fit_template, suggest_templates
from finassert.reporting import artifact_to_json, build_artifact, render_artifact_html

_PREVIEW_ROWS = 5


def catalog() -> str:
    """Return the built-in rule catalog as JSON."""
    return json.dumps(default_catalog().to_dict())


def templates() -> str:
    """Return the starter policies in the editable form used by the application."""
    return json.dumps(
        {
            "templates": [
                {
                    "name": template.name,
                    "title": template.title,
                    "summary": template.summary,
                    "adapt": list(template.adapt),
                    "policy": _editable(template.policy().to_document()),
                }
                for template in policy_templates()
            ]
        }
    )


def suggest(columns_json: str, template: str = "") -> str:
    """Match templates to a file's columns and return each fit with its adapted policy.

    With no ``template`` the built-in templates that fit are ranked best first;
    with one, only that template is returned, however well it fits.
    """
    columns = [str(item) for item in json.loads(columns_json)]
    fits: tuple[TemplateFit, ...]
    if template:
        try:
            fits = (fit_template(get_template(template), columns),)
        except KeyError:
            return json.dumps({"ok": False, "error": f"Unknown template {template!r}."})
    else:
        fits = suggest_templates(columns)
    return json.dumps(
        {
            "ok": True,
            "suggestions": [
                {
                    **{key: item for key, item in fit.to_dict().items() if key != "document"},
                    "policy": _editable(fit.adapted().policy().to_document()),
                }
                for fit in fits
            ],
        }
    )


def inspect_input(
    content: Any, name: str, sheet: str | None = None, source_format: str | None = None
) -> str:
    """Parse an input file and return its columns, row count, and a preview.

    ``content`` is text for CSV and JSON and bytes for Excel workbooks. When a
    workbook has several sheets and none is chosen, the result lists them. With
    ``source_format`` ``"excel-range"``, ``content`` is the JSON of cells selected
    in Excel (see :func:`finassert.excel.read_range`) and ``name`` describes them.
    """
    try:
        data = _parse_input(content, name, sheet, source_format)
    except SheetError as exc:
        if sheet is None and exc.sheets:
            return json.dumps(
                {
                    "ok": False,
                    "sheets": list(exc.sheets),
                    "error": "This workbook has several sheets; choose the one to check.",
                }
            )
        return json.dumps({"ok": False, "error": str(exc)})
    except InvalidDataError as exc:
        return json.dumps({"ok": False, "error": str(exc)})
    if isinstance(data, TableSource):
        columns = list(data.column_names)
        rows = data.row_count
        preview = data.preview(_PREVIEW_ROWS)
    elif isinstance(data, Mapping):
        columns = [str(key) for key in data]
        rows = max((len(value) for value in data.values() if isinstance(value, list)), default=0)
        preview = [
            {
                key: value[index] if index < len(value) else None
                for key, value in data.items()
                if isinstance(value, list)
            }
            for index in range(min(rows, _PREVIEW_ROWS))
        ]
    else:
        columns = list(dict.fromkeys(str(key) for row in data for key in row))
        rows = len(data)
        preview = data[:_PREVIEW_ROWS]
    return json.dumps(
        {
            "ok": True,
            "columns": columns,
            "row_count": rows,
            "preview": [{str(k): _display(v) for k, v in row.items()} for row in preview],
            "notes": list(getattr(data, "notes", ())),
        }
    )


def read_policy(text: str, name: str) -> str:
    """Parse a policy file into the editable form used by the application."""
    try:
        policy = parse_policy_text(text, format=policy_format_for(Path(name)))
    except PolicyError as exc:
        return json.dumps({"ok": False, "issues": [issue.to_dict() for issue in exc.issues]})
    return json.dumps({"ok": True, "policy": _editable(policy.to_document())})


def run(
    content: Any,
    input_name: str,
    policy_json: str,
    sheet: str | None = None,
    source_format: str | None = None,
) -> str:
    """Validate an input against an edited policy and return every output.

    The result holds the HTML report, the JSON artifact, and the policy
    exported as YAML. The exported policy is the exact policy that was run.
    """
    try:
        policy = parse_policy(json.loads(policy_json, object_hook=_restore_number))
    except PolicyError as exc:
        return json.dumps({"ok": False, "issues": [issue.to_dict() for issue in exc.issues]})
    try:
        data = _parse_input(content, input_name, sheet, source_format)
    except InvalidDataError as exc:
        return json.dumps({"ok": False, "error": f"The data file could not be read: {exc}"})
    report = policy.check(data)
    artifact = build_artifact(
        report,
        policy=policy,
        input_locator=input_name,
        input_format=source_format or input_format_for(Path(input_name)),
        input_sheet=sheet,
    )
    return json.dumps(
        {
            "ok": True,
            "passed": report.passed,
            "warnings": len(report.warnings),
            "counts": report.counts_by_outcome,
            "html": render_artifact_html(artifact),
            "artifact_json": artifact_to_json(artifact) + "\n",
            "policy_yaml": dump_policy(policy),
        }
    )


def results_sheet(artifact_json: str) -> str:
    """Return a report as rows of cells for a results sheet in Excel."""
    return json.dumps({"rows": results_table(json.loads(artifact_json))})


def _parse_input(
    content: Any, name: str, sheet: str | None = None, source_format: str | None = None
) -> Any:
    if source_format == "excel-range":
        try:
            return read_range(json.loads(_as_text(content)))
        except (json.JSONDecodeError, TypeError) as exc:
            raise InvalidDataError(f"the selected cells could not be read: {exc}") from exc
    if source_format:
        raise InvalidDataError(f"unknown source format {source_format!r}")
    # Same format rules as the command line, so files the app accepts also run there.
    input_format = input_format_for(Path(name))
    if input_format == "xlsx":
        return parse_xlsx(_as_bytes(content), sheet=sheet)
    if sheet is not None:
        raise SheetError("a sheet can only be chosen for Excel (.xlsx) input", ())
    if input_format == "json":
        return parse_json(_as_text(content))
    if input_format == "csv":
        return parse_csv(_as_text(content))
    raise InvalidDataError(f"{input_format} files cannot be opened in the browser app")


def _as_bytes(content: Any) -> bytes:
    # Pyodide passes a JavaScript Uint8Array as a proxy with to_py().
    if hasattr(content, "to_py"):
        content = content.to_py()
    if isinstance(content, str):
        raise InvalidDataError("the workbook was read as text; open it again")
    return bytes(content)


def _as_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    try:
        return _as_bytes(content).decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise InvalidDataError("the file is not UTF-8 text; re-save it as 'CSV UTF-8'") from exc


_NUMERIC_KINDS = (ParameterKind.TOLERANCE, ParameterKind.NUMBER)


def _editable(document: dict[str, Any]) -> dict[str, Any]:
    """Return a policy document the browser can edit without changing it.

    Exact decimals become their text, which reads back as the same ``Decimal``.
    Binary floats and integers inside tolerances and numbers are tagged so an unedited value
    returns with its original type, keeping the policy fingerprint unchanged.
    """
    catalog = default_catalog()
    result = dict(document)
    rules = []
    for entry in document["rules"]:
        spec = catalog.resolve(entry["rule"])
        converted: dict[str, Any] = {}
        for key, value in entry.items():
            numeric = key != "rule" and spec.parameter(key).kind in _NUMERIC_KINDS
            converted[key] = _tag_number(value) if numeric else value
        rules.append(converted)
    result["rules"] = rules
    return result


def _tag_number(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _tag_number(item) for key, item in value.items()}
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, float):
        return {"$float": repr(value)}
    if isinstance(value, int) and not isinstance(value, bool):
        return {"$int": str(value)}
    return value


def _restore_number(value: dict[str, Any]) -> Any:
    if len(value) == 1 and isinstance(next(iter(value.values())), str):
        tag, text = next(iter(value.items()))
        try:
            if tag == "$float":
                return float(text)
            if tag == "$int":
                return int(text)
        except ValueError:
            return value
    return value


def _display(value: Any) -> Any:
    if value is None or isinstance(value, bool | int | str):
        return value
    return str(value)
