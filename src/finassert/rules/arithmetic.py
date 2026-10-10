"""General arithmetic financial invariants."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from finassert.adapters._column import extract_column, is_missing
from finassert.core.models import Outcome, Severity, ValidationResult
from finassert.numerical import Numeric, Tolerance, coerce_tolerance, is_finite
from finassert.rules.base import NullPolicy


@dataclass(frozen=True, slots=True)
class NonNegativeRule:
    """Validate that selected financial values are not below zero."""

    column: str
    tolerance: Tolerance = field(default_factory=Tolerance)
    null_policy: NullPolicy = NullPolicy.FAIL
    severity: Severity = Severity.ERROR
    max_violations: int = 20
    rule_id: str = "arithmetic.non_negative"
    name: str = "Financial values are nonnegative"

    def evaluate(self, data: Any) -> ValidationResult:
        """Evaluate values against ``-absolute_tolerance`` inclusively."""
        values, labels = extract_column(data, self.column)
        missing_rows = [labels[index] for index, value in enumerate(values) if is_missing(value)]
        if missing_rows and self.null_policy is NullPolicy.SKIP:
            return self._result(
                Outcome.SKIPPED,
                "Skipped because the configured column contains missing values.",
                metadata={"missing_rows": missing_rows},
            )
        violations: list[dict[str, Any]] = []
        invalid_rows: list[Any] = []
        checked = 0
        for label, value in zip(labels, values, strict=True):
            if is_missing(value):
                if self.null_policy is NullPolicy.FAIL:
                    invalid_rows.append(label)
                continue
            if not is_finite(value):
                invalid_rows.append(label)
                continue
            checked += 1
            threshold = _negative_absolute(self.tolerance.absolute, value)
            if value < threshold:
                violations.append({"row": label, "value": value})
        failed = bool(violations or invalid_rows)
        if failed:
            message = (
                f"Column {self.column!r} has {len(violations)} value(s) below the allowed "
                f"minimum and {len(invalid_rows)} missing/non-finite value(s)."
            )
        else:
            message = f"All {checked} checked value(s) in {self.column!r} are nonnegative."
        return self._result(
            Outcome.FAILED if failed else Outcome.PASSED,
            message,
            observed=len(violations),
            expected=0,
            metadata={
                "column": self.column,
                "checked_count": checked,
                "violation_count": len(violations),
                "violations": violations[: self.max_violations],
                "violations_truncated": len(violations) > self.max_violations,
                "invalid_rows": invalid_rows[: self.max_violations],
            },
        )

    def _result(
        self,
        outcome: Outcome,
        message: str,
        *,
        observed: Any = None,
        expected: Any = 0,
        metadata: dict[str, Any] | None = None,
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
            metadata=metadata or {"column": self.column},
        )


def _negative_absolute(tolerance: Numeric, value: Numeric) -> Numeric:
    if isinstance(value, Decimal):
        converted = tolerance if isinstance(tolerance, Decimal) else Decimal(str(tolerance))
        return -converted
    return -tolerance


def non_negative(
    *,
    column: str,
    tolerance: Numeric | Tolerance = 0,
    null_policy: NullPolicy | str = NullPolicy.FAIL,
    severity: Severity | str = Severity.ERROR,
    max_violations: int = 20,
) -> NonNegativeRule:
    """Create a rule for fields whose financial semantics require nonnegativity."""
    if max_violations < 0:
        raise ValueError("max_violations must be non-negative")
    return NonNegativeRule(
        column=column,
        tolerance=coerce_tolerance(tolerance),
        null_policy=NullPolicy(null_policy),
        severity=Severity(severity),
        max_violations=max_violations,
    )
