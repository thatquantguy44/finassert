"""Exposure limits (specification 0002, milestone 3).

Exposure is measured per group, for example per portfolio or per portfolio and
sector, either directly on weights or as a fraction of a base such as the NAV.
Limits are inclusive. Currencies are never converted: a file in several
currencies should name its currency column so each is checked separately.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from finassert.adapters.contracts import ColumnMapping, FieldAggregation
from finassert.core.models import Outcome, Severity, ValidationResult
from finassert.numerical import Numeric, is_finite
from finassert.rules._grouping import (
    Group,
    Wording,
    currency_note,
    evaluate_groups,
    group_keys_for,
)
from finassert.rules._helpers import precise_product, precise_quotient, precise_sum
from finassert.rules.base import NullPolicy

_WITHIN = Wording(
    action="check",
    passes="are within the limit",
    fails="are outside the limit",
    unusable="cannot be checked",
    file_passes="is within the limit",
    file_fails="is outside the limit",
)
_POSITIONS = Wording(
    action="check",
    passes="have no position above the limit",
    fails="have a position above the limit",
    unusable="cannot be checked",
    file_passes="has no position above the limit",
    file_fails="has a position above the limit",
)
_MAX_BREACHES_LISTED = 10


class ExposureMeasure(StrEnum):
    """What is added up within a group."""

    GROSS = "gross"
    """Sum of absolute values: longs and shorts both add exposure."""
    NET = "net"
    """Sum of signed values: shorts offset longs."""


def _validate_limits(minimum: Numeric | None, maximum: Numeric | None, *, floor: bool) -> None:
    for name, limit in (("minimum", minimum), ("maximum", maximum)):
        if limit is not None and not is_finite(limit):
            raise ValueError(f"{name} must be a finite number")
    if minimum is None and maximum is None:
        raise ValueError("set a minimum, a maximum, or both")
    if minimum is not None and maximum is not None and minimum > maximum:
        raise ValueError("minimum must not exceed maximum")
    if floor and maximum is not None and maximum < 0:
        raise ValueError("a position limit cannot be negative")


def _validate_common(rule: ExposureLimitRule | PositionLimitRule) -> None:
    if rule.max_violations < 0:
        raise ValueError("max_violations must be non-negative")
    if rule.null_policy is NullPolicy.IGNORE:
        raise ValueError(
            "null_policy 'ignore' is not allowed: leaving out rows changes the totals; "
            "use 'fail' or 'skip'"
        )
    rule.mapping.required_columns("value")


def _absolute(value: Numeric) -> Numeric:
    return -value if value < 0 else value


def _scaled(limit: Numeric, base: Numeric | None) -> Numeric:
    return limit if base is None else precise_product([limit, base])


def _base(
    group: Group, mapping: ColumnMapping, uses_base: bool
) -> tuple[Numeric | None, str | None]:
    """Return the group's base and a failure reason when it cannot be used."""
    if not uses_base:
        return None, None
    if not group.values["base"]:
        return None, "no_base"
    base = group.aggregate("base", mapping)
    return (base, None) if base > 0 else (base, "base_not_positive")


@dataclass(frozen=True, slots=True)
class ExposureLimitRule:
    """Check that each group's gross or net exposure is within limits.

    Exposure is ``sum(|value|)`` (gross) or ``sum(value)`` (net) of the group,
    divided by the group's base when a base column is given. Use
    :func:`gross_within_limit` or :func:`net_within_limit` to build one.
    """

    mapping: ColumnMapping
    measure: ExposureMeasure
    minimum: Numeric | None
    maximum: Numeric | None
    null_policy: NullPolicy
    severity: Severity
    max_violations: int
    rule_id: str
    name: str
    currency_key: str | None = None

    def __post_init__(self) -> None:
        _validate_common(self)
        _validate_limits(self.minimum, self.maximum, floor=False)

    @property
    def semantics(self) -> tuple[str, ...]:
        """Return the fields this rule reads."""
        return ("value", "base") if self.uses_base else ("value",)

    @property
    def uses_base(self) -> bool:
        """Return whether exposure is measured as a fraction of a base column."""
        return "base" in self.mapping.columns

    @property
    def equation(self) -> str:
        """Return the quantity compared with the limits."""
        total = "sum(abs(value))" if self.measure is ExposureMeasure.GROSS else "sum(value)"
        return f"{total} / base" if self.uses_base else total

    def evaluate(self, data: Any) -> ValidationResult:
        """Check every group's exposure."""

        def check(group: Group) -> dict[str, Any] | None:
            values = group.values["value"]
            if self.measure is ExposureMeasure.GROSS:
                total = precise_sum([_absolute(v) for v in values])
            else:
                total = precise_sum(values)
            base, problem = _base(group, self.mapping, self.uses_base)
            if problem is not None:
                return {"reason": problem, "base": base}
            exposure = total if base is None else precise_quotient(total, base)
            reason = None
            if self.maximum is not None and total > _scaled(self.maximum, base):
                reason = "above_maximum"
            elif self.minimum is not None and total < _scaled(self.minimum, base):
                reason = "below_minimum"
            if reason is None:
                return None
            return {
                "reason": reason,
                "observed": exposure,
                "minimum": self.minimum,
                "maximum": self.maximum,
            }

        return evaluate_groups(
            self,
            data,
            self.semantics,
            check,
            blank_allowed=("base",) if self.uses_base else (),
            wording=_WITHIN,
            description={
                "measure": self.measure.value,
                "equation": self.equation,
                "minimum": self.minimum,
                "maximum": self.maximum,
                "currency": currency_note(self.mapping, self.currency_key, "checked"),
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
        return _result(self, outcome, message, metadata, observed, expected)


@dataclass(frozen=True, slots=True)
class PositionLimitRule:
    """Check that no single position is larger than a limit.

    A position's size is ``abs(value)``, divided by the group's base when a base
    column is given. Use :func:`position_within_limit` to build one.
    """

    mapping: ColumnMapping
    maximum: Numeric
    null_policy: NullPolicy
    severity: Severity
    max_violations: int
    currency_key: str | None = None
    rule_id: str = "exposure.position_within_limit"
    name: str = "No single position is above the limit"

    def __post_init__(self) -> None:
        _validate_common(self)
        _validate_limits(None, self.maximum, floor=True)

    @property
    def semantics(self) -> tuple[str, ...]:
        """Return the fields this rule reads."""
        return ("value", "base") if self.uses_base else ("value",)

    @property
    def uses_base(self) -> bool:
        """Return whether size is measured as a fraction of a base column."""
        return "base" in self.mapping.columns

    def evaluate(self, data: Any) -> ValidationResult:
        """Check every position."""

        def check(group: Group) -> dict[str, Any] | None:
            base, problem = _base(group, self.mapping, self.uses_base)
            if problem is not None:
                return {"reason": problem, "base": base}
            limit = _scaled(self.maximum, base)
            breaches = [
                {
                    "row": row,
                    "value": value,
                    "size": value if base is None else precise_quotient(_absolute(value), base),
                }
                for row, value in zip(group.rows, group.values["value"], strict=True)
                if _absolute(value) > limit
            ]
            if not breaches:
                return None
            return {
                "reason": "position_above_limit",
                "maximum": self.maximum,
                "breach_count": len(breaches),
                "breaches": breaches[:_MAX_BREACHES_LISTED],
            }

        return evaluate_groups(
            self,
            data,
            self.semantics,
            check,
            blank_allowed=("base",) if self.uses_base else (),
            wording=_POSITIONS,
            description={
                "equation": "abs(value) / base" if self.uses_base else "abs(value)",
                "maximum": self.maximum,
                "currency": currency_note(self.mapping, self.currency_key, "checked"),
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
        return _result(self, outcome, message, metadata, observed, expected)


def _result(
    rule: ExposureLimitRule | PositionLimitRule,
    outcome: Outcome,
    message: str,
    metadata: dict[str, Any],
    observed: Any,
    expected: Any,
) -> ValidationResult:
    return ValidationResult(
        rule_id=rule.rule_id,
        rule_name=rule.name,
        outcome=outcome,
        severity=rule.severity,
        message=message,
        observed=observed,
        expected=expected,
        metadata=metadata,
    )


def _mapping(
    value: str,
    base: str | None,
    group_by: Sequence[str],
    currency: str | None,
    row_key: str | None,
) -> ColumnMapping:
    columns = {"value": value}
    aggregations = {"value": FieldAggregation.SUM}
    if base is not None:
        columns["base"] = base
        aggregations["base"] = FieldAggregation.REQUIRE_UNIQUE
    return ColumnMapping(
        columns,
        group_keys=group_keys_for(group_by, currency),
        row_key=row_key,
        aggregations=aggregations,
    )


def _exposure_rule(
    measure: ExposureMeasure,
    rule_id: str,
    name: str,
    mapping: ColumnMapping,
    minimum: Numeric | None,
    maximum: Numeric | None,
    null_policy: NullPolicy | str,
    severity: Severity | str,
    max_violations: int,
    currency: str | None,
) -> ExposureLimitRule:
    return ExposureLimitRule(
        mapping=mapping,
        measure=measure,
        minimum=minimum,
        maximum=maximum,
        null_policy=NullPolicy(null_policy),
        severity=Severity(severity),
        max_violations=max_violations,
        rule_id=rule_id,
        name=name,
        currency_key=currency,
    )


def gross_within_limit(
    *,
    value: str,
    maximum: Numeric | None = None,
    minimum: Numeric | None = None,
    base: str | None = None,
    group_by: Sequence[str] = (),
    currency: str | None = None,
    row_key: str | None = None,
    null_policy: NullPolicy | str = NullPolicy.FAIL,
    severity: Severity | str = Severity.ERROR,
    max_violations: int = 20,
) -> ExposureLimitRule:
    """Create a rule limiting gross exposure: long and short positions both count.

    Args:
        value: Column with each position's signed weight or market value.
        maximum: Highest allowed gross exposure (1.3 means 130%), inclusive.
        minimum: Lowest allowed gross exposure, inclusive.
        base: Column with the group's base, such as its NAV, repeated on every
            row or given on some. Omit when ``value`` is already a weight.
        group_by: Columns identifying each portfolio, or each portfolio and
            sector, so each group is limited separately.
        currency: Currency column; each currency is checked separately.
        row_key: Column used to label rows in the report.
        null_policy: ``"fail"`` or ``"skip"`` when a value is blank.
        severity: Severity recorded with the result.
        max_violations: Maximum failing groups listed in the report.
    """
    return _exposure_rule(
        ExposureMeasure.GROSS,
        "exposure.gross_within_limit",
        "Gross exposure is within its limit",
        _mapping(value, base, group_by, currency, row_key),
        minimum,
        maximum,
        null_policy,
        severity,
        max_violations,
        currency,
    )


def net_within_limit(
    *,
    value: str,
    maximum: Numeric | None = None,
    minimum: Numeric | None = None,
    base: str | None = None,
    group_by: Sequence[str] = (),
    currency: str | None = None,
    row_key: str | None = None,
    null_policy: NullPolicy | str = NullPolicy.FAIL,
    severity: Severity | str = Severity.ERROR,
    max_violations: int = 20,
) -> ExposureLimitRule:
    """Create a rule limiting net exposure: short positions offset long ones.

    Arguments are as for :func:`gross_within_limit`. Limits may be negative, for
    a portfolio that must be net short.
    """
    return _exposure_rule(
        ExposureMeasure.NET,
        "exposure.net_within_limit",
        "Net exposure is within its limit",
        _mapping(value, base, group_by, currency, row_key),
        minimum,
        maximum,
        null_policy,
        severity,
        max_violations,
        currency,
    )


def position_within_limit(
    *,
    value: str,
    maximum: Numeric,
    base: str | None = None,
    group_by: Sequence[str] = (),
    currency: str | None = None,
    row_key: str | None = None,
    null_policy: NullPolicy | str = NullPolicy.FAIL,
    severity: Severity | str = Severity.ERROR,
    max_violations: int = 20,
) -> PositionLimitRule:
    """Create a rule limiting the size of any single position.

    Args:
        value: Column with each position's signed weight or market value; a
            short position counts by its absolute size.
        maximum: Largest allowed position (0.1 means 10%), inclusive.
        base: Column with the group's base, such as its NAV. Omit when ``value``
            is already a weight.
        group_by: Columns identifying each portfolio.
        currency: Currency column; each currency is checked separately.
        row_key: Column used to label rows in the report, such as a ticker.
        null_policy: ``"fail"`` or ``"skip"`` when a value is blank.
        severity: Severity recorded with the result.
        max_violations: Maximum failing groups listed in the report.
    """
    return PositionLimitRule(
        mapping=_mapping(value, base, group_by, currency, row_key),
        maximum=maximum,
        null_policy=NullPolicy(null_policy),
        severity=Severity(severity),
        max_violations=max_violations,
        currency_key=currency,
    )
