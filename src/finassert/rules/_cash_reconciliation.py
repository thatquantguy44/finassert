"""Private grouped cash-reconciliation prototype.

This module is an architectural spike, not a supported public API. It validates
the adapter and diagnostic contracts needed before an accounting rule is
exported from :mod:`finassert.rules`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, ClassVar

from finassert.adapters._column import extract_columns, is_missing
from finassert.adapters.contracts import ColumnMapping
from finassert.core.exceptions import InvalidDataError
from finassert.core.models import Outcome, Severity, ValidationResult
from finassert.numerical import Numeric, Tolerance, is_finite
from finassert.rules._helpers import precise_sum


@dataclass(frozen=True, slots=True)
class _GroupedCashReconciliationRule:
    """Prototype additive cash reconciliation over ordered groups.

    Each row is an additive reconciliation slice using the convention
    ``opening_cash + inflows - outflows + cash_pnl = closing_cash``.
    Currency conversion is never attempted; callers must include currency as a
    group key whenever a dataset can contain more than one currency.
    """

    mapping: ColumnMapping
    tolerance: Tolerance = field(default_factory=lambda: Tolerance(absolute=0))
    severity: Severity = Severity.ERROR
    max_groups: int = 20
    rule_id: str = "_prototype.accounting.grouped_cash_reconciliation"
    name: str = "Grouped cash reconciliation prototype"

    _SEMANTICS: ClassVar[tuple[str, ...]] = (
        "opening_cash",
        "inflows",
        "outflows",
        "cash_pnl",
        "closing_cash",
    )

    def __post_init__(self) -> None:
        if self.max_groups < 0:
            raise ValueError("max_groups must be non-negative")
        self.mapping.required_columns(*self._SEMANTICS)

    def evaluate(self, data: Any) -> ValidationResult:
        """Aggregate additive slices and compare expected closing cash by group."""
        semantic_columns = dict(
            zip(
                self._SEMANTICS,
                self.mapping.required_columns(*self._SEMANTICS),
                strict=True,
            )
        )
        physical_columns = [*semantic_columns.values(), *self.mapping.grouping_columns]
        columns, row_labels = extract_columns(
            data,
            physical_columns,
            row_key=self.mapping.row_key,
        )
        if not row_labels:
            return self._result(
                Outcome.SKIPPED,
                "No reconciliation observations were available.",
                metadata={"group_count": 0, "failed_group_count": 0},
            )

        grouped: dict[tuple[Any, ...], dict[str, list[Numeric]]] = {}
        invalid_rows: list[dict[str, Any]] = []
        for position, row_label in enumerate(row_labels):
            group = tuple(columns[key.column][position] for key in self.mapping.group_keys)
            if any(is_missing(value) for value in group):
                raise InvalidDataError(f"row {row_label!r} has a missing group key")

            row_values = {
                semantic: columns[column][position] for semantic, column in semantic_columns.items()
            }
            invalid_fields = [
                semantic
                for semantic, value in row_values.items()
                if is_missing(value) or not is_finite(value)
            ]
            if invalid_fields:
                invalid_rows.append({"row": row_label, "fields": invalid_fields})
                continue

            bucket = grouped.setdefault(group, {semantic: [] for semantic in self._SEMANTICS})
            for semantic, value in row_values.items():
                bucket[semantic].append(value)

        if invalid_rows:
            return self._result(
                Outcome.FAILED,
                f"Cash inputs contain {len(invalid_rows)} invalid row(s).",
                metadata={
                    "invalid_row_count": len(invalid_rows),
                    "invalid_rows": invalid_rows[: self.max_groups],
                    "invalid_rows_truncated": len(invalid_rows) > self.max_groups,
                },
            )

        failed_groups: list[dict[str, Any]] = []
        for group, values in grouped.items():
            totals = {semantic: precise_sum(items) for semantic, items in values.items()}
            expected = precise_sum(
                [
                    totals["opening_cash"],
                    totals["inflows"],
                    -totals["outflows"],
                    totals["cash_pnl"],
                ]
            )
            observed = totals["closing_cash"]
            if not self.tolerance.is_close(observed, expected):
                failed_groups.append(
                    {
                        "group": {
                            key.name: value
                            for key, value in zip(self.mapping.group_keys, group, strict=True)
                        },
                        "observed": observed,
                        "expected": expected,
                        "difference": precise_sum([observed, -expected]),
                        "row_count": len(values["closing_cash"]),
                    }
                )

        failed_count = len(failed_groups)
        group_count = len(grouped)
        outcome = Outcome.FAILED if failed_count else Outcome.PASSED
        message = (
            f"{failed_count} of {group_count} cash reconciliation group(s) failed."
            if failed_count
            else f"All {group_count} cash reconciliation group(s) passed."
        )
        return self._result(
            outcome,
            message,
            observed=failed_count,
            expected=0,
            metadata={
                "group_count": group_count,
                "failed_group_count": failed_count,
                "failed_groups": failed_groups[: self.max_groups],
                "failed_groups_truncated": failed_count > self.max_groups,
                "group_keys": [key.name for key in self.mapping.group_keys],
            },
        )

    def _result(
        self,
        outcome: Outcome,
        message: str,
        *,
        observed: Any = None,
        expected: Any = None,
        metadata: dict[str, Any],
    ) -> ValidationResult:
        return ValidationResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            outcome=outcome,
            severity=self.severity,
            message=message,
            observed=observed,
            expected=expected,
            tolerance=self.tolerance.to_dict(),
            metadata=metadata,
        )
