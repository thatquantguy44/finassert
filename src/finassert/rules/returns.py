"""Return consistency (specification 0002, milestone 3)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from finassert.core.models import Outcome, Severity, ValidationResult
from finassert.numerical import Numeric, Tolerance, coerce_tolerance
from finassert.rules._helpers import precise_quotient, precise_sum
from finassert.rules._rows import evaluate_rows
from finassert.rules.base import NullPolicy


class ReturnUnit(StrEnum):
    """How a file writes a return."""

    FRACTION = "fraction"
    """0.05 means 5%."""
    PERCENT = "percent"
    """5 means 5%."""


@dataclass(frozen=True, slots=True)
class SimpleReturnReconcilesRule:
    """Check ``return = (ending - beginning - net_flows) / beginning`` on every row.

    This is the simple one-period return: flows are assumed to happen at the
    end of the period, so it does not match a time-weighted or Modified Dietz
    return when money moves in or out during the period. ``net_flows`` is
    optional and counts money added to the portfolio as positive. A beginning
    value of zero has no return and fails. Use :func:`simple_return_reconciles`
    to build one.
    """

    beginning_value: str
    ending_value: str
    reported_return: str
    return_unit: ReturnUnit
    net_flows: str | None = None
    row_key: str | None = None
    tolerance: Tolerance = field(default_factory=Tolerance)
    null_policy: NullPolicy = NullPolicy.FAIL
    severity: Severity = Severity.ERROR
    max_violations: int = 20
    rule_id: str = "returns.simple_return_reconciles"
    name: str = "Reported return matches beginning and ending values"

    def __post_init__(self) -> None:
        if self.max_violations < 0:
            raise ValueError("max_violations must be non-negative")
        if self.null_policy is NullPolicy.IGNORE:
            raise ValueError(
                "null_policy 'ignore' is not allowed: a row with a blank value cannot be "
                "checked and must not be passed over silently; use 'fail' or 'skip'"
            )
        columns = [self.beginning_value, self.ending_value, self.reported_return]
        if self.net_flows is not None:
            columns.append(self.net_flows)
        if len(set(columns)) != len(columns):
            raise ValueError("each value must come from a different column")

    @property
    def equation(self) -> str:
        """Return the identity checked."""
        flows = " - net_flows" if self.net_flows else ""
        scale = " * 100" if self.return_unit is ReturnUnit.PERCENT else ""
        return f"return = (ending_value - beginning_value{flows}) / beginning_value{scale}"

    def evaluate(self, data: Any) -> ValidationResult:
        """Check every row."""
        scale = 100 if self.return_unit is ReturnUnit.PERCENT else 1

        def check(values: dict[str, Numeric]) -> dict[str, Any] | None:
            beginning = values["beginning_value"]
            observed = values["reported_return"]
            if beginning == 0:
                return {"reason": "zero_beginning_value", "observed": observed}
            gain = precise_sum([values["ending_value"], -beginning, -values.get("net_flows", 0)])
            expected = precise_quotient(gain, beginning) * scale
            if self.tolerance.is_close(observed, expected):
                return None
            return {
                "reason": "does_not_reconcile",
                "observed": observed,
                "expected": expected,
                "difference": precise_sum([observed, -expected]),
            }

        columns = {
            "beginning_value": self.beginning_value,
            "ending_value": self.ending_value,
            "reported_return": self.reported_return,
        }
        if self.net_flows:
            columns["net_flows"] = self.net_flows
        return evaluate_rows(
            self,
            data,
            columns,
            check,
            row_key=self.row_key,
            noun="return",
            description={
                "equation": self.equation,
                "return_unit": self.return_unit.value,
                "columns": columns,
            },
        )

    def _row_result(
        self,
        outcome: Outcome,
        message: str,
        metadata: dict[str, Any],
        *,
        observed: Any = None,
        expected: Any = None,
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


def simple_return_reconciles(
    *,
    beginning_value: str,
    ending_value: str,
    reported_return: str,
    return_unit: ReturnUnit | str,
    net_flows: str | None = None,
    row_key: str | None = None,
    tolerance: Numeric | Tolerance = 0,
    null_policy: NullPolicy | str = NullPolicy.FAIL,
    severity: Severity | str = Severity.ERROR,
    max_violations: int = 20,
) -> SimpleReturnReconcilesRule:
    """Create a rule checking that reported returns follow from the values.

    Args:
        beginning_value: Column with the value at the start of the period.
        ending_value: Column with the value at the end of the period.
        reported_return: Column with the return the file reports.
        return_unit: ``"fraction"`` (0.05 is 5%) or ``"percent"`` (5 is 5%).
            There is no default: a wrong guess is off by a factor of 100.
        net_flows: Optional column with money added (positive) or withdrawn
            (negative) during the period.
        row_key: Column used to label rows in the report.
        tolerance: Allowed difference, in the return's unit.
        null_policy: ``"fail"`` or ``"skip"`` when a value is blank.
        severity: Severity recorded with the result.
        max_violations: Maximum rows listed in the report.
    """
    return SimpleReturnReconcilesRule(
        beginning_value=beginning_value,
        ending_value=ending_value,
        reported_return=reported_return,
        return_unit=ReturnUnit(return_unit),
        net_flows=net_flows,
        row_key=row_key,
        tolerance=coerce_tolerance(tolerance),
        null_policy=NullPolicy(null_policy),
        severity=Severity(severity),
        max_violations=max_violations,
    )
