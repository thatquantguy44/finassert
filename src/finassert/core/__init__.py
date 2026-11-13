"""Core validation contracts."""

from finassert.core.engine import check
from finassert.core.exceptions import GroupAggregationError
from finassert.core.models import (
    DiagnosticCollection,
    Outcome,
    Severity,
    ValidationReport,
    ValidationResult,
)
from finassert.core.protocols import ColumnSource, GroupedRule, Rule

__all__ = [
    "ColumnSource",
    "DiagnosticCollection",
    "GroupAggregationError",
    "GroupedRule",
    "Outcome",
    "Rule",
    "Severity",
    "ValidationReport",
    "ValidationResult",
    "check",
]
