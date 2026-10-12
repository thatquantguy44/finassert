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

from finassert.core.exceptions import InvalidDataError, PolicyError
from finassert.loaders import TableSource, input_format_for, parse_csv, parse_json
from finassert.policy import (
    ParameterKind,
    default_catalog,
    dump_policy,
    parse_policy,
    parse_policy_text,
)
from finassert.policy.io import policy_format_for
from finassert.reporting import artifact_to_json, build_artifact, render_artifact_html

_PREVIEW_ROWS = 5


def catalog() -> str:
    """Return the built-in rule catalog as JSON."""
    return json.dumps(default_catalog().to_dict())


def inspect_input(text: str, name: str) -> str:
    """Parse an input file and return its columns, row count, and a preview."""
    try:
        data = _parse_input(text, name)
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
        }
    )


def read_policy(text: str, name: str) -> str:
    """Parse a policy file into the editable form used by the application."""
    try:
        policy = parse_policy_text(text, format=policy_format_for(Path(name)))
    except PolicyError as exc:
        return json.dumps({"ok": False, "issues": [issue.to_dict() for issue in exc.issues]})
    return json.dumps({"ok": True, "policy": _editable(policy.to_document())})


def run(input_text: str, input_name: str, policy_json: str) -> str:
    """Validate an input against an edited policy and return every output.

    The result holds the HTML report, the JSON artifact, and the policy
    exported as YAML. The exported policy is the exact policy that was run.
    """
    try:
        policy = parse_policy(json.loads(policy_json, object_hook=_restore_number))
    except PolicyError as exc:
        return json.dumps({"ok": False, "issues": [issue.to_dict() for issue in exc.issues]})
    try:
        data = _parse_input(input_text, input_name)
    except InvalidDataError as exc:
        return json.dumps({"ok": False, "error": f"The data file could not be read: {exc}"})
    report = policy.check(data)
    artifact = build_artifact(
        report,
        policy=policy,
        input_locator=input_name,
        input_format=input_format_for(Path(input_name)),
    )
    return json.dumps(
        {
            "ok": True,
            "passed": report.passed,
            "counts": report.counts_by_outcome,
            "html": render_artifact_html(artifact),
            "artifact_json": artifact_to_json(artifact) + "\n",
            "policy_yaml": dump_policy(policy),
        }
    )


def _parse_input(text: str, name: str) -> Any:
    # Same format rules as the command line, so files the app accepts also run there.
    if input_format_for(Path(name)) == "json":
        return parse_json(text)
    return parse_csv(text)


def _editable(document: dict[str, Any]) -> dict[str, Any]:
    """Return a policy document the browser can edit without changing it.

    Exact decimals become their text, which reads back as the same ``Decimal``.
    Binary floats and integers inside tolerances are tagged so an unedited value
    returns with its original type, keeping the policy fingerprint unchanged.
    """
    catalog = default_catalog()
    result = dict(document)
    rules = []
    for entry in document["rules"]:
        spec = catalog.resolve(entry["rule"])
        converted: dict[str, Any] = {}
        for key, value in entry.items():
            is_tolerance = key != "rule" and spec.parameter(key).kind is ParameterKind.TOLERANCE
            converted[key] = _tag_number(value) if is_tolerance else value
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
