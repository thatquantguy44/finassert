"""Portfolio-level financial invariants."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from finassert.adapters._column import extract_column, is_missing
from finassert.core.models import Outcome, Severity, ValidationResult
from finassert.numerical import Numeric, Tolerance, coerce_tolerance
from finassert.rules._helpers import finite_numeric_values, precise_sum
from finassert.rules.base import NullPolicy


@dataclass(frozen=True, slots=True)
class WeightsSumToOneRule:
    """Validate that a portfolio's weights add to one within tolerance."""

    column: str = "weight"
    tolerance: Tolerance = field(default_factory=lambda: Tolerance(absolute=1e-8))
    null_policy: NullPolicy = NullPolicy.FAIL
    severity: Severity = Severity.ERROR
    rule_id: str = "portfolio.weights_sum_to_one"
    name: str = "Portfolio weights sum to one"

    def evaluate(self, data: Any) -> ValidationResult:
        """Evaluate the invariant without modifying or normalizing weights."""
        values, labels = extract_column(data, self.column)
        missing = [index for index, value in enumerate(values) if is_missing(value)]
        if missing and self.null_policy is NullPolicy.SKIP:
            return self._result(
                Outcome.SKIPPED,
                "Skipped because the weight column contains missing values.",
                metadata={"missing_rows": [labels[index] for index in missing]},
            )
        if missing and self.null_policy is NullPolicy.FAIL:
            return self._result(
                Outcome.FAILED,
                f"Weight column contains {len(missing)} missing value(s).",
                metadata={"missing_rows": [labels[index] for index in missing]},
            )
        usable = [value for index, value in enumerate(values) if index not in missing]
        if not usable:
            return self._result(Outcome.FAILED, "No weights were available to sum.", observed=None)
        numeric, invalid = finite_numeric_values(usable)
        if invalid:
            return self._result(
                Outcome.FAILED,
                f"Weight column contains {len(invalid)} non-numeric or non-finite value(s).",
                metadata={"invalid_positions": invalid},
            )
        total = precise_sum(numeric)
        expected: Numeric = Decimal(1) if isinstance(total, Decimal) else 1
        passed = self.tolerance.is_close(total, expected)
        message = (
            f"Weight total {total!s} is within tolerance of 1."
            if passed
            else f"Weight total {total!s} is not within tolerance of 1."
        )
        return self._result(
            Outcome.PASSED if passed else Outcome.FAILED,
            message,
            observed=total,
            expected=expected,
            metadata={"column": self.column, "observation_count": len(numeric)},
        )

    def _result(
        self,
        outcome: Outcome,
        message: str,
        *,
        observed: Any = None,
        expected: Any = 1,
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


def weights_sum_to_one(
    *,
    column: str = "weight",
    tolerance: Numeric | Tolerance = 1e-8,
    null_policy: NullPolicy | str = NullPolicy.FAIL,
    severity: Severity | str = Severity.ERROR,
) -> WeightsSumToOneRule:
    """Create a portfolio-weight summation rule."""
    return WeightsSumToOneRule(
        column=column,
        tolerance=coerce_tolerance(tolerance),
        null_policy=NullPolicy(null_policy),
        severity=Severity(severity),
    )
