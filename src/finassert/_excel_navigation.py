"""Private, bounded navigation for live Excel results, before labels lose types.

Artifacts keep their canonical diagnostics unchanged. This session-only bridge
resolves retained examples against the parsed capture, never against row numbers
in a business key or a reconstructed population of failed rows.
"""

from __future__ import annotations

import json
import math
from typing import Any

from finassert.core.models import ValidationReport, _json_value
from finassert.loaders import TableSource
from finassert.policy.schema import Policy


def _wire_key(value: Any) -> str | None:
    """Match the identity a JSON/JavaScript consumer can actually distinguish."""
    if isinstance(value, (dict, list, tuple, set)) or value is None:
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if abs(value) > 2**53 - 1 or not math.isfinite(value):
            return None
        # JavaScript does not distinguish JSON 1 from 1.0.
        return "number:" + str(value if value % 1 else int(value))
    return json.dumps(_json_value(value), sort_keys=True, allow_nan=False)


def _rows(observation: dict[str, Any]) -> list[tuple[str, Any]]:
    rows = [("Row", observation["row"])] if "row" in observation else []
    if "previous_row" in observation:
        rows.append(("Previous row", observation["previous_row"]))
    if isinstance(observation.get("rows"), (list, tuple)):
        rows.extend(("Example row", value) for value in observation["rows"])
    return rows


def build_navigation(data: TableSource, policy: Policy, report: ValidationReport) -> dict[str, Any]:
    """Resolve only canonical retained examples; duplicate/colliding keys require rerun."""
    names = data.column_names
    _, native_rows = data.column(names[0])
    physical_rows = set(native_rows)
    results = []
    for entry, result in zip(policy.entries, report.results, strict=True):
        rule = entry.rule
        row_key = getattr(rule, "row_key", None) or getattr(
            getattr(rule, "mapping", None), "row_key", None
        )
        wanted = {
            key
            for collection in result.diagnostics
            for observation in collection.observations
            for _, label in _rows(observation)
            if (key := _wire_key(label)) is not None
        }
        # A single pass per effective key column, retaining at most one row and
        # a count per requested identity. Duplicates do not grow candidate lists.
        matches: dict[str, tuple[int, Any]] = {}
        if row_key in names:
            values, labels = data.column(row_key)
            for value, physical in zip(values, labels, strict=True):
                key = _wire_key(value)
                if key in wanted:
                    count, _ = matches.get(key, (0, None))
                    matches[key] = (count + 1, physical)

        collections = []
        for collection in result.diagnostics:
            samples = []
            for observation in collection.observations:
                column = observation.get("column", result.metadata.get("column"))
                column_index = (
                    names.index(column) if isinstance(column, str) and column in names else None
                )
                targets = []
                for role, label in _rows(observation):
                    target: dict[str, Any] = {
                        "role": role,
                        "label": _json_value(label),
                        "status": "unavailable",
                        "reason": "Row identity unresolved. Review the mapping and rerun.",
                    }
                    if row_key:
                        key = _wire_key(label)
                        count, physical = (
                            matches.get(key, (0, None)) if key is not None else (0, None)
                        )
                        if count > 1 or (key is None and isinstance(label, (int, float))):
                            target.update(
                                status="ambiguous",
                                reason=(
                                    "Ambiguous row key: duplicate or serialized collision. "
                                    "Choose a unique row key and rerun."
                                ),
                            )
                        elif count == 1 and type(physical) is int and physical in physical_rows:
                            target.update(
                                status="resolved",
                                row=physical,
                                column_index=column_index,
                                reason="",
                            )
                    elif type(label) is int and label in physical_rows:
                        target.update(
                            status="resolved", row=label, column_index=column_index, reason=""
                        )
                    targets.append(target)
                samples.append({"observation": _json_value(observation), "targets": targets})
            collections.append({**collection.to_dict(), "observations": samples})
        results.append(
            {
                "rule_id": result.rule_id,
                "title": result.rule_name,
                "outcome": result.outcome.value,
                "severity": result.severity.value,
                "message": result.message,
                "collections": collections,
            }
        )
    return {"version": 1, "results": results}
