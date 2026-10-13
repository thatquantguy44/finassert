"""Financial invariants, tested like code."""

from finassert._version import __version__
from finassert.core import (
    GroupAggregationError,
    GroupedRule,
    Outcome,
    Rule,
    Severity,
    ValidationReport,
    ValidationResult,
    check,
)
from finassert.numerical import Tolerance
from finassert.rules import NullPolicy, custom_rule, non_negative, weights_sum_to_one

__all__ = [
    "GroupAggregationError",
    "GroupedRule",
    "NullPolicy",
    "Outcome",
    "Rule",
    "Severity",
    "Tolerance",
    "ValidationReport",
    "ValidationResult",
    "__version__",
    "check",
    "custom_rule",
    "non_negative",
    "weights_sum_to_one",
]
