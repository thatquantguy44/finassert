"""Market value consistency (specification 0002, milestone 3)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from finassert.core.models import Outcome, Severity, ValidationResult
from finassert.numerical import Numeric, Tolerance, coerce_tolerance
from finassert.rules._helpers import precise_product, precise_sum
from finassert.rules._rows import evaluate_rows
from finassert.rules.base import NullPolicy


@dataclass(frozen=True, slots=True)
class MarketValueReconcilesRule:
    """Check ``market_value = quantity * price * multiplier`` on every row.

    The multiplier column is optional; without it the multiplier is 1. Amounts
    are compared as given, in the file's own units and currency: nothing is
    converted, and a price quoted per 100 of par is not rescaled. Use
    :func:`market_value_reconciles` to build one.
    """

    quantity: str
    price: str
    market_value: str
    multiplier: str | None = None
    row_key: str | None = None
    tolerance: Tolerance = field(default_factory=Tolerance)
    null_policy: NullPolicy = NullPolicy.FAIL
    severity: Severity = Severity.ERROR
    max_violations: int = 20
    rule_id: str = "accounting.market_value_reconciles"
    name: str = "Market value equals quantity * price * multiplier"

    def __post_init__(self) -> None:
        if self.max_violations < 0:
            raise ValueError("max_violations must be non-negative")
        if self.null_policy is NullPolicy.IGNORE:
            raise ValueError(
                "null_policy 'ignore' is not allowed: a row with a blank value cannot be "
                "checked and must not be passed over silently; use 'fail' or 'skip'"
            )
        columns = [self.quantity, self.price, self.market_value]
        if self.multiplier is not None:
            columns.append(self.multiplier)
        if len(set(columns)) != len(columns):
            raise ValueError("each value must come from a different column")

    @property
    def equation(self) -> str:
        """Return the identity checked."""
        factor = " * multiplier" if self.multiplier else ""
        return f"market_value = quantity * price{factor}"

    def evaluate(self, data: Any) -> ValidationResult:
        """Check every row."""

        def check(values: dict[str, Numeric]) -> dict[str, Any] | None:
            factors = [values["quantity"], values["price"]]
            if self.multiplier:
                factors.append(values["multiplier"])
            expected = precise_product(factors)
            observed = values["market_value"]
            if self.tolerance.is_close(observed, expected):
                return None
            failure: dict[str, Any] = {
                "reason": "does_not_reconcile",
                "quantity": values["quantity"],
                "price": values["price"],
            }
            if self.multiplier:
                failure["multiplier"] = values["multiplier"]
            failure.update(
                observed=observed,
                expected=expected,
                difference=precise_sum([observed, -expected]),
            )
            return failure

        columns = {
            "quantity": self.quantity,
            "price": self.price,
            "market_value": self.market_value,
        }
        if self.multiplier:
            columns["multiplier"] = self.multiplier
        return evaluate_rows(
            self,
            data,
            columns,
            check,
            row_key=self.row_key,
            noun="position",
            description={"equation": self.equation, "columns": columns},
        )

    def _row_result(
        self,
        outcome: Outcome,
        message: str,
        metadata: dict[str, Any],
        *,
        observed: Any = None,
        expected: Any = None,
    ) -> ValidationResult:
        return ValidationResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            outcome=outcome,
            severity=self.severity,
            message=message,
            observed=observed,
            expected=expected,
            tolerance=self.tolerance.to_dict(),
            metadata=metadata,
        )


def market_value_reconciles(
    *,
    quantity: str,
    price: str,
    market_value: str,
    multiplier: str | None = None,
    row_key: str | None = None,
    tolerance: Numeric | Tolerance = 0,
    null_policy: NullPolicy | str = NullPolicy.FAIL,
    severity: Severity | str = Severity.ERROR,
    max_violations: int = 20,
) -> MarketValueReconcilesRule:
    """Create a rule checking that each row's market value is quantity * price * multiplier.

    Args:
        quantity: Column with the number of units held (negative for shorts).
        price: Column with the price of one unit, in the market value's currency.
        market_value: Column with the reported market value.
        multiplier: Optional column with a contract multiplier or similar factor.
        row_key: Column used to label rows in the report, such as a ticker.
        tolerance: Allowed difference of the market value, in its units; a
            relative part allows for prices rounded before multiplying.
        null_policy: ``"fail"`` or ``"skip"`` when a value is blank.
        severity: Severity recorded with the result.
        max_violations: Maximum rows listed in the report.
    """
    return MarketValueReconcilesRule(
        quantity=quantity,
        price=price,
        market_value=market_value,
        multiplier=multiplier,
        row_key=row_key,
        tolerance=coerce_tolerance(tolerance),
        null_policy=NullPolicy(null_policy),
        severity=Severity(severity),
        max_violations=max_violations,
    )
