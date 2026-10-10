"""Financial invariants, tested like code."""

from finassert.core import Outcome, Rule, Severity, ValidationReport, ValidationResult, check
from finassert.numerical import Tolerance
from finassert.rules import NullPolicy, custom_rule, non_negative, weights_sum_to_one

__all__ = [
    "NullPolicy",
    "Outcome",
    "Rule",
    "Severity",
    "Tolerance",
    "ValidationReport",
    "ValidationResult",
    "check",
    "custom_rule",
    "non_negative",
    "weights_sum_to_one",
]

__version__ = "0.1.0"
