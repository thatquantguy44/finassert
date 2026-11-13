"""Versioned report artifacts carrying run context."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from finassert._version import __version__
from finassert.core.models import ValidationReport

if TYPE_CHECKING:
    from finassert.policy.schema import Policy

ARTIFACT_SCHEMA_VERSION = 1


def build_artifact(
    report: ValidationReport,
    *,
    policy: Policy | None = None,
    input_locator: str | None = None,
    input_format: str | None = None,
    input_sheet: str | None = None,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    """Wrap a report with the context needed to audit or reproduce it.

    Args:
        report: Results to record.
        policy: Policy that produced the rules, if any; its digest is recorded.
        input_locator: Input description exactly as the user supplied it.
        input_format: Loader format used for the input.
        input_sheet: Worksheet read from a workbook input, if any.
        generated_at: Timestamp to record; defaults to the current UTC time.
    """
    moment = (generated_at or datetime.now(UTC)).astimezone(UTC)
    return {
        "schema_version": ARTIFACT_SCHEMA_VERSION,
        "tool": {"name": "finassert", "version": __version__},
        "generated_at": moment.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "policy": None if policy is None else policy.describe(),
        "input": _input_context(input_locator, input_format, input_sheet),
        "report": report.to_dict(),
    }


def artifact_to_json(artifact: dict[str, Any], *, indent: int | None = 2) -> str:
    """Serialize an artifact to deterministic JSON."""
    return json.dumps(artifact, indent=indent, sort_keys=True, allow_nan=False)


def _input_context(
    locator: str | None, input_format: str | None, sheet: str | None
) -> dict[str, Any] | None:
    if locator is None and input_format is None:
        return None
    context: dict[str, Any] = {"locator": locator, "format": input_format}
    if sheet is not None:
        context["sheet"] = sheet
    return context
