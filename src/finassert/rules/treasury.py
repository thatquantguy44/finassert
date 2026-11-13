"""Explicit weekly forecast coverage and cash continuity (specification 0012)."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal, localcontext
from typing import Any, ClassVar

from finassert.adapters._column import extract_columns
from finassert.core.models import DiagnosticCollection, Outcome, Severity, ValidationResult
from finassert.numerical import Numeric, Tolerance, coerce_tolerance, is_finite
from finassert.rules._helpers import is_blank, precise_sum
from finassert.rules.base import NullPolicy

_MAX_EXPECTED_ROWS = 100_000


def _iso_date(value: object) -> date:
    if not isinstance(value, str) or re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) is None:
        raise ValueError("dates must be ISO YYYY-MM-DD text")
    return date.fromisoformat(value)


def _column(value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("column names must be nonempty text")


@dataclass(frozen=True, slots=True)
class _WeeklySchedule:
    keys: tuple[str, ...]
    scope: tuple[tuple[str, ...], ...]
    starts: tuple[str, ...]
    ends: tuple[str, ...]


def _schedule(
    group_by: Sequence[str],
    currency: str,
    expected_scope: Sequence[Mapping[str, str]],
    first_period: str,
    periods: int,
) -> _WeeklySchedule:
    if isinstance(group_by, (str, bytes)):
        raise ValueError("group_by must be a sequence of column names")
    keys = (*group_by, currency)
    for key in keys:
        _column(key)
    if len(set(keys)) != len(keys):
        raise ValueError("group_by and currency must name distinct columns")
    if type(periods) is not int or not 1 <= periods <= _MAX_EXPECTED_ROWS:
        raise ValueError(f"periods must be between 1 and {_MAX_EXPECTED_ROWS}")
    if isinstance(expected_scope, (str, bytes, Mapping)) or not expected_scope:
        raise ValueError("expected_scope must be a nonempty sequence of scope mappings")
    if len(expected_scope) * periods > _MAX_EXPECTED_ROWS:
        raise ValueError(f"expected schedule exceeds {_MAX_EXPECTED_ROWS} rows")
    scope: list[tuple[str, ...]] = []
    for item in expected_scope:
        if not isinstance(item, Mapping) or set(item) != set(keys):
            raise ValueError("each expected_scope mapping must name exactly group_by and currency")
        values = tuple(item[key] for key in keys)
        if not all(isinstance(value, str) and value.strip() for value in values):
            raise ValueError("scope values must be nonempty text")
        if re.fullmatch(r"[A-Z]{3}", values[-1]) is None:
            raise ValueError("currencies must be explicit three-letter uppercase codes")
        scope.append(values)
    if len(set(scope)) != len(scope):
        raise ValueError("expected_scope contains duplicate groups")
    anchor = _iso_date(first_period)
    try:
        bounds = tuple((anchor + timedelta(days=7 * n)).isoformat() for n in range(periods + 1))
    except OverflowError as exc:
        raise ValueError("forecast horizon exceeds supported dates") from exc
    return _WeeklySchedule(tuple(keys), tuple(sorted(scope)), bounds[:-1], bounds[1:])


@dataclass(slots=True)
class _Violations:
    limit: int
    count: int = 0
    examples: list[dict[str, Any]] = field(default_factory=list)

    def add(self, **entry: Any) -> None:
        self.count += 1
        if len(self.examples) < self.limit:
            self.examples.append(entry)

    def metadata(self) -> dict[str, Any]:
        return {
            "violation_count": self.count,
            "violations": self.examples,
            "violations_truncated": self.count > len(self.examples),
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class _ScheduleRule:
    schedule: _WeeklySchedule
    period_start: str
    period_end: str
    row_key: str | None = None
    severity: Severity = Severity.ERROR
    max_violations: int = 20

    def __post_init__(self) -> None:
        columns = (*self.schedule.keys, self.period_start, self.period_end)
        for column in columns:
            _column(column)
        if len(set(columns)) != len(columns):
            raise ValueError("scope and period columns must be distinct")
        if self.row_key is not None:
            _column(self.row_key)
        if type(self.max_violations) is not int or self.max_violations < 0:
            raise ValueError("max_violations must be a nonnegative integer")


def _scan(
    rule: _ScheduleRule,
    data: Any,
    extra: Sequence[str] = (),
) -> tuple[dict[str, list[Any]], list[Any], dict[tuple[str, ...], list[int]], _Violations]:
    schedule = rule.schedule
    names = (*schedule.keys, rule.period_start, rule.period_end, *extra)
    columns, labels = extract_columns(data, names, row_key=rule.row_key)
    issues = _Violations(rule.max_violations)
    buckets: dict[tuple[str, ...], list[int]] = {}
    expected = set(schedule.scope)
    bounds = dict(zip(schedule.starts, schedule.ends, strict=True))
    if rule.row_key is not None:
        ids = columns[rule.row_key]
        if any(not isinstance(label, str) or not label.strip() for label in ids):
            issues.add(reason="invalid_row_identity")
        elif len(set(ids)) != len(ids):
            issues.add(reason="duplicate_row_identity")
    # Explicit diagnostic identities give stable findings even after row reordering.
    for i in sorted(range(len(labels)), key=lambda i: repr(labels[i])):
        group = tuple(columns[key][i] for key in schedule.keys)
        if not all(isinstance(value, str) and value.strip() for value in group):
            issues.add(reason="invalid_scope", row=labels[i])
            continue
        context = {"group": dict(zip(schedule.keys, group, strict=True)), "row": labels[i]}
        if group not in expected:
            issues.add(reason="unexpected_scope", **context)
            continue
        start, end = columns[rule.period_start][i], columns[rule.period_end][i]
        try:
            _iso_date(start)
            _iso_date(end)
        except ValueError:
            issues.add(reason="invalid_period", **context)
            continue
        if start not in bounds:
            issues.add(reason="unexpected_period", period_start=start, **context)
            continue
        if end != bounds[start]:
            issues.add(
                reason="invalid_period_end",
                period_start=start,
                observed=end,
                expected=bounds[start],
                **context,
            )
        buckets.setdefault((*group, start), []).append(i)
    for group in schedule.scope:
        for start in schedule.starts:
            indices = buckets.get((*group, start), [])
            context = {"group": dict(zip(schedule.keys, group, strict=True)), "period_start": start}
            if not indices:
                issues.add(reason="missing_period", **context)
            elif len(indices) > 1:
                issues.add(
                    reason="duplicate_period",
                    row_count=len(indices),
                    rows=[labels[i] for i in indices[: rule.max_violations]],
                    **context,
                )
    return columns, labels, buckets, issues


def _context(rule: _ScheduleRule, row_count: int) -> dict[str, Any]:
    return {
        "group_by": list(rule.schedule.keys),
        "currency": rule.schedule.keys[-1],
        "currency_conversion": "none",
        "period_grain": "weekly_calendar_days",
        "first_period": rule.schedule.starts[0],
        "periods": len(rule.schedule.starts),
        "expected_group_count": len(rule.schedule.scope),
        "expected_row_count": len(rule.schedule.scope) * len(rule.schedule.starts),
        "row_count": row_count,
    }


@dataclass(frozen=True, slots=True, kw_only=True)
class ForecastCoverageRule(_ScheduleRule):
    """Require one weekly row for every explicitly expected scope and period."""

    rule_id: ClassVar[str] = "treasury.forecast_coverage"
    name: ClassVar[str] = "Forecast covers every expected week"

    def evaluate(self, data: Any) -> ValidationResult:
        """Check interval bounds, explicit scope, duplicates and missing periods."""
        _, labels, _, issues = _scan(self, data)
        return ValidationResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            severity=self.severity,
            outcome=Outcome.FAILED if issues.count else Outcome.PASSED,
            message=f"Weekly coverage has {issues.count} violation(s).",
            observed=issues.count,
            expected=0,
            metadata={**_context(self, len(labels)), **issues.metadata()},
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class CashContinuityRule(_ScheduleRule):
    """Compare opening to prior closing cash on a complete weekly schedule."""

    opening_cash: str
    closing_cash: str
    tolerance: Tolerance = field(default_factory=Tolerance)
    null_policy: NullPolicy = NullPolicy.FAIL
    rule_id: ClassVar[str] = "treasury.cash_continuity"
    name: ClassVar[str] = "Cash connects between forecast weeks"

    def __post_init__(self) -> None:
        _ScheduleRule.__post_init__(self)
        _column(self.opening_cash)
        _column(self.closing_cash)
        if self.opening_cash == self.closing_cash:
            raise ValueError("opening_cash and closing_cash must name distinct columns")
        if self.null_policy not in (NullPolicy.FAIL, NullPolicy.SKIP):
            raise ValueError("continuity null_policy must be 'fail' or 'skip'")

    def evaluate(self, data: Any) -> ValidationResult:
        """Error on ambiguous schedules; otherwise compare all adjacent balances."""
        columns, labels, buckets, issues = _scan(self, data, (self.opening_cash, self.closing_cash))
        context = {**_context(self, len(labels)), "equation": "opening[t] = closing[t-1]"}
        if issues.count:
            return self._result(
                Outcome.ERROR,
                "Coverage prerequisites are not satisfied.",
                {**context, "checked_count": 0, **issues.metadata()},
            )
        invalid = _Violations(self.max_violations)
        has_invalid = False
        for i in sorted(range(len(labels)), key=lambda i: repr(labels[i])):
            for name in (self.opening_cash, self.closing_cash):
                value = columns[name][i]
                if not is_finite(value):
                    blank = is_blank(value)
                    has_invalid |= not blank
                    invalid.add(
                        row=labels[i],
                        column=name,
                        reason="blank" if blank else "non_finite_or_nonnumeric",
                    )
        if invalid.count:
            outcome = (
                Outcome.SKIPPED
                if not has_invalid and self.null_policy is NullPolicy.SKIP
                else Outcome.FAILED
            )
            return self._result(
                outcome,
                "Cash amounts are blank or nonnumeric.",
                {**context, "checked_count": 0, **invalid.metadata()},
            )
        checked = 0
        for group in self.schedule.scope:
            for previous, current in zip(
                self.schedule.starts, self.schedule.starts[1:], strict=False
            ):
                prior, index = buckets[(*group, previous)][0], buckets[(*group, current)][0]
                observed = columns[self.opening_cash][index]
                expected = columns[self.closing_cash][prior]
                checked += 1
                if not self.tolerance.is_close(observed, expected):
                    issues.add(
                        reason="cash_discontinuity",
                        group=dict(zip(self.schedule.keys, group, strict=True)),
                        period_start=current,
                        row=labels[index],
                        previous_row=labels[prior],
                        observed=observed,
                        expected=expected,
                        difference=precise_sum([observed, -expected]),
                    )
        return self._result(
            Outcome.FAILED if issues.count else Outcome.PASSED,
            f"{issues.count} of {checked} adjacent cash balances do not connect.",
            {**context, "checked_count": checked, **issues.metadata()},
        )

    def _result(self, outcome: Outcome, message: str, metadata: dict[str, Any]) -> ValidationResult:
        return ValidationResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            outcome=outcome,
            severity=self.severity,
            message=message,
            observed=metadata["violation_count"],
            expected=0,
            tolerance=self.tolerance.to_dict(),
            metadata=metadata,
        )


def forecast_coverage(
    *,
    period_start: str,
    period_end: str,
    group_by: Sequence[str],
    currency: str,
    expected_scope: Sequence[Mapping[str, str]],
    first_period: str,
    periods: int = 13,
    row_key: str | None = None,
    severity: Severity | str = Severity.ERROR,
    max_violations: int = 20,
) -> ForecastCoverageRule:
    """Require all explicitly expected weekly buckets, including wholly missing groups.

    Args:
        period_start: Inclusive ISO YYYY-MM-DD week-start column.
        period_end: Exclusive ISO week-end column, seven calendar days later.
        group_by: Non-currency series columns, including vintage/entity/scenario as needed.
        currency: Mandatory explicit currency column, never converted or inferred.
        expected_scope: Nonempty text mappings naming exactly group_by and currency columns.
        first_period: Explicit ISO first week start; no weekday/calendar inference.
        periods: Number of consecutive weeks, defaults to 13; maximum expected rows is 100,000.
        row_key: Optional unique nonempty text diagnostic identity column.
        severity: Business impact of coverage failures.
        max_violations: Maximum examples, not an evaluation limit.

    Empty data fails coverage. Invalid scope or dates fail; missing columns raise
    an evaluation error. No rows are ignored. Configuration is copied into
    immutable tuples. Nonweekly schedules require a different contract.
    """
    return ForecastCoverageRule(
        schedule=_schedule(group_by, currency, expected_scope, first_period, periods),
        period_start=period_start,
        period_end=period_end,
        row_key=row_key,
        severity=Severity(severity),
        max_violations=max_violations,
    )


def cash_continuity(
    *,
    opening_cash: str,
    closing_cash: str,
    period_start: str,
    period_end: str,
    group_by: Sequence[str],
    currency: str,
    expected_scope: Sequence[Mapping[str, str]],
    first_period: str,
    periods: int = 13,
    row_key: str | None = None,
    tolerance: Numeric | Tolerance = 0,
    null_policy: NullPolicy | str = NullPolicy.FAIL,
    severity: Severity | str = Severity.ERROR,
    max_violations: int = 20,
) -> CashContinuityRule:
    """Compare opening cash with prior closing cash only on complete expected series.

    Args:
        opening_cash: Opening balance column in currency major units; negatives allowed.
        closing_cash: Closing balance column in the same units.
        period_start: Inclusive ISO YYYY-MM-DD week-start column.
        period_end: Exclusive ISO week-end column, exactly seven calendar days later.
        group_by: Non-currency series columns; no comparison crosses a series.
        currency: Mandatory explicit currency column; never converted.
        expected_scope: Nonempty text mappings naming exactly group_by and currency columns.
        first_period: Explicit ISO first week start.
        periods: Consecutive weeks, defaults to 13; expected schedule capped at 100,000 rows.
        row_key: Optional unique nonempty text diagnostic identity column.
        tolerance: Inclusive absolute/relative amount tolerance under specification 0003.
        null_policy: 'fail' or 'skip' for blank amounts; never ignore missing balances.
        severity: Business impact of continuity failures.
        max_violations: Maximum examples, not an evaluation limit.

    Missing/duplicate/extra/malformed periods produce ERROR, never a pass across
    a gap. All amounts must be finite, including first opening and last closing.
    A single-week series has zero comparisons after input validation. This rule
    does not check within-week cash flows or tie the first opening to actuals,
    and is inappropriate across account-perimeter changes.
    """
    return CashContinuityRule(
        schedule=_schedule(group_by, currency, expected_scope, first_period, periods),
        period_start=period_start,
        period_end=period_end,
        row_key=row_key,
        opening_cash=opening_cash,
        closing_cash=closing_cash,
        tolerance=coerce_tolerance(tolerance),
        null_policy=NullPolicy(null_policy),
        severity=Severity(severity),
        max_violations=max_violations,
    )


def _amount_precision(values: Sequence[Decimal]) -> int:
    # Retain all finite input digits and room for sums/products and relative bounds.
    low = min(int(value.as_tuple().exponent) for value in values)
    high = max(value.adjusted() for value in values)
    return max(50, high - low + sum(len(value.as_tuple().digits) for value in values) + 5)


def _amounts(
    rule: Any,
    columns: dict[str, list[Any]],
    labels: list[Any],
    names: Sequence[str],
    nonnegative: Sequence[str],
) -> tuple[_Violations, bool]:
    invalid = _Violations(rule.max_violations)
    nonblank = False
    for i in sorted(range(len(labels)), key=lambda i: repr(labels[i])):
        for name in names:
            value = columns[name][i]
            reason = None
            if not is_finite(value):
                blank = is_blank(value) and not isinstance(value, (int, float, Decimal))
                nonblank |= not blank
                reason = "blank" if blank else "non_finite_or_nonnumeric"
            elif name in nonnegative and value < 0:
                nonblank = True
                reason = "negative_amount"
            if reason:
                invalid.add(row=labels[i], column=name, reason=reason)
    return invalid, nonblank


def _amount_result(
    rule: Any,
    outcome: Outcome,
    context: dict[str, Any],
    issues: _Violations,
    message: str,
    *,
    diagnostics: tuple[DiagnosticCollection, ...] = (),
) -> ValidationResult:
    return ValidationResult(
        rule_id=rule.rule_id,
        rule_name=rule.name,
        severity=rule.severity,
        outcome=outcome,
        message=message,
        observed=issues.count,
        expected=0,
        tolerance=rule.tolerance.to_dict(),
        metadata={**context, **issues.metadata()},
        diagnostics=diagnostics,
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class MinimumCashBufferRule(_ScheduleRule):
    """Compare closing less restricted cash with each row's explicit minimum."""

    closing_cash: str
    restricted_cash: str
    minimum_buffer: str
    tolerance: Tolerance = field(default_factory=Tolerance)
    null_policy: NullPolicy = NullPolicy.FAIL
    rule_id: ClassVar[str] = "treasury.minimum_cash_buffer"
    name: ClassVar[str] = "Available cash meets the minimum buffer"

    def __post_init__(self) -> None:
        _ScheduleRule.__post_init__(self)
        for name in (self.closing_cash, self.restricted_cash, self.minimum_buffer):
            _column(name)
        if len({self.closing_cash, self.restricted_cash, self.minimum_buffer}) != 3:
            raise ValueError("cash amount columns must be distinct")
        if not all(is_finite(v) for v in (self.tolerance.absolute, self.tolerance.relative)):
            raise ValueError("tolerance components must be finite numeric amounts")
        if self.null_policy not in (NullPolicy.FAIL, NullPolicy.SKIP):
            raise ValueError("buffer null_policy must be 'fail' or 'skip'")

    def evaluate(self, data: Any) -> ValidationResult:
        """Check complete currency-isolated schedules and sample every actual shortfall."""
        names = (self.closing_cash, self.restricted_cash, self.minimum_buffer)
        columns, labels, _, issues = _scan(self, data, names)
        context = {
            **_context(self, len(labels)),
            "equation": "available_cash = closing_cash - restricted_cash >= minimum_buffer",
            "units": "currency_major_units",
            "checked_count": 0,
            "columns": dict(
                zip(("closing_cash", "restricted_cash", "minimum_buffer"), names, strict=True)
            ),
        }
        if issues.count:
            return _amount_result(
                self, Outcome.ERROR, context, issues, "Coverage prerequisites are not satisfied."
            )
        invalid, nonblank = _amounts(self, columns, labels, names, names[1:])
        if invalid.count:
            outcome = (
                Outcome.SKIPPED
                if not nonblank and self.null_policy is NullPolicy.SKIP
                else Outcome.FAILED
            )
            return _amount_result(
                self, outcome, context, invalid, "Cash amounts are missing or invalid."
            )
        shortfalls = _Violations(self.max_violations)
        for i in sorted(range(len(labels)), key=lambda i: repr(labels[i])):
            close, restricted, minimum = (Decimal(str(columns[name][i])) for name in names)
            values = [
                close,
                restricted,
                minimum,
                Decimal(str(self.tolerance.absolute)),
                Decimal(str(self.tolerance.relative)),
            ]
            with localcontext() as precision:
                precision.prec = _amount_precision(values)
                available = close - restricted
                if available < minimum:
                    allowed = self.tolerance.is_close(available, minimum)
                    entry = dict(
                        row=labels[i],
                        group={key: columns[key][i] for key in self.schedule.keys},
                        period_start=columns[self.period_start][i],
                        observed=available,
                        expected=minimum,
                        difference=available - minimum,
                        shortfall=minimum - available,
                        within_tolerance=allowed,
                    )
                    shortfalls.add(**entry)
                    if not allowed:
                        issues.add(reason="cash_buffer_shortfall", **entry)
        context.update(
            checked_count=len(labels),
            shortfall_count=shortfalls.count,
            shortfalls=shortfalls.examples,
            shortfalls_truncated=shortfalls.count > self.max_violations,
        )
        return _amount_result(
            self,
            Outcome.FAILED if issues.count else Outcome.PASSED,
            context,
            issues,
            f"{issues.count} cash buffer breach(es).",
            diagnostics=(
                DiagnosticCollection(
                    "cash_shortfalls",
                    shortfalls.count,
                    self.max_violations,
                    tuple(shortfalls.examples),
                ),
            ),
        )


def minimum_cash_buffer(
    *,
    closing_cash: str,
    restricted_cash: str,
    minimum_buffer: str,
    period_start: str,
    period_end: str,
    group_by: Sequence[str],
    currency: str,
    expected_scope: Sequence[Mapping[str, str]],
    first_period: str,
    periods: int = 13,
    row_key: str | None = None,
    tolerance: Numeric | Tolerance = 0,
    null_policy: NullPolicy | str = NullPolicy.FAIL,
    severity: Severity | str = Severity.ERROR,
    max_violations: int = 20,
) -> MinimumCashBufferRule:
    """Require available cash to meet a caller-supplied per-row minimum.

    Args:
        closing_cash: Closing cash including restricted balances, in major units.
        restricted_cash: Nonnegative restricted balance column; never added to liquidity.
        minimum_buffer: Nonnegative required available cash column, with no business default.
        period_start: Inclusive ISO YYYY-MM-DD weekly start column.
        period_end: Exclusive ISO weekly end column, exactly seven days later.
        group_by: Series columns, including vintage/entity/scenario as appropriate.
        currency: Mandatory explicit currency column; no netting or conversion.
        expected_scope: Independent complete series mappings, including currency.
        first_period: Explicit ISO first week start.
        periods: Consecutive weeks; expected schedule capped at 100,000 rows.
        row_key: Optional unique nonempty text diagnostic identity column.
        tolerance: Inclusive amount tolerance, zero by default.
        null_policy: Fail or skip on blank amounts; invalid numerics always fail.
        severity: Impact of a financial breach.
        max_violations: Example cap, never a count/evaluation limit.

    Missing/ambiguous coverage errors. Negative closing cash is allowed. Equality
    passes. All shortfalls, including tolerated ones, are counted and sampled.
    This measure excludes facilities and does not judge adequacy of the minimum.
    """
    return MinimumCashBufferRule(
        schedule=_schedule(group_by, currency, expected_scope, first_period, periods),
        period_start=period_start,
        period_end=period_end,
        row_key=row_key,
        closing_cash=closing_cash,
        restricted_cash=restricted_cash,
        minimum_buffer=minimum_buffer,
        tolerance=coerce_tolerance(tolerance),
        null_policy=NullPolicy(null_policy),
        severity=Severity(severity),
        max_violations=max_violations,
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class FacilityCapacityRule(_ScheduleRule):
    """Check period-end facility principal and effective capacity."""

    facility_id: str
    opening_drawn: str
    draws: str
    repayments: str
    closing_drawn: str
    commitment: str
    unavailable_amount: str
    tolerance: Tolerance = field(default_factory=Tolerance)
    null_policy: NullPolicy = NullPolicy.FAIL
    rule_id: ClassVar[str] = "treasury.facility_capacity"
    name: ClassVar[str] = "Facility principal and capacity reconcile"

    def __post_init__(self) -> None:
        _ScheduleRule.__post_init__(self)
        names = self._amount_columns()
        for name in names:
            _column(name)
        if len(set(names)) != len(names):
            raise ValueError("facility amount columns must be distinct")
        if self.facility_id not in self.schedule.keys[:-1]:
            raise ValueError("facility_id must be part of the expected scope")
        if self.null_policy not in (NullPolicy.FAIL, NullPolicy.SKIP):
            raise ValueError("facility null_policy must be 'fail' or 'skip'")
        if not all(is_finite(v) for v in (self.tolerance.absolute, self.tolerance.relative)):
            raise ValueError("tolerance components must be finite numeric amounts")

    def _amount_columns(self) -> tuple[str, ...]:
        return (
            self.opening_drawn,
            self.draws,
            self.repayments,
            self.closing_drawn,
            self.commitment,
            self.unavailable_amount,
        )

    def evaluate(self, data: Any) -> ValidationResult:
        """Validate complete schedules before checking every principal/capacity row."""
        names = self._amount_columns()
        columns, labels, _, issues = _scan(self, data, names)
        context = {
            **_context(self, len(labels)),
            "checked_count": 0,
            "units": "currency_major_units",
            "facility_id": self.facility_id,
            "equations": [
                "closing_drawn = opening_drawn + draws - repayments",
                "available_commitment = commitment - unavailable_amount",
                "headroom = available_commitment - closing_drawn",
            ],
            "repayment_sign": "positive",
            "capacity_scope": "period_end_only",
        }
        if issues.count:
            return _amount_result(
                self,
                Outcome.ERROR,
                context,
                issues,
                "Facility coverage prerequisites are not satisfied.",
            )
        invalid, nonblank = _amounts(self, columns, labels, names, names)
        if invalid.count:
            outcome = (
                Outcome.SKIPPED
                if not nonblank and self.null_policy is NullPolicy.SKIP
                else Outcome.FAILED
            )
            return _amount_result(
                self, outcome, context, invalid, "Facility amounts are missing or invalid."
            )
        balances = _Violations(self.max_violations)
        for i in sorted(range(len(labels)), key=lambda i: repr(labels[i])):
            values = [Decimal(str(columns[name][i])) for name in names]
            with localcontext() as precision:
                precision.prec = _amount_precision(
                    [
                        *values,
                        Decimal(str(self.tolerance.absolute)),
                        Decimal(str(self.tolerance.relative)),
                    ]
                )
                opening, draws, repayments, closing, commitment, unavailable = values
                expected = opening + draws - repayments
                capacity = commitment - unavailable
                entry = dict(
                    row=labels[i],
                    group={key: columns[key][i] for key in self.schedule.keys},
                    period_start=columns[self.period_start][i],
                )
                balances.add(
                    **entry,
                    closing_drawn=closing,
                    available_commitment=capacity,
                    headroom=capacity - closing,
                )
                if not self.tolerance.is_close(closing, expected):
                    issues.add(
                        **entry,
                        reason="principal_identity",
                        observed=closing,
                        expected=expected,
                        difference=closing - expected,
                    )
                for actual, limit, reason in (
                    (unavailable, commitment, "unavailable_exceeds_commitment"),
                    (closing, capacity, "capacity_exceeded"),
                ):
                    if actual > limit and not self.tolerance.is_close(actual, limit):
                        issues.add(
                            **entry,
                            reason=reason,
                            observed=actual,
                            expected=limit,
                            difference=actual - limit,
                            headroom=capacity - closing,
                        )
        context.update(
            checked_count=len(labels),
            balance_count=balances.count,
            balances=balances.examples,
            balances_truncated=balances.count > self.max_violations,
        )
        return _amount_result(
            self,
            Outcome.FAILED if issues.count else Outcome.PASSED,
            context,
            issues,
            f"{issues.count} facility breach(es).",
            diagnostics=(
                DiagnosticCollection(
                    "facility_balances",
                    balances.count,
                    self.max_violations,
                    tuple(balances.examples),
                ),
            ),
        )
