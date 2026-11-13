"""Normalize built-in diagnostic collections without changing validation truth."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from finassert.core.models import DiagnosticCollection, ValidationResult

_COUNTS = {
    "missing_rows": "missing_row_count",
    "invalid_rows": "invalid_row_count",
    "violations": "violation_count",
    "failed_groups": "failed_group_count",
    "failed_rows": "failed_count",
    "unusable_rows": "unusable_row_count",
    "blank_rows": "blank_row_count",
    "duplicates": "duplicate_key_count",
    "blank_cells": "blank_column_count",
}


def normalize_diagnostics(result: ValidationResult, limit: int) -> ValidationResult:
    """Attach canonical collections for declared rule diagnostics, retaining metadata.

    The rule supplies full counts before applying any cap. Unknown metadata stays
    untouched; custom rules opt in by declaring ``max_violations``.
    """
    if type(limit) is not int or limit < 0:
        raise ValueError("max_violations must be a nonnegative integer")
    metadata = dict(result.metadata)
    collections: list[DiagnosticCollection] = []
    for kind, count_key in _COUNTS.items():
        entries = metadata.get(kind)
        if not isinstance(entries, list):
            continue
        count = metadata.get(count_key, len(entries))
        if type(count) is not int or count < len(entries):
            raise ValueError(f"invalid diagnostic total for {kind}")
        bounded = entries[:limit]
        metadata[kind] = bounded
        observations: tuple[dict[str, Any], ...] = tuple(
            dict(entry) if isinstance(entry, dict) else {"row": entry} for entry in bounded
        )
        collections.append(DiagnosticCollection(kind, count, limit, observations))
    # Filtered positions are legacy aliases of invalid_rows, not a second population.
    if isinstance(metadata.get("invalid_positions"), list):
        metadata["invalid_positions"] = metadata["invalid_positions"][:limit]
    return replace(result, metadata=metadata, diagnostics=tuple(collections))
