"""Built-in and custom financial validation rules."""

from finassert.rules.accounting import (
    CashGrain,
    CashReconciliationRule,
    NavReconciliationRule,
    OutflowSign,
    cash_reconciles,
    nav_reconciles,
)
from finassert.rules.arithmetic import NonNegativeRule, non_negative
from finassert.rules.base import NullPolicy
from finassert.rules.custom import FunctionRule, custom_rule
from finassert.rules.exposure import (
    ExposureLimitRule,
    ExposureMeasure,
    PositionLimitRule,
    gross_within_limit,
    net_within_limit,
    position_within_limit,
)
from finassert.rules.grouped import aggregate_values
from finassert.rules.integrity import (
    NoDuplicatesRule,
    RequiredFieldsRule,
    no_duplicates,
    required_fields,
)
from finassert.rules.portfolio import WeightsSumToOneRule, weights_sum_to_one
from finassert.rules.returns import ReturnUnit, SimpleReturnReconcilesRule, simple_return_reconciles
from finassert.rules.valuation import MarketValueReconcilesRule, market_value_reconciles

__all__ = [
    "CashGrain",
    "CashReconciliationRule",
    "ExposureLimitRule",
    "ExposureMeasure",
    "FunctionRule",
    "MarketValueReconcilesRule",
    "NavReconciliationRule",
    "NoDuplicatesRule",
    "NonNegativeRule",
    "NullPolicy",
    "OutflowSign",
    "PositionLimitRule",
    "RequiredFieldsRule",
    "ReturnUnit",
    "SimpleReturnReconcilesRule",
    "WeightsSumToOneRule",
    "aggregate_values",
    "cash_reconciles",
    "custom_rule",
    "gross_within_limit",
    "market_value_reconciles",
    "nav_reconciles",
    "net_within_limit",
    "no_duplicates",
    "non_negative",
    "position_within_limit",
    "required_fields",
    "simple_return_reconciles",
    "weights_sum_to_one",
]
