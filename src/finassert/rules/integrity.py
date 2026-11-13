"""Data-integrity rules: duplicates and missing required values.

These check the shape of a file rather than a financial identity, so they hold
for any holdings, transaction, or reference file. They never normalize values:
``"AAPL"`` and ``"aapl "`` are different identifiers, and a cell of spaces is
blank but zero is a value.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from finassert.adapters._column import extract_columns
from finassert.core.models import Outcome, Severity, ValidationResult
from finassert.rules._diagnostics import Sample
from finassert.rules._grouping import _MAX_ROWS_LISTED
from finassert.rules._helpers import is_blank
from finassert.rules.base import NullPolicy


def _result(
    rule: NoDuplicatesRule | RequiredFieldsRule,
    outcome: Outcome,
    message: str,
    metadata: dict[str, Any],
    *,
    observed: Any = None,
    expected: Any = None,
) -> ValidationResult:
    return ValidationResult(
        rule_id=rule.rule_id,
        rule_name=rule.name,
        outcome=outcome,
        severity=rule.severity,
        message=message,
        observed=observed,
        expected=expected,
        metadata={"columns": list(rule.columns), **metadata},
    )


def _columns(columns: Sequence[str]) -> tuple[str, ...]:
    if isinstance(columns, str):
        raise TypeError("columns must be a list of column names")
    names = tuple(columns)
    if not names:
        raise ValueError("name at least one column")
    if any(not isinstance(name, str) or not name.strip() for name in names):
        raise ValueError("column names must be non-empty text")
    if len(set(names)) != len(names):
        raise ValueError("a column is named more than once")
    return names


@dataclass(frozen=True, slots=True)
class NoDuplicatesRule:
    """Check that no value, or combination of values, appears on two rows.

    Values are compared exactly. Rows with a blank in any key column cannot be
    compared: with ``null_policy`` ``fail`` they are listed as a failure,
    ``ignore`` leaves them out, and ``skip`` records the check as not run. Use
    :func:`no_duplicates` to build one.
    """

    columns: tuple[str, ...]
    null_policy: NullPolicy = NullPolicy.FAIL
    severity: Severity = Severity.ERROR
    max_violations: int = 20
    rule_id: str = "data.no_duplicates"
    name: str = "Each item appears only once"

    def __post_init__(self) -> None:
        _columns(self.columns)
        if self.max_violations < 0:
            raise ValueError("max_violations must be non-negative")

    def evaluate(self, data: Any) -> ValidationResult:
        """Find repeated keys without reordering or changing the data."""
        values, labels = extract_columns(data, self.columns)
        if not labels:
            return _result(self, Outcome.SKIPPED, "The file has no rows to check.", {})

        seen: dict[tuple[Any, ...], Sample[Any]] = {}
        blank_rows: Sample[Any] = Sample(self.max_violations)
        unhashable_rows: Sample[Any] = Sample(self.max_violations)
        for position, label in enumerate(labels):
            key = tuple(values[column][position] for column in self.columns)
            if any(is_blank(value) for value in key):
                blank_rows.add(label)
                continue
            try:
                rows = seen.get(key)
                if rows is None:
                    rows = Sample(_MAX_ROWS_LISTED)
                    seen[key] = rows
                rows.add(label)
            except TypeError:
                unhashable_rows.add(label)

        base = {"columns": list(self.columns), "row_count": len(labels)}
        if blank_rows and self.null_policy is NullPolicy.SKIP:
            return _result(
                self,
                Outcome.SKIPPED,
                f"Skipped because {blank_rows.count} row(s) have a blank key.",
                {
                    **base,
                    "blank_rows": blank_rows.examples,
                    "blank_row_count": blank_rows.count,
                },
            )
        duplicates: Sample[dict[str, Any]] = Sample(self.max_violations)
        duplicate_row_count = 0
        for key, rows in seen.items():
            if rows.count > 1:
                duplicate_row_count += rows.count
                duplicates.add(
                    {
                        "key": dict(zip(self.columns, key, strict=True)),
                        "count": rows.count,
                        "rows": rows.examples,
                    }
                )
        blanks_fail = bool(blank_rows) and self.null_policy is NullPolicy.FAIL
        failed = bool(duplicates or unhashable_rows or blanks_fail)
        metadata: dict[str, Any] = {
            **base,
            "checked_count": sum(rows.count for rows in seen.values()),
            "duplicate_key_count": duplicates.count,
            "duplicate_row_count": duplicate_row_count,
            "duplicates": duplicates.examples,
            "duplicates_truncated": duplicates.count > self.max_violations,
        }
        if blank_rows:
            metadata["blank_row_count"] = blank_rows.count
            if blanks_fail:
                metadata["blank_rows"] = blank_rows.examples
        if unhashable_rows:
            metadata["unusable_rows"] = unhashable_rows.examples
            metadata["unusable_row_count"] = unhashable_rows.count
        what = "/".join(self.columns)
        unit = "combination(s)" if len(self.columns) > 1 else "value(s)"
        parts = []
        if duplicates:
            parts.append(f"{duplicates.count} {what} {unit} appear on more than one row")
        if blanks_fail:
            parts.append(f"{blank_rows.count} row(s) have a blank key")
        if unhashable_rows:
            parts.append(f"{unhashable_rows.count} row(s) hold values that cannot be compared")
        message = (
            "; ".join(parts) + "."
            if failed
            else f"All {metadata['checked_count']} row(s) have a unique {what}."
        )
        return _result(
            self,
            Outcome.FAILED if failed else Outcome.PASSED,
            message,
            metadata,
            observed=duplicates.count,
            expected=0,
        )


@dataclass(frozen=True, slots=True)
class RequiredFieldsRule:
    """Check that none of the named columns has a blank cell on any row.

    A cell is blank when it is missing or holds only spaces. Zero and ``False``
    are values. Use :func:`required_fields` to build one.
    """

    columns: tuple[str, ...]
    severity: Severity = Severity.ERROR
    max_violations: int = 20
    rule_id: str = "data.required_fields"
    name: str = "Required fields are filled in"

    def __post_init__(self) -> None:
        _columns(self.columns)
        if self.max_violations < 0:
            raise ValueError("max_violations must be non-negative")

    def evaluate(self, data: Any) -> ValidationResult:
        """List each column's blank rows."""
        values, labels = extract_columns(data, self.columns)
        if not labels:
            return _result(self, Outcome.SKIPPED, "The file has no rows to check.", {})
        blanks: list[dict[str, Any]] = []
        for column in self.columns:
            rows = Sample[Any](self.max_violations)
            for label, value in zip(labels, values[column], strict=True):
                if is_blank(value):
                    rows.add(label)
            if rows:
                blanks.append(
                    {
                        "column": column,
                        "blank_count": rows.count,
                        "rows": rows.examples,
                        "rows_truncated": rows.truncated,
                    }
                )
        total = sum(item["blank_count"] for item in blanks)
        metadata = {
            "columns": list(self.columns),
            "row_count": len(labels),
            "blank_cell_count": total,
            "blank_column_count": len(blanks),
            "blank_cells": blanks,
        }
        if not blanks:
            return _result(
                self,
                Outcome.PASSED,
                f"All {len(labels)} row(s) have every required field filled in.",
                metadata,
                observed=0,
                expected=0,
            )
        detail = ", ".join(f"{item['column']} ({item['blank_count']})" for item in blanks)
        return _result(
            self,
            Outcome.FAILED,
            f"{total} required cell(s) are blank: {detail}.",
            metadata,
            observed=total,
            expected=0,
        )


def no_duplicates(
    *,
    columns: Sequence[str],
    null_policy: NullPolicy | str = NullPolicy.FAIL,
    severity: Severity | str = Severity.ERROR,
    max_violations: int = 20,
) -> NoDuplicatesRule:
    """Create a rule checking that a value, or combination, appears only once.

    Args:
        columns: Column, or columns taken together, that identify a row, such as
            ``["portfolio", "ticker"]``.
        null_policy: What to do with rows that have a blank key: ``"fail"``,
            ``"ignore"`` (leave them out), or ``"skip"``.
        severity: Severity recorded with the result.
        max_violations: Maximum repeated keys listed in the report.
    """
    return NoDuplicatesRule(
        columns=_columns(columns),
        null_policy=NullPolicy(null_policy),
        severity=Severity(severity),
        max_violations=max_violations,
    )


def required_fields(
    *,
    columns: Sequence[str],
    severity: Severity | str = Severity.ERROR,
    max_violations: int = 20,
) -> RequiredFieldsRule:
    """Create a rule checking that the named columns are never blank.

    Args:
        columns: Columns that must be filled in on every row.
        severity: Severity recorded with the result.
        max_violations: Maximum blank rows listed per column.
    """
    return RequiredFieldsRule(
        columns=_columns(columns), severity=Severity(severity), max_violations=max_violations
    )
