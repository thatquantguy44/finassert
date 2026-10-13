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
from finassert.rules import (
    NullPolicy,
    cash_reconciles,
    custom_rule,
    nav_reconciles,
    non_negative,
    weights_sum_to_one,
)

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
    "cash_reconciles",
    "check",
    "custom_rule",
    "nav_reconciles",
    "non_negative",
    "weights_sum_to_one",
]
