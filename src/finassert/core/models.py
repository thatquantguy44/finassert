"""Structured validation results and reports."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from enum import Enum, StrEnum
from typing import Any


class Outcome(StrEnum):
    """The outcome of one rule evaluation."""

    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"


class Severity(StrEnum):
    """Business impact assigned to a validation result.

    A failed check of ``ERROR`` severity fails the report. A failed check of
    ``WARNING`` or ``INFO`` severity is reported but does not, unless a caller
    asks for a stricter threshold (for example ``--fail-on warning``).
    """

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

    @property
    def rank(self) -> int:
        """Return the severity's order: ``error`` above ``warning`` above ``info``."""
        return _RANKS[self.value]


_RANKS = {"error": 2, "warning": 1, "info": 0}


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Immutable result of evaluating one rule."""

    rule_id: str
    rule_name: str
    outcome: Outcome
    severity: Severity
    message: str
    observed: Any = None
    expected: Any = None
    tolerance: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        """Return whether this evaluation passed."""
        return self.outcome is Outcome.PASSED

    def blocks(self, fail_on: Severity = Severity.ERROR) -> bool:
        """Return whether this result fails a run that fails on ``fail_on`` and above.

        A check that could not run always blocks, because it is never a pass.
        A failed check blocks when its severity is at least ``fail_on``.
        """
        if self.outcome is Outcome.ERROR:
            return True
        return self.outcome is Outcome.FAILED and self.severity.rank >= fail_on.rank

    @property
    def blocking(self) -> bool:
        """Return whether this result fails the report (see :meth:`blocks`)."""
        return self.blocks()

    @property
    def warning(self) -> bool:
        """Return whether this is a failed check whose severity does not fail the report."""
        return self.outcome is Outcome.FAILED and not self.blocking

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible dictionary."""
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "passed": self.passed,
            "blocking": self.blocking,
            "outcome": self.outcome.value,
            "severity": self.severity.value,
            "message": self.message,
            "observed": _json_value(self.observed),
            "expected": _json_value(self.expected),
            "tolerance": _json_value(self.tolerance),
            "metadata": _json_value(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class ValidationReport:
    """Aggregate of results produced by a validation run.

    An empty report passes vacuously. Skipped rules do not fail a report. A rule
    that could not run fails it, and so does a failed rule of ``error``
    severity. A failed rule of ``warning`` or ``info`` severity is a warning: it
    is listed and counted but does not fail the report.
    """

    results: tuple[ValidationResult, ...] = ()

    @property
    def passed(self) -> bool:
        """Return ``True`` when no result blocks: nothing errored or failed at ``error``."""
        return not any(result.blocking for result in self.results)

    @property
    def warnings(self) -> tuple[ValidationResult, ...]:
        """Return failed results whose severity does not fail the report."""
        return tuple(result for result in self.results if result.warning)

    @property
    def blocking_failures(self) -> tuple[ValidationResult, ...]:
        """Return the results that fail the report."""
        return tuple(result for result in self.results if result.blocking)

    @property
    def counts_by_outcome(self) -> dict[str, int]:
        """Return counts for every outcome, including zero counts."""
        counts = Counter(result.outcome.value for result in self.results)
        return {outcome.value: counts[outcome.value] for outcome in Outcome}

    @property
    def counts_by_severity(self) -> dict[str, int]:
        """Return counts for every severity, including zero counts."""
        counts = Counter(result.severity.value for result in self.results)
        return {severity.value: counts[severity.value] for severity in Severity}

    @property
    def failures(self) -> tuple[ValidationResult, ...]:
        """Return failed and errored results."""
        return tuple(
            result for result in self.results if result.outcome in {Outcome.FAILED, Outcome.ERROR}
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible dictionary."""
        return {
            "passed": self.passed,
            "blocking_failures": len(self.blocking_failures),
            "warnings": len(self.warnings),
            "counts_by_outcome": self.counts_by_outcome,
            "counts_by_severity": self.counts_by_severity,
            "results": [result.to_dict() for result in self.results],
        }

    def summary(self) -> str:
        """Render a concise human-readable terminal summary."""
        status = "PASS" if self.passed else "FAIL"
        counts = self.counts_by_outcome
        warned = len(self.warnings)
        noted = f" ({warned} warning{'s' if warned != 1 else ''})" if warned else ""
        header = (
            f"finassert {status}{noted}: {counts['passed']} passed, {counts['failed']} failed, "
            f"{counts['error']} errors, {counts['skipped']} skipped"
        )
        details = [
            f"- [{item.severity.value}] {item.rule_id}: {item.message}" for item in self.failures
        ]
        return "\n".join([header, *details])


def _json_value(value: Any) -> Any:
    """Convert common financial values to JSON-compatible primitives."""
    from decimal import Decimal

    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)
