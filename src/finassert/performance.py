"""Reference calculations for one monthly strategy and benchmark series."""

from __future__ import annotations

import calendar
import math
import re
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
from types import MappingProxyType
from typing import Any

from finassert.adapters._column import extract_columns
from finassert.numerical import is_finite
from finassert.rules.returns import ReturnUnit

_DECIMAL_PRECISION = 50
_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass(frozen=True, slots=True)
class MonthlyPerformanceIssue:
    """One blocking source or coverage issue found during monthly preflight."""

    code: str
    message: str
    source_row: Any | None = None
    source_position: int | None = None
    period_end: date | None = None
    field: str | None = None
    observed: Any = None
    expected: Any = None

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation of the issue."""
        return {
            "code": self.code,
            "message": self.message,
            "source_row": _json_value(self.source_row),
            "source_position": self.source_position,
            "period_end": None if self.period_end is None else self.period_end.isoformat(),
            "field": self.field,
            "observed": _json_value(self.observed),
            "expected": _json_value(self.expected),
        }


@dataclass(frozen=True, slots=True)
class MonthlyPerformancePeriod:
    """Reference calculations for one valid, chronologically ordered month."""

    period_end: date
    source_row: Any
    source_position: int
    strategy_return: Decimal
    benchmark_return: Decimal
    active_return: Decimal
    strategy_cumulative_return: Decimal
    benchmark_cumulative_return: Decimal
    cumulative_return_difference: Decimal

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation, preserving Decimal text."""
        return {
            "period_end": self.period_end.isoformat(),
            "source_row": _json_value(self.source_row),
            "source_position": self.source_position,
            "strategy_return": str(self.strategy_return),
            "benchmark_return": str(self.benchmark_return),
            "active_return": str(self.active_return),
            "strategy_cumulative_return": str(self.strategy_cumulative_return),
            "benchmark_cumulative_return": str(self.benchmark_cumulative_return),
            "cumulative_return_difference": str(self.cumulative_return_difference),
        }


@dataclass(frozen=True, slots=True)
class MonthlyPerformanceSummary:
    """Summary measures from a complete monthly return window."""

    complete_months: int
    strategy_cumulative_return: Decimal
    benchmark_cumulative_return: Decimal
    cumulative_return_difference: Decimal
    strategy_annualized_geometric_return: Decimal | None
    benchmark_annualized_geometric_return: Decimal | None
    annualized_geometric_unavailable_reason: str | None
    annualized_tracking_error: Decimal | None
    tracking_error_unavailable_reason: str | None

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation, preserving Decimal text."""
        return {
            "complete_months": self.complete_months,
            "strategy_cumulative_return": str(self.strategy_cumulative_return),
            "benchmark_cumulative_return": str(self.benchmark_cumulative_return),
            "cumulative_return_difference": str(self.cumulative_return_difference),
            "strategy_annualized_geometric_return": _decimal_text(
                self.strategy_annualized_geometric_return
            ),
            "benchmark_annualized_geometric_return": _decimal_text(
                self.benchmark_annualized_geometric_return
            ),
            "annualized_geometric_unavailable_reason": self.annualized_geometric_unavailable_reason,
            "annualized_tracking_error": _decimal_text(self.annualized_tracking_error),
            "tracking_error_unavailable_reason": self.tracking_error_unavailable_reason,
        }


@dataclass(frozen=True, slots=True)
class MonthlyPerformanceReference:
    """Preflight findings and reference calculations for a declared window.

    ``summary`` and ``periods`` are unavailable when any blocking input or
    coverage issue exists. ``issues`` contains at most ``max_violations``
    observations; ``issue_count`` and ``issue_counts`` always describe the full
    scan.
    """

    window_start: date
    window_end: date
    period_end_column: str
    strategy_return_column: str
    benchmark_return_column: str
    return_unit: ReturnUnit
    row_key: str | None
    expected_periods: tuple[date, ...]
    periods: tuple[MonthlyPerformancePeriod, ...]
    summary: MonthlyPerformanceSummary | None
    issues: tuple[MonthlyPerformanceIssue, ...]
    issue_count: int
    issue_counts: Mapping[str, int]
    max_violations: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "issue_counts", MappingProxyType(dict(self.issue_counts)))

    @property
    def available(self) -> bool:
        """Whether complete reference calculations are available."""
        return self.summary is not None

    @property
    def issues_truncated(self) -> bool:
        """Whether the issue examples are capped below the full issue count."""
        return self.issue_count > len(self.issues)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation of the full preflight result."""
        return {
            "window_start": self.window_start.isoformat(),
            "window_end": self.window_end.isoformat(),
            "columns": {
                "period_end": self.period_end_column,
                "strategy_return": self.strategy_return_column,
                "benchmark_return": self.benchmark_return_column,
                "row_key": self.row_key,
            },
            "return_unit": self.return_unit.value,
            "expected_period_count": len(self.expected_periods),
            "available": self.available,
            "periods": [period.to_dict() for period in self.periods],
            "summary": None if self.summary is None else self.summary.to_dict(),
            "issue_count": self.issue_count,
            "issue_counts": dict(self.issue_counts),
            "issues_limit": self.max_violations,
            "issues_truncated": self.issues_truncated,
            "issues": [issue.to_dict() for issue in self.issues],
        }


@dataclass(frozen=True, slots=True)
class _InputRow:
    position: int
    source_row: Any
    period_end: date | None
    strategy_return: Decimal | None
    benchmark_return: Decimal | None


class _IssueCollector:
    def __init__(self, limit: int) -> None:
        self.limit = limit
        self.items: list[MonthlyPerformanceIssue] = []
        self.counts: Counter[str] = Counter()

    def add(self, issue: MonthlyPerformanceIssue) -> None:
        self.counts[issue.code] += 1
        if len(self.items) < self.limit:
            self.items.append(issue)

    @property
    def count(self) -> int:
        return sum(self.counts.values())


def monthly_performance_reference(
    data: Any,
    *,
    period_end: str,
    strategy_return: str,
    benchmark_return: str,
    window_start: date | str,
    window_end: date | str,
    return_unit: ReturnUnit | str,
    row_key: str | None = None,
    max_violations: int = 20,
) -> MonthlyPerformanceReference:
    """Preflight and calculate monthly performance from paired periodic returns.

    Rows may be supplied in any order. The window is inclusive and must use
    calendar month-end dates. Percent inputs are normalized to decimal fractions
    before calculation. Invalid or incomplete data blocks every cumulative and
    annualized reference measure; no partial series is returned.

    Args:
        data: A supported column mapping, row-mapping sequence, ``ColumnSource``,
            or pandas DataFrame.
        period_end: Physical column containing ISO dates or date-valued month ends.
        strategy_return: Physical column with the strategy's simple monthly returns.
        benchmark_return: Physical column with paired benchmark returns.
        window_start: Inclusive first month-end as an ISO date or ``date``.
        window_end: Inclusive last month-end as an ISO date or ``date``.
        return_unit: Required ``"fraction"`` or ``"percent"`` declaration.
        row_key: Optional column used as the source-row identity. Native adapter
            labels are retained when omitted.
        max_violations: Maximum issue examples to retain. The full issue counts
            remain available even when examples are truncated.

    Returns:
        A preflight result with chronological reference rows and summary when
        every expected month and both return values are valid. Otherwise the
        result contains blocking issues and no calculated periods or summary.

    Raises:
        ValueError: If the window, unit, column mappings, or issue limit is invalid.
        ColumnNotFoundError: If a requested source column is absent.
        InvalidDataError: If the input is not a supported aligned table.
    """
    start = _window_date(window_start, "window_start")
    end = _window_date(window_end, "window_end")
    if start > end:
        raise ValueError("window_start must not be after window_end")
    if type(max_violations) is not int or max_violations < 0:
        raise ValueError("max_violations must be a non-negative integer")
    try:
        unit = ReturnUnit(return_unit)
    except (TypeError, ValueError) as exc:
        raise ValueError("return_unit must be 'fraction' or 'percent'") from exc

    columns = {
        "period_end": period_end,
        "strategy_return": strategy_return,
        "benchmark_return": benchmark_return,
    }
    for semantic, name in columns.items():
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"{semantic} must be a non-empty column name")
    if len(set(columns.values())) != len(columns):
        raise ValueError("period_end, strategy_return, and benchmark_return need distinct columns")
    if row_key is not None:
        if not isinstance(row_key, str) or not row_key.strip():
            raise ValueError("row_key must be a non-empty column name when provided")
        if row_key in columns.values():
            raise ValueError("row_key must be distinct from the period and return columns")

    expected = _expected_month_ends(start, end)
    source_columns, source_rows = extract_columns(data, list(columns.values()), row_key=row_key)
    issues = _IssueCollector(max_violations)
    if not source_rows:
        issues.add(
            MonthlyPerformanceIssue(
                code="empty_input",
                message="The source contains no rows for the declared window.",
                expected=len(expected),
            )
        )
    parsed: list[_InputRow] = []
    period_rows: dict[date, list[_InputRow]] = {}

    for position, source_row in enumerate(source_rows):
        raw_period = source_columns[period_end][position]
        parsed_period: date | None
        try:
            parsed_period = _source_month_end(raw_period)
        except ValueError:
            parsed_period = None
            issues.add(
                MonthlyPerformanceIssue(
                    code="invalid_period",
                    message="The period value must resolve to a calendar month-end date.",
                    source_row=source_row,
                    source_position=position,
                    field=period_end,
                    observed=raw_period,
                    expected="calendar month-end",
                )
            )

        if parsed_period is not None and (parsed_period < start or parsed_period > end):
            issues.add(
                MonthlyPerformanceIssue(
                    code="outside_window",
                    message="The period is outside the declared inclusive window.",
                    source_row=source_row,
                    source_position=position,
                    period_end=parsed_period,
                    field=period_end,
                    observed=parsed_period,
                    expected={"window_start": start, "window_end": end},
                )
            )

        strategy_value = _periodic_return(
            source_columns[strategy_return][position],
            column=strategy_return,
            source_row=source_row,
            position=position,
            period_end=parsed_period,
            unit=unit,
            issues=issues,
        )
        benchmark_value = _periodic_return(
            source_columns[benchmark_return][position],
            column=benchmark_return,
            source_row=source_row,
            position=position,
            period_end=parsed_period,
            unit=unit,
            issues=issues,
        )
        item = _InputRow(position, source_row, parsed_period, strategy_value, benchmark_value)
        parsed.append(item)
        if parsed_period is not None:
            period_rows.setdefault(parsed_period, []).append(item)

    for parsed_period, rows in period_rows.items():
        if len(rows) > 1:
            for item in rows:
                issues.add(
                    MonthlyPerformanceIssue(
                        code="duplicate_period",
                        message="More than one source row has this calendar month-end.",
                        source_row=item.source_row,
                        source_position=item.position,
                        period_end=parsed_period,
                        field=period_end,
                        observed=parsed_period,
                        expected="one row per month",
                    )
                )

    for expected_period in expected:
        if expected_period not in period_rows:
            issues.add(
                MonthlyPerformanceIssue(
                    code="missing_period",
                    message="The declared window has no source row for this month.",
                    period_end=expected_period,
                    field=period_end,
                    expected=expected_period,
                )
            )

    if issues.count:
        return MonthlyPerformanceReference(
            window_start=start,
            window_end=end,
            period_end_column=period_end,
            strategy_return_column=strategy_return,
            benchmark_return_column=benchmark_return,
            return_unit=unit,
            row_key=row_key,
            expected_periods=expected,
            periods=(),
            summary=None,
            issues=tuple(issues.items),
            issue_count=issues.count,
            issue_counts=dict(sorted(issues.counts.items())),
            max_violations=max_violations,
        )

    ordered = [period_rows[month][0] for month in expected]
    assert all(
        row.strategy_return is not None and row.benchmark_return is not None for row in ordered
    )
    reference_periods, summary = _calculate(ordered)
    return MonthlyPerformanceReference(
        window_start=start,
        window_end=end,
        period_end_column=period_end,
        strategy_return_column=strategy_return,
        benchmark_return_column=benchmark_return,
        return_unit=unit,
        row_key=row_key,
        expected_periods=expected,
        periods=reference_periods,
        summary=summary,
        issues=(),
        issue_count=0,
        issue_counts={},
        max_violations=max_violations,
    )


def _calculate(
    rows: list[_InputRow],
) -> tuple[tuple[MonthlyPerformancePeriod, ...], MonthlyPerformanceSummary]:
    with localcontext() as context:
        context.prec = _DECIMAL_PRECISION
        context.rounding = ROUND_HALF_EVEN
        wealth_strategy = Decimal(1)
        wealth_benchmark = Decimal(1)
        periods: list[MonthlyPerformancePeriod] = []
        active_returns: list[Decimal] = []
        for row in rows:
            strategy = row.strategy_return
            benchmark = row.benchmark_return
            assert strategy is not None and benchmark is not None and row.period_end is not None
            active = strategy - benchmark
            wealth_strategy *= Decimal(1) + strategy
            wealth_benchmark *= Decimal(1) + benchmark
            cumulative_strategy = wealth_strategy - Decimal(1)
            cumulative_benchmark = wealth_benchmark - Decimal(1)
            difference = cumulative_strategy - cumulative_benchmark
            periods.append(
                MonthlyPerformancePeriod(
                    period_end=row.period_end,
                    source_row=row.source_row,
                    source_position=row.position,
                    strategy_return=strategy,
                    benchmark_return=benchmark,
                    active_return=active,
                    strategy_cumulative_return=cumulative_strategy,
                    benchmark_cumulative_return=cumulative_benchmark,
                    cumulative_return_difference=difference,
                )
            )
            active_returns.append(active)

        complete_months = len(rows)
        strategy_cumulative_return = wealth_strategy - Decimal(1)
        benchmark_cumulative_return = wealth_benchmark - Decimal(1)
        cumulative_difference = strategy_cumulative_return - benchmark_cumulative_return

        if complete_months >= 12:
            exponent = Decimal(12) / Decimal(complete_months)
            strategy_annualized = (Decimal(1) + strategy_cumulative_return) ** exponent - Decimal(1)
            benchmark_annualized = (Decimal(1) + benchmark_cumulative_return) ** exponent - Decimal(
                1
            )
            geometric_unavailable = None
        else:
            strategy_annualized = None
            benchmark_annualized = None
            geometric_unavailable = "fewer_than_12_complete_months"

        if complete_months >= 2:
            mean_active = sum(active_returns, Decimal(0)) / Decimal(complete_months)
            sample_variance = sum(
                ((value - mean_active) ** 2 for value in active_returns), Decimal(0)
            ) / Decimal(complete_months - 1)
            tracking_error = sample_variance.sqrt() * Decimal(12).sqrt()
            tracking_unavailable = None
        else:
            tracking_error = None
            tracking_unavailable = "fewer_than_2_complete_months"

    summary = MonthlyPerformanceSummary(
        complete_months=complete_months,
        strategy_cumulative_return=strategy_cumulative_return,
        benchmark_cumulative_return=benchmark_cumulative_return,
        cumulative_return_difference=cumulative_difference,
        strategy_annualized_geometric_return=strategy_annualized,
        benchmark_annualized_geometric_return=benchmark_annualized,
        annualized_geometric_unavailable_reason=geometric_unavailable,
        annualized_tracking_error=tracking_error,
        tracking_error_unavailable_reason=tracking_unavailable,
    )
    return tuple(periods), summary


def _periodic_return(
    value: Any,
    *,
    column: str,
    source_row: Any,
    position: int,
    period_end: date | None,
    unit: ReturnUnit,
    issues: _IssueCollector,
) -> Decimal | None:
    identity = {
        "source_row": source_row,
        "source_position": position,
        "period_end": period_end,
        "field": column,
        "observed": value,
    }
    if _is_blank(value):
        issues.add(
            MonthlyPerformanceIssue(
                code="blank_return",
                message="A monthly return is blank and cannot be calculated.",
                **identity,
            )
        )
        return None
    if not is_finite(value):
        issues.add(
            MonthlyPerformanceIssue(
                code="invalid_return",
                message="A monthly return must be a finite numeric value.",
                expected="finite numeric return",
                **identity,
            )
        )
        return None

    with localcontext() as context:
        context.prec = _DECIMAL_PRECISION
        context.rounding = ROUND_HALF_EVEN
        normalized = Decimal(str(value))
        if unit is ReturnUnit.PERCENT:
            normalized /= Decimal(100)
    if normalized <= Decimal(-1):
        issues.add(
            MonthlyPerformanceIssue(
                code="return_at_or_below_minus_100_percent",
                message="Returns at or below -100% are outside the positive-wealth workflow.",
                expected="greater than -1 in decimal-return fractions",
                **identity,
            )
        )
        return None
    return normalized


def _window_date(value: date | str, field: str) -> date:
    if type(value).__name__ in {"NAType", "NaTType"}:
        raise ValueError(f"{field} must be a valid date")
    if isinstance(value, datetime):
        parsed = value.date()
    elif isinstance(value, date):
        parsed = value
    elif isinstance(value, str) and _ISO_DATE.fullmatch(value):
        try:
            parsed = date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError(f"{field} must be a valid ISO calendar date") from exc
    else:
        raise ValueError(f"{field} must be a date or YYYY-MM-DD string")
    if not _is_month_end(parsed):
        raise ValueError(f"{field} must be a calendar month-end date")
    return parsed


def _source_month_end(value: Any) -> date:
    if type(value).__name__ in {"NAType", "NaTType"}:
        raise ValueError("not a date")
    if isinstance(value, datetime):
        parsed = value.date()
    elif isinstance(value, date):
        parsed = value
    elif isinstance(value, str) and _ISO_DATE.fullmatch(value):
        parsed = date.fromisoformat(value)
    else:
        raise ValueError("not a date")
    if not _is_month_end(parsed):
        raise ValueError("not a month end")
    return parsed


def _is_month_end(value: date) -> bool:
    return (
        isinstance(value, date)
        and not isinstance(value, datetime)
        and value.day == calendar.monthrange(value.year, value.month)[1]
    )


def _expected_month_ends(start: date, end: date) -> tuple[date, ...]:
    periods: list[date] = []
    year, month = start.year, start.month
    while (year, month) <= (end.year, end.month):
        day = calendar.monthrange(year, month)[1]
        periods.append(date(year, month, day))
        if month == 12:
            year += 1
            month = 1
        else:
            month += 1
    return tuple(periods)


def _is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    value_type = type(value)
    return value_type.__name__ in {"NAType", "NaTType"} and value_type.__module__.startswith(
        "pandas"
    )


def _decimal_text(value: Decimal | None) -> str | None:
    return None if value is None else str(value)


def _json_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [_json_value(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return repr(value)
