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
    """Business impact assigned to a validation result."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


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

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible dictionary."""
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "passed": self.passed,
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

    An empty report passes vacuously. Skipped rules do not fail a report. Any
    failed or errored rule fails the report, independent of its severity.
    """

    results: tuple[ValidationResult, ...] = ()

    @property
    def passed(self) -> bool:
        """Return ``True`` when no result failed or errored."""
        return all(result.outcome in {Outcome.PASSED, Outcome.SKIPPED} for result in self.results)

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
            "counts_by_outcome": self.counts_by_outcome,
            "counts_by_severity": self.counts_by_severity,
            "results": [result.to_dict() for result in self.results],
        }

    def summary(self) -> str:
        """Render a concise human-readable terminal summary."""
        status = "PASS" if self.passed else "FAIL"
        counts = self.counts_by_outcome
        header = (
            f"finassert {status}: {counts['passed']} passed, {counts['failed']} failed, "
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
