"""General arithmetic financial invariants."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from finassert.adapters._column import extract_column, extract_columns, is_missing
from finassert.core.models import Outcome, Severity, ValidationResult
from finassert.numerical import Numeric, Tolerance, coerce_tolerance, is_finite
from finassert.rules._helpers import is_blank, precise_sum
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


@dataclass(frozen=True, slots=True)
class InRangeRule:
    """Validate that every value of a column lies between a minimum and a maximum.

    Limits are inclusive, and the tolerance widens each of them: with a maximum of
    1 and a tolerance of 0.01, a value of 1.01 passes. Set a minimum, a maximum,
    or both. Use :func:`in_range` to build one.
    """

    column: str
    minimum: Numeric | None = None
    maximum: Numeric | None = None
    tolerance: Tolerance = field(default_factory=Tolerance)
    null_policy: NullPolicy = NullPolicy.FAIL
    severity: Severity = Severity.ERROR
    max_violations: int = 20
    row_key: str | None = None
    rule_id: str = "arithmetic.in_range"
    name: str = "Values are within their allowed range"

    def __post_init__(self) -> None:
        if self.max_violations < 0:
            raise ValueError("max_violations must be non-negative")
        for label, limit in (("minimum", self.minimum), ("maximum", self.maximum)):
            if limit is not None and not is_finite(limit):
                raise ValueError(f"{label} must be a finite number")
        if self.minimum is None and self.maximum is None:
            raise ValueError("set a minimum, a maximum, or both")
        if self.minimum is not None and self.maximum is not None and self.minimum > self.maximum:
            raise ValueError("minimum must not exceed maximum")
        if self.tolerance.relative != 0:
            raise ValueError("a range accepts only an absolute tolerance")

    def evaluate(self, data: Any) -> ValidationResult:
        """Evaluate every value against the limits, widened by the tolerance."""
        columns, labels = extract_columns(data, [self.column], row_key=self.row_key)
        values = columns[self.column]
        blank_rows = [labels[i] for i, value in enumerate(values) if is_blank(value)]
        if blank_rows and self.null_policy is NullPolicy.SKIP:
            return self._result(
                Outcome.SKIPPED,
                "Skipped because the configured column contains blank values.",
                metadata={"column": self.column, "missing_rows": blank_rows},
            )
        low = (
            None if self.minimum is None else precise_sum([self.minimum, -self.tolerance.absolute])
        )
        high = (
            None if self.maximum is None else precise_sum([self.maximum, self.tolerance.absolute])
        )
        violations: list[dict[str, Any]] = []
        invalid_rows: list[Any] = []
        checked = 0
        for label, value in zip(labels, values, strict=True):
            if is_blank(value):
                if self.null_policy is NullPolicy.FAIL:
                    invalid_rows.append(label)
                continue
            if not is_finite(value):
                invalid_rows.append(label)
                continue
            checked += 1
            if high is not None and value > high:
                assert self.maximum is not None
                violations.append(self._violation(label, value, "above_maximum", self.maximum))
            elif low is not None and value < low:
                assert self.minimum is not None
                violations.append(self._violation(label, value, "below_minimum", self.minimum))
        failed = bool(violations or invalid_rows)
        if failed:
            message = (
                f"Column {self.column!r} has {len(violations)} value(s) outside the allowed "
                f"range and {len(invalid_rows)} blank or non-numeric value(s)."
            )
        else:
            message = f"All {checked} checked value(s) in {self.column!r} are within range."
        return self._result(
            Outcome.FAILED if failed else Outcome.PASSED,
            message,
            observed=len(violations),
            expected=0,
            metadata={
                "column": self.column,
                "minimum": self.minimum,
                "maximum": self.maximum,
                "checked_count": checked,
                "violation_count": len(violations),
                "violations": violations[: self.max_violations],
                "violations_truncated": len(violations) > self.max_violations,
                "invalid_rows": invalid_rows[: self.max_violations],
            },
        )

    @staticmethod
    def _violation(label: Any, value: Numeric, reason: str, limit: Numeric) -> dict[str, Any]:
        distance = (
            precise_sum([value, -limit])
            if reason == "above_maximum"
            else precise_sum([limit, -value])
        )
        return {"row": label, "value": value, "reason": reason, "limit": limit, "beyond": distance}

    def _result(
        self,
        outcome: Outcome,
        message: str,
        *,
        observed: Any = None,
        expected: Any = None,
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


def in_range(
    *,
    column: str,
    minimum: Numeric | None = None,
    maximum: Numeric | None = None,
    tolerance: Numeric | Tolerance = 0,
    null_policy: NullPolicy | str = NullPolicy.FAIL,
    severity: Severity | str = Severity.ERROR,
    max_violations: int = 20,
    row_key: str | None = None,
) -> InRangeRule:
    """Create a rule requiring every value of a column to lie within limits.

    Args:
        column: Column to check.
        minimum: Lowest allowed value, inclusive.
        maximum: Highest allowed value, inclusive.
        tolerance: Absolute allowance beyond either limit, for rounding.
        null_policy: ``"fail"``, ``"ignore"``, or ``"skip"`` for blank cells.
        severity: Severity recorded with the result; below ``error`` it only warns.
        max_violations: Maximum offending rows listed in the report.
        row_key: Column used to label rows in the report, such as a ticker.
    """
    return InRangeRule(
        column=column,
        minimum=minimum,
        maximum=maximum,
        tolerance=coerce_tolerance(tolerance),
        null_policy=NullPolicy(null_policy),
        severity=Severity(severity),
        max_violations=max_violations,
        row_key=row_key,
    )
