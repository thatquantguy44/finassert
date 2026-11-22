"""Composite monthly performance audit rule (specification 0020)."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
from typing import TYPE_CHECKING, Any

from finassert.adapters._column import extract_columns
from finassert.core.models import (
    DiagnosticCollection,
    Outcome,
    Severity,
    ValidationResult,
)
from finassert.numerical import Numeric, Tolerance, coerce_tolerance
from finassert.rules.returns import ReturnUnit
from finassert.units import Money

if TYPE_CHECKING:
    from finassert.performance import MonthlyPerformanceReference


@dataclass(frozen=True, slots=True)
class MonthlyPerformanceAuditRule:
    """One composite check for monthly returns, coverage, and cumulative tie-outs."""

    period_end: str
    strategy_return: str
    benchmark_return: str
    reported_strategy_cumulative: str
    reported_benchmark_cumulative: str
    window_start: date | str
    window_end: date | str
    periodic_return_unit: ReturnUnit
    reported_return_unit: ReturnUnit
    strategy_id: str
    benchmark_id: str
    base_currency: str
    valuation_convention: str
    strategy_fee_treatment: str
    benchmark_fee_treatment: str
    tolerance: Tolerance
    row_key: str | None = None
    severity: Severity = Severity.ERROR
    max_violations: int = 20
    rule_id: str = "performance.monthly_performance_audit"
    name: str = "Monthly performance matches periodic returns"

    def __post_init__(self) -> None:
        columns = (
            self.period_end,
            self.strategy_return,
            self.benchmark_return,
            self.reported_strategy_cumulative,
            self.reported_benchmark_cumulative,
        )
        if any(not isinstance(column, str) or not column.strip() for column in columns):
            raise ValueError("all monthly audit column mappings must be non-empty text")
        if len(set(columns)) != len(columns):
            raise ValueError("each monthly audit value must use a distinct source column")
        if self.row_key is not None:
            if not isinstance(self.row_key, str) or not self.row_key.strip():
                raise ValueError("row_key must be non-empty text when provided")
            if self.row_key in columns:
                raise ValueError("row_key must be distinct from every audit value column")

        from finassert.performance import _window_date

        start = _window_date(self.window_start, "window_start")
        end = _window_date(self.window_end, "window_end")
        if start > end:
            raise ValueError("window_start must not be after window_end")
        object.__setattr__(self, "window_start", start)
        object.__setattr__(self, "window_end", end)

        object.__setattr__(self, "periodic_return_unit", ReturnUnit(self.periodic_return_unit))
        object.__setattr__(self, "reported_return_unit", ReturnUnit(self.reported_return_unit))
        object.__setattr__(self, "severity", Severity(self.severity))

        for name in (
            "strategy_id",
            "benchmark_id",
            "valuation_convention",
            "strategy_fee_treatment",
            "benchmark_fee_treatment",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be non-empty text")
        object.__setattr__(self, "base_currency", Money(Decimal(0), self.base_currency).currency)

        tolerance = coerce_tolerance(self.tolerance)
        if tolerance.relative != 0:
            raise ValueError("monthly performance tie-outs support absolute tolerance only")
        object.__setattr__(self, "tolerance", tolerance)
        if type(self.max_violations) is not int or self.max_violations < 0:
            raise ValueError("max_violations must be a non-negative integer")

    def evaluate(self, data: Any) -> ValidationResult:
        """Preflight the source and reconcile both reported cumulative series."""
        from finassert.performance import (
            _IssueCollector,
            _periodic_return,
            monthly_performance_reference,
        )

        reference = monthly_performance_reference(
            data,
            period_end=self.period_end,
            strategy_return=self.strategy_return,
            benchmark_return=self.benchmark_return,
            window_start=self.window_start,
            window_end=self.window_end,
            return_unit=self.periodic_return_unit,
            row_key=self.row_key,
            max_violations=self.max_violations,
        )
        metadata = self._policy_metadata(reference)
        if not reference.available:
            assert reference.summary is None
            diagnostic = DiagnosticCollection(
                kind="preflight_issues",
                count=reference.issue_count,
                limit=self.max_violations,
                observations=tuple(issue.to_dict() for issue in reference.issues),
            )
            metadata["preflight"] = {
                "issue_count": reference.issue_count,
                "issue_counts": dict(reference.issue_counts),
                "issues_truncated": reference.issues_truncated,
            }
            return ValidationResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                outcome=Outcome.FAILED,
                severity=self.severity,
                message=(
                    f"Monthly performance preflight found {reference.issue_count} issue(s); "
                    "full-window calculations and tie-outs were not run."
                ),
                observed={
                    "preflight_issue_count": reference.issue_count,
                    "issue_counts": dict(reference.issue_counts),
                },
                expected={"complete_monthly_window": len(reference.expected_periods)},
                tolerance=self.tolerance.to_dict(),
                metadata=metadata,
                diagnostics=(diagnostic,),
            )

        assert reference.summary is not None
        reported, _ = extract_columns(
            data,
            [self.reported_strategy_cumulative, self.reported_benchmark_cumulative],
            row_key=self.row_key,
        )
        invalid_reported = _IssueCollector(self.max_violations)
        tie_out_counts: Counter[str] = Counter()
        tie_out_examples: list[dict[str, Any]] = []
        comparisons = 0
        comparison_columns = (
            ("strategy_tie_out", self.reported_strategy_cumulative, "strategy"),
            ("benchmark_tie_out", self.reported_benchmark_cumulative, "benchmark"),
        )

        for period in reference.periods:
            for reason, column, series in comparison_columns:
                observed = _periodic_return(
                    reported[column][period.source_position],
                    column=column,
                    source_row=period.source_row,
                    position=period.source_position,
                    period_end=period.period_end,
                    unit=self.reported_return_unit,
                    issues=invalid_reported,
                )
                if observed is None:
                    continue
                comparisons += 1
                expected = (
                    period.strategy_cumulative_return
                    if series == "strategy"
                    else period.benchmark_cumulative_return
                )
                with localcontext() as context:
                    context.prec = 50
                    context.rounding = ROUND_HALF_EVEN
                    within_tolerance = self.tolerance.is_close(observed, expected)
                    difference = observed - expected
                if within_tolerance:
                    continue
                tie_out_counts[reason] += 1
                if len(tie_out_examples) < self.max_violations:
                    tie_out_examples.append(
                        {
                            "code": reason,
                            "message": f"Reported cumulative {series} return does not tie out.",
                            "source_row": period.source_row,
                            "source_position": period.source_position,
                            "period_end": period.period_end.isoformat(),
                            "field": column,
                            "observed": str(observed),
                            "expected": str(expected),
                            "difference": str(difference),
                            "absolute_tolerance": str(self.tolerance.absolute),
                        }
                    )

        invalid_diagnostic = DiagnosticCollection(
            kind="reported_input_issues",
            count=invalid_reported.count,
            limit=self.max_violations,
            observations=tuple(issue.to_dict() for issue in invalid_reported.items),
        )
        tie_out_count = sum(tie_out_counts.values())
        tie_out_diagnostic = DiagnosticCollection(
            kind="tie_out_violations",
            count=tie_out_count,
            limit=self.max_violations,
            observations=tuple(tie_out_examples),
        )
        issue_count = invalid_reported.count + tie_out_count
        metadata["reference"] = {
            "summary": reference.summary.to_dict(),
            "complete_months": reference.summary.complete_months,
        }
        metadata["tie_out"] = {
            "comparison_count": comparisons,
            "issue_count": issue_count,
            "reported_input_issue_count": invalid_reported.count,
            "reported_input_issue_counts": dict(sorted(invalid_reported.counts.items())),
            "tie_out_failure_counts": dict(sorted(tie_out_counts.items())),
            "tie_out_issues_truncated": tie_out_count > len(tie_out_examples),
            "absolute_tolerance": str(self.tolerance.absolute),
        }
        return ValidationResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            outcome=Outcome.FAILED if issue_count else Outcome.PASSED,
            severity=self.severity,
            message=(
                f"Monthly performance audit found {issue_count} issue(s) across "
                f"{reference.summary.complete_months} month(s)."
                if issue_count
                else f"Reported strategy and benchmark returns tie out across "
                f"{reference.summary.complete_months} month(s)."
            ),
            observed={"issue_count": issue_count, "comparison_count": comparisons},
            expected={"issue_count": 0, "comparison_count": 2 * len(reference.periods)},
            tolerance=self.tolerance.to_dict(),
            metadata=metadata,
            diagnostics=(invalid_diagnostic, tie_out_diagnostic),
        )

    def _policy_metadata(self, reference: MonthlyPerformanceReference) -> dict[str, Any]:
        assert isinstance(self.window_start, date)
        assert isinstance(self.window_end, date)
        return {
            "strategy_id": self.strategy_id,
            "benchmark_id": self.benchmark_id,
            "base_currency": self.base_currency,
            "valuation_convention": self.valuation_convention,
            "strategy_fee_treatment": self.strategy_fee_treatment,
            "benchmark_fee_treatment": self.benchmark_fee_treatment,
            "window": {
                "start": self.window_start.isoformat(),
                "end": self.window_end.isoformat(),
                "expected_months": len(reference.expected_periods),
            },
            "columns": {
                "period_end": self.period_end,
                "strategy_return": self.strategy_return,
                "benchmark_return": self.benchmark_return,
                "reported_strategy_cumulative": self.reported_strategy_cumulative,
                "reported_benchmark_cumulative": self.reported_benchmark_cumulative,
                "row_key": self.row_key,
            },
            "return_units": {
                "periodic": self.periodic_return_unit.value,
                "reported": self.reported_return_unit.value,
            },
            "period_count": len(reference.periods),
        }


def monthly_performance_audit(
    *,
    period_end: str,
    strategy_return: str,
    benchmark_return: str,
    reported_strategy_cumulative: str,
    reported_benchmark_cumulative: str,
    window_start: date | str,
    window_end: date | str,
    periodic_return_unit: ReturnUnit | str,
    reported_return_unit: ReturnUnit | str,
    strategy_id: str,
    benchmark_id: str,
    base_currency: str,
    valuation_convention: str,
    strategy_fee_treatment: str,
    benchmark_fee_treatment: str,
    tolerance: Numeric | Tolerance,
    row_key: str | None = None,
    severity: Severity | str = Severity.ERROR,
    max_violations: int = 20,
) -> MonthlyPerformanceAuditRule:
    """Create one composite monthly performance coverage and tie-out check.

    Financial tolerances are absolute decimal-return allowances. A relative
    tolerance is rejected so the same policy has one clear financial meaning.
    """
    return MonthlyPerformanceAuditRule(
        period_end=period_end,
        strategy_return=strategy_return,
        benchmark_return=benchmark_return,
        reported_strategy_cumulative=reported_strategy_cumulative,
        reported_benchmark_cumulative=reported_benchmark_cumulative,
        window_start=window_start,
        window_end=window_end,
        periodic_return_unit=ReturnUnit(periodic_return_unit),
        reported_return_unit=ReturnUnit(reported_return_unit),
        strategy_id=strategy_id,
        benchmark_id=benchmark_id,
        base_currency=base_currency,
        valuation_convention=valuation_convention,
        strategy_fee_treatment=strategy_fee_treatment,
        benchmark_fee_treatment=benchmark_fee_treatment,
        tolerance=coerce_tolerance(tolerance),
        row_key=row_key,
        severity=Severity(severity),
        max_violations=max_violations,
    )
