"""Built-in and custom financial validation rules."""

from finassert.rules.arithmetic import NonNegativeRule, non_negative
from finassert.rules.base import NullPolicy
from finassert.rules.custom import FunctionRule, custom_rule
from finassert.rules.grouped import aggregate_values
from finassert.rules.portfolio import WeightsSumToOneRule, weights_sum_to_one

__all__ = [
    "FunctionRule",
    "NonNegativeRule",
    "NullPolicy",
    "WeightsSumToOneRule",
    "aggregate_values",
    "custom_rule",
    "non_negative",
    "weights_sum_to_one",
]
