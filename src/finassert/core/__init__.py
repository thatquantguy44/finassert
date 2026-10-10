"""Core validation contracts."""

from finassert.core.engine import check
from finassert.core.exceptions import GroupAggregationError
from finassert.core.models import Outcome, Severity, ValidationReport, ValidationResult
from finassert.core.protocols import ColumnSource, GroupedRule, Rule

__all__ = [
    "ColumnSource",
    "GroupAggregationError",
    "GroupedRule",
    "Outcome",
    "Rule",
    "Severity",
    "ValidationReport",
    "ValidationResult",
    "check",
]
