"""Portfolio-level financial invariants."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from finassert.adapters._column import extract_column, is_missing
from finassert.adapters.contracts import ColumnMapping, FieldAggregation, GroupKey
from finassert.core.models import Outcome, Severity, ValidationResult
from finassert.numerical import Numeric, Tolerance, coerce_tolerance
from finassert.rules._grouping import Group, Wording, evaluate_groups
from finassert.rules._helpers import finite_numeric_values, precise_sum
from finassert.rules.base import NullPolicy

_WEIGHTS = Wording(
    action="check",
    passes="add up to 1",
    fails="do not add up to 1",
    unusable="cannot be checked",
    file_passes="adds up to 1",
    file_fails="does not add up to 1",
)


@dataclass(frozen=True, slots=True)
class WeightsSumToOneRule:
    """Validate that weights add to one within tolerance.

    With ``group_by`` empty, all rows form one portfolio and the result reports
    its total. With ``group_by`` naming columns, such as a portfolio code, each
    group of rows must add to one, and the result lists the groups that do not.
    """

    column: str = "weight"
    tolerance: Tolerance = field(default_factory=lambda: Tolerance(absolute=1e-8))
    null_policy: NullPolicy = NullPolicy.FAIL
    severity: Severity = Severity.ERROR
    rule_id: str = "portfolio.weights_sum_to_one"
    name: str = "Portfolio weights sum to one"
    group_by: tuple[str, ...] = ()
    max_violations: int = 20

    def __post_init__(self) -> None:
        if self.max_violations < 0:
            raise ValueError("max_violations must be non-negative")
        if self.column in self.group_by:
            raise ValueError("group_by must not include the weight column")
        self._mapping()  # rejects empty or repeated grouping columns

    def evaluate(self, data: Any) -> ValidationResult:
        """Evaluate the invariant without modifying or normalizing weights."""
        if self.group_by:
            return self._evaluate_groups(data)
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
        skipped = set(missing)
        usable = [value for index, value in enumerate(values) if index not in skipped]
        usable_labels = [label for index, label in enumerate(labels) if index not in skipped]
        if not usable:
            return self._result(Outcome.FAILED, "No weights were available to sum.", observed=None)
        numeric, invalid = finite_numeric_values(usable)
        if invalid:
            return self._result(
                Outcome.FAILED,
                f"Weight column contains {len(invalid)} non-numeric or non-finite value(s).",
                metadata={
                    "invalid_positions": invalid,
                    "invalid_rows": [usable_labels[position] for position in invalid],
                },
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

    @property
    def mapping(self) -> ColumnMapping:
        """Return the grouped column mapping used when ``group_by`` is set."""
        return self._mapping()

    def _mapping(self) -> ColumnMapping:
        return ColumnMapping(
            {"weight": self.column},
            group_keys=tuple(GroupKey(column, column) for column in self.group_by),
            aggregations={"weight": FieldAggregation.SUM},
        )

    def _evaluate_groups(self, data: Any) -> ValidationResult:
        mapping = self._mapping()

        def check(group: Group) -> dict[str, Any] | None:
            if not group.values["weight"]:
                return {"reason": "no_weights"}
            total = group.aggregate("weight", mapping)
            expected: Numeric = Decimal(1) if isinstance(total, Decimal) else 1
            if self.tolerance.is_close(total, expected):
                return None
            return {
                "reason": "weights_do_not_sum_to_one",
                "observed": total,
                "expected": expected,
                "difference": precise_sum([total, -expected]),
            }

        return evaluate_groups(
            self,
            data,
            ("weight",),
            check,
            blank_allowed=("weight",) if self.null_policy is NullPolicy.IGNORE else (),
            wording=_WEIGHTS,
            description={
                "column": self.column,
                "equation": "sum(weight) = 1",
                "group_by": list(self.group_by),
            },
        )

    def _grouped_result(
        self,
        outcome: Outcome,
        message: str,
        metadata: dict[str, Any],
        *,
        observed: Any = None,
        expected: Any = None,
    ) -> ValidationResult:
        return self._result(
            outcome, message, observed=observed, expected=expected, metadata=metadata
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
    group_by: Sequence[str] = (),
    max_violations: int = 20,
) -> WeightsSumToOneRule:
    """Create a rule checking that weights add up to one.

    Args:
        column: Column holding each row's weight as a fraction of 1.
        tolerance: Allowed difference of the total from 1.
        null_policy: ``"fail"``, ``"ignore"``, or ``"skip"`` for blank weights.
        severity: Severity recorded with the result.
        group_by: Columns identifying each portfolio. When given, every group
            must add up to one; when empty, the whole file is one portfolio.
        max_violations: Maximum failing groups listed in a grouped result.
    """
    if isinstance(group_by, str):
        raise TypeError("group_by must be a list of column names")
    return WeightsSumToOneRule(
        column=column,
        tolerance=coerce_tolerance(tolerance),
        null_policy=NullPolicy(null_policy),
        severity=Severity(severity),
        group_by=tuple(group_by),
        max_violations=max_violations,
    )
