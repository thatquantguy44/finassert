"""Format structured reports for humans and machines."""

from __future__ import annotations

import json

from finassert.core.models import ValidationReport


def to_json(report: ValidationReport, *, indent: int | None = 2) -> str:
    """Serialize a report to deterministic JSON."""
    return json.dumps(report.to_dict(), indent=indent, sort_keys=True, allow_nan=False)


def to_text(report: ValidationReport) -> str:
    """Render a concise terminal representation."""
    return report.summary()
