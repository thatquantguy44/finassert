"""Private version-1 provenance for verified live Excel snapshots."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Literal, NotRequired, TypedDict, cast


class ExcelContext(TypedDict):
    schema_version: int
    kind: Literal["range", "table"]
    worksheet_name: str
    worksheet_id: str
    table_name: NotRequired[str]
    table_id: NotRequired[str]
    address: str
    header_row: int
    data_row_count: int
    physical_data_row_count: int
    column_count: int
    hidden_rows: Literal["include_all"]
    date_system: Literal["1900", "1904"]
    date_system_source: Literal["user", "host"]
    captured_at: str
    verified_at: str
    snapshot_sha256: str


def parse_context(raw: Any) -> ExcelContext:
    """Accept only allowlisted scalar provenance, never records or session maps."""
    optional = {"table_name", "table_id"}
    required = set(ExcelContext.__annotations__) - optional
    if not isinstance(raw, dict) or set(raw) - required - optional or required - set(raw):
        raise ValueError("Excel source context has missing or unknown fields")
    if type(raw["schema_version"]) is not int or raw["schema_version"] != 1:
        raise ValueError("unsupported Excel source schema_version")
    for key, choices in {
        "kind": ("range", "table"),
        "hidden_rows": ("include_all",),
        "date_system": ("1900", "1904"),
        "date_system_source": ("user", "host"),
    }.items():
        if raw[key] not in choices:
            raise ValueError(f"invalid Excel {key}")
    table_keys = set(raw) & optional
    if table_keys != (optional if raw["kind"] == "table" else set()):
        raise ValueError("table identity is required only for a table source")
    for key in ("worksheet_name", "worksheet_id", "address", *table_keys):
        if not isinstance(raw[key], str) or not raw[key].strip():
            raise ValueError(f"Excel {key} must be nonempty text")
    for key, maximum in (
        ("header_row", 1048576),
        ("data_row_count", 1048575),
        ("physical_data_row_count", 1048575),
        ("column_count", 16384),
    ):
        if type(raw[key]) is not int or not 1 <= raw[key] <= maximum:
            raise ValueError(f"invalid Excel {key}")
    if (
        raw["data_row_count"] > raw["physical_data_row_count"]
        or raw["header_row"] + raw["physical_data_row_count"] > 1048576
        or (raw["physical_data_row_count"] + 1) * raw["column_count"] > 5_000_000
    ):
        raise ValueError("Excel source counts exceed the captured bounds")
    moments = []
    for key in ("captured_at", "verified_at"):
        value = raw[key]
        if not isinstance(value, str) or not re.fullmatch(
            r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,6})?Z", value
        ):
            raise ValueError(f"Excel {key} must be a UTC timestamp ending in Z")
        moments.append(datetime.fromisoformat(value[:-1] + "+00:00"))
    if moments[1] < moments[0]:
        raise ValueError("Excel verification cannot precede capture")
    if not isinstance(raw["snapshot_sha256"], str) or not re.fullmatch(
        r"sha256:[0-9a-f]{64}", raw["snapshot_sha256"]
    ):
        raise ValueError("invalid Excel snapshot_sha256")
    return cast(ExcelContext, dict(raw))


def context_rows(context: dict[str, Any]) -> list[tuple[str, Any]]:
    """Shared literal provenance labels for HTML and worksheet views."""
    return [
        ("Evidence", "Captured snapshot; later edits require a new run."),
        *[("Excel " + key.replace("_", " "), value) for key, value in sorted(context.items())],
    ]
