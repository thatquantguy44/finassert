"""Portfolio weights against values, targets, and prior holdings.

Three grouped checks for files that hold one row per position, with a column that
identifies each portfolio:

* ``weights_match_market_values``: each weight equals its market value divided by
  the portfolio's NAV (or its total market value);
* ``drift_within_band``: each weight is within a band of its target;
* ``turnover_within_limit``: the change from the previous weights is within a limit.

Weights are fractions (0.25, not 25). Blank cells are never read as zero: a
position that was not held before needs a previous weight of 0, not a blank.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, ClassVar

from finassert.adapters.contracts import ColumnMapping, FieldAggregation
from finassert.core.models import Outcome, Severity, ValidationResult
from finassert.numerical import Numeric, Tolerance, coerce_tolerance, is_finite
from finassert.rules._grouping import (
    Group,
    Wording,
    evaluate_groups,
    group_base,
    group_keys_for,
)
from finassert.rules._helpers import absolute, precise_quotient, precise_sum
from finassert.rules.base import NullPolicy

_MAX_LISTED = 10

_VALUES = Wording(
    action="check",
    passes="have weights that match their market values",
    fails="have weights that do not match their market values",
    unusable="cannot be checked",
    file_passes="has weights that match its market values",
    file_fails="has weights that do not match its market values",
)
_DRIFT = Wording(
    action="check",
    passes="are within their drift limits",
    fails="have drifted beyond their limits",
    unusable="cannot be checked",
    file_passes="is within its drift limits",
    file_fails="has drifted beyond its limits",
)
_TURNOVER = Wording(
    action="check",
    passes="are within the turnover limit",
    fails="are above the turnover limit",
    unusable="cannot be checked",
    file_passes="is within the turnover limit",
    file_fails="is above the turnover limit",
)


class TurnoverSides(StrEnum):
    """How turnover counts a trade."""

    ONE_WAY = "one_way"
    """Half the sum of absolute weight changes: each unit sold funds a unit bought."""
    TWO_WAY = "two_way"
    """The full sum of absolute weight changes: buys and sells both count."""


def _validate(rule: Any) -> None:
    if rule.max_violations < 0:
        raise ValueError("max_violations must be non-negative")
    if rule.null_policy is NullPolicy.IGNORE:
        raise ValueError(
            "null_policy 'ignore' is not allowed: leaving out rows changes the totals; "
            "use 'fail' or 'skip'"
        )
    rule.mapping.required_columns(*rule.semantics)


def _mapping(
    columns: dict[str, str],
    group_by: Sequence[str],
    row_key: str | None,
    unique: Sequence[str] = (),
) -> ColumnMapping:
    if isinstance(group_by, str):
        raise TypeError("group_by must be a list of column names")
    return ColumnMapping(
        columns,
        group_keys=group_keys_for(group_by, None),
        row_key=row_key,
        aggregations={
            name: FieldAggregation.REQUIRE_UNIQUE if name in unique else FieldAggregation.SUM
            for name in columns
        },
    )


def _result(
    rule: Any,
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
        tolerance=getattr(rule, "tolerance", None) and rule.tolerance.to_dict(),
        metadata=metadata,
    )


@dataclass(frozen=True, slots=True)
class WeightsMatchMarketValuesRule:
    """Check ``weight = market_value / base`` on every row of each portfolio.

    The base is the portfolio's NAV when a NAV column is given (it may be repeated
    on every row or given on some rows, but must agree and be positive), and
    otherwise the portfolio's total market value. Use
    :func:`weights_match_market_values` to build one.
    """

    mapping: ColumnMapping
    tolerance: Tolerance = field(default_factory=lambda: Tolerance(absolute=1e-8))
    null_policy: NullPolicy = NullPolicy.FAIL
    severity: Severity = Severity.ERROR
    max_violations: int = 20
    rule_id: str = "portfolio.weights_match_market_values"
    name: str = "Weights match market values"

    def __post_init__(self) -> None:
        _validate(self)

    @property
    def uses_nav(self) -> bool:
        """Return whether weights are measured against a NAV column."""
        return "nav" in self.mapping.columns

    @property
    def semantics(self) -> tuple[str, ...]:
        """Return the fields this rule reads."""
        return ("weight", "market_value", *(("nav",) if self.uses_nav else ()))

    @property
    def equation(self) -> str:
        """Return the identity checked."""
        base = "nav" if self.uses_nav else "sum(market_value)"
        return f"weight = market_value / {base}"

    def evaluate(self, data: Any) -> ValidationResult:
        """Check every portfolio."""

        def check(group: Group) -> dict[str, Any] | None:
            if self.uses_nav:
                base, problem = group_base(group, self.mapping, True, "nav")
            else:
                base = precise_sum(group.values["market_value"])
                problem = "base_not_positive" if base <= 0 else None
            if problem is not None or base is None:
                return {"reason": problem, "base": base}
            mismatches = []
            for row, weight, value in zip(
                group.rows, group.values["weight"], group.values["market_value"], strict=True
            ):
                expected = precise_quotient(value, base)
                if not self.tolerance.is_close(weight, expected):
                    mismatches.append(
                        {
                            "row": row,
                            "weight": weight,
                            "expected": expected,
                            "difference": precise_sum([weight, -expected]),
                        }
                    )
            if not mismatches:
                return None
            return {
                "reason": "weights_do_not_match_values",
                "base": base,
                "mismatch_count": len(mismatches),
                "mismatches": mismatches[:_MAX_LISTED],
            }

        return evaluate_groups(
            self,
            data,
            self.semantics,
            check,
            blank_allowed=("nav",) if self.uses_nav else (),
            wording=_VALUES,
            description={"equation": self.equation},
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
class DriftWithinBandRule:
    """Check that each weight is within a band of its target.

    A position drifts by ``abs(weight - target_weight)``, in the same fractions as
    the weights (0.02 is two percentage points). Set a ``band`` for single
    positions, a ``total_limit`` for the sum of all absolute drifts in a portfolio,
    or both. Drift defaults to ``warning`` severity: it asks for a rebalance more
    often than it signals bad data. Use :func:`drift_within_band` to build one.
    """

    mapping: ColumnMapping
    band: Numeric | None
    total_limit: Numeric | None
    null_policy: NullPolicy = NullPolicy.FAIL
    severity: Severity = Severity.WARNING
    max_violations: int = 20
    rule_id: str = "portfolio.drift_within_band"
    name: str = "Weights are within their drift limits"

    semantics: ClassVar[tuple[str, ...]] = ("weight", "target_weight")

    def __post_init__(self) -> None:
        _validate(self)
        if self.band is None and self.total_limit is None:
            raise ValueError("set a band, a total limit, or both")
        for label, limit in (("band", self.band), ("total_limit", self.total_limit)):
            if limit is not None and (not is_finite(limit) or limit < 0):
                raise ValueError(f"{label} must be a finite number, zero or more")

    def evaluate(self, data: Any) -> ValidationResult:
        """Check every portfolio."""

        def check(group: Group) -> dict[str, Any] | None:
            drifts = [
                (row, weight, target, absolute(precise_sum([weight, -target])))
                for row, weight, target in zip(
                    group.rows, group.values["weight"], group.values["target_weight"], strict=True
                )
            ]
            total = precise_sum([drift for *_, drift in drifts])
            breaches = (
                []
                if self.band is None
                else [
                    {"row": row, "weight": weight, "target": target, "drift": drift}
                    for row, weight, target, drift in drifts
                    if drift > self.band
                ]
            )
            total_exceeded = self.total_limit is not None and total > self.total_limit
            if not breaches and not total_exceeded:
                return None
            failure: dict[str, Any] = {
                "reason": "drift_above_band" if breaches else "total_drift_above_limit",
                "total_drift": total,
            }
            if breaches:
                failure.update(
                    band=self.band,
                    breach_count=len(breaches),
                    breaches=breaches[:_MAX_LISTED],
                )
            if total_exceeded:
                failure["total_limit"] = self.total_limit
            return failure

        return evaluate_groups(
            self,
            data,
            self.semantics,
            check,
            wording=_DRIFT,
            description={
                "equation": "abs(weight - target_weight)",
                "band": self.band,
                "total_limit": self.total_limit,
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
class TurnoverWithinLimitRule:
    """Check that each portfolio's turnover since the previous weights is within a limit.

    Turnover is ``sum(abs(weight - previous_weight))``, halved when ``sides`` is
    ``one_way``. Every position held before or now needs a row, with a weight of 0
    where it was not held. Use :func:`turnover_within_limit` to build one.
    """

    mapping: ColumnMapping
    maximum: Numeric
    sides: TurnoverSides
    null_policy: NullPolicy = NullPolicy.FAIL
    severity: Severity = Severity.ERROR
    max_violations: int = 20
    rule_id: str = "portfolio.turnover_within_limit"
    name: str = "Turnover is within its limit"

    semantics: ClassVar[tuple[str, ...]] = ("weight", "previous_weight")

    def __post_init__(self) -> None:
        _validate(self)
        if not is_finite(self.maximum) or self.maximum < 0:
            raise ValueError("maximum must be a finite number, zero or more")

    @property
    def equation(self) -> str:
        """Return the quantity compared with the limit."""
        total = "sum(abs(weight - previous_weight))"
        return f"{total} / 2" if self.sides is TurnoverSides.ONE_WAY else total

    def evaluate(self, data: Any) -> ValidationResult:
        """Check every portfolio."""

        def check(group: Group) -> dict[str, Any] | None:
            changes = [
                (row, weight, previous, absolute(precise_sum([weight, -previous])))
                for row, weight, previous in zip(
                    group.rows,
                    group.values["weight"],
                    group.values["previous_weight"],
                    strict=True,
                )
            ]
            total = precise_sum([change for *_, change in changes])
            turnover = total / 2 if self.sides is TurnoverSides.ONE_WAY else total
            if turnover <= self.maximum:
                return None
            largest = sorted(changes, key=lambda item: item[3], reverse=True)[:5]
            return {
                "reason": "turnover_above_limit",
                "observed": turnover,
                "maximum": self.maximum,
                "largest_changes": [
                    {"row": row, "weight": weight, "previous_weight": previous, "change": change}
                    for row, weight, previous, change in largest
                ],
            }

        return evaluate_groups(
            self,
            data,
            self.semantics,
            check,
            wording=_TURNOVER,
            description={
                "equation": self.equation,
                "sides": self.sides.value,
                "maximum": self.maximum,
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


def weights_match_market_values(
    *,
    weight: str,
    market_value: str,
    nav: str | None = None,
    group_by: Sequence[str] = (),
    row_key: str | None = None,
    tolerance: Numeric | Tolerance = 1e-8,
    null_policy: NullPolicy | str = NullPolicy.FAIL,
    severity: Severity | str = Severity.ERROR,
    max_violations: int = 20,
) -> WeightsMatchMarketValuesRule:
    """Create a rule checking that weights equal market value divided by NAV.

    Args:
        weight: Column with each position's weight as a fraction of 1.
        market_value: Column with each position's signed market value.
        nav: Column with the portfolio's NAV, repeated on every row or given on
            some rows of each portfolio. When omitted, the base is the portfolio's
            total market value, so weights are shares of that total.
        group_by: Columns identifying each portfolio.
        row_key: Column used to label rows in the report, such as a ticker.
        tolerance: Allowed difference between a weight and its expected value, in
            fractions (0.0001 is one basis point).
        null_policy: ``"fail"`` or ``"skip"`` when a value is blank.
        severity: Severity recorded with the result.
        max_violations: Maximum failing portfolios listed in the report.
    """
    columns = {"weight": weight, "market_value": market_value}
    if nav is not None:
        columns["nav"] = nav
    return WeightsMatchMarketValuesRule(
        mapping=_mapping(columns, group_by, row_key, unique=("nav",)),
        tolerance=coerce_tolerance(tolerance),
        null_policy=NullPolicy(null_policy),
        severity=Severity(severity),
        max_violations=max_violations,
    )


def drift_within_band(
    *,
    weight: str,
    target_weight: str,
    band: Numeric | None = None,
    total_limit: Numeric | None = None,
    group_by: Sequence[str] = (),
    row_key: str | None = None,
    null_policy: NullPolicy | str = NullPolicy.FAIL,
    severity: Severity | str = Severity.WARNING,
    max_violations: int = 20,
) -> DriftWithinBandRule:
    """Create a rule checking that weights have not drifted from their targets.

    Args:
        weight: Column with each position's current weight.
        target_weight: Column with each position's target weight.
        band: Largest allowed ``abs(weight - target)`` for one position, as a
            fraction (0.02 is two percentage points). Inclusive.
        total_limit: Largest allowed sum of absolute drifts in a portfolio.
        group_by: Columns identifying each portfolio.
        row_key: Column used to label rows in the report, such as a ticker.
        null_policy: ``"fail"`` or ``"skip"`` when a value is blank.
        severity: Severity recorded with the result; ``warning`` by default.
        max_violations: Maximum failing portfolios listed in the report.
    """
    return DriftWithinBandRule(
        mapping=_mapping({"weight": weight, "target_weight": target_weight}, group_by, row_key),
        band=band,
        total_limit=total_limit,
        null_policy=NullPolicy(null_policy),
        severity=Severity(severity),
        max_violations=max_violations,
    )


def turnover_within_limit(
    *,
    weight: str,
    previous_weight: str,
    maximum: Numeric,
    sides: TurnoverSides | str,
    group_by: Sequence[str] = (),
    row_key: str | None = None,
    null_policy: NullPolicy | str = NullPolicy.FAIL,
    severity: Severity | str = Severity.ERROR,
    max_violations: int = 20,
) -> TurnoverWithinLimitRule:
    """Create a rule limiting how much a portfolio changed since its previous weights.

    Args:
        weight: Column with each position's current weight.
        previous_weight: Column with its previous weight; 0, not blank, for a
            position that was not held.
        maximum: Largest allowed turnover as a fraction (0.2 is 20%). Inclusive.
        sides: ``"one_way"`` (half the sum of absolute changes) or ``"two_way"``
            (the full sum). There is no default: the two differ by a factor of 2.
        group_by: Columns identifying each portfolio.
        row_key: Column used to label rows in the report, such as a ticker.
        null_policy: ``"fail"`` or ``"skip"`` when a value is blank.
        severity: Severity recorded with the result.
        max_violations: Maximum failing portfolios listed in the report.
    """
    return TurnoverWithinLimitRule(
        mapping=_mapping({"weight": weight, "previous_weight": previous_weight}, group_by, row_key),
        maximum=maximum,
        sides=TurnoverSides(sides),
        null_policy=NullPolicy(null_policy),
        severity=Severity(severity),
        max_violations=max_violations,
    )
