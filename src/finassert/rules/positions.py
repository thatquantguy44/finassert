"""Position roll-forward (specification 0002, milestone 3).

A share count rolls forward like a cash balance: the closing quantity is the
opening quantity plus buys, less sells, plus any other movements. The file must
say how it records sells, because a wrong guess would hide real breaks.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, ClassVar

from finassert.adapters.contracts import ColumnMapping, FieldAggregation
from finassert.core.models import Outcome, Severity, ValidationResult
from finassert.numerical import Numeric, Tolerance, coerce_tolerance
from finassert.rules._grouping import Group, Wording, evaluate_groups, group_keys_for
from finassert.rules._helpers import precise_sum
from finassert.rules.base import NullPolicy

_ROLLS = Wording(
    action="reconcile",
    passes="roll forward",
    fails="do not roll forward",
    unusable="cannot be rolled forward",
    file_passes="rolls forward",
    file_fails="does not roll forward",
)


class SellSign(StrEnum):
    """How a file records quantities sold."""

    POSITIVE = "positive"
    """Sells are positive quantities and are subtracted."""
    NEGATIVE = "negative"
    """Sells are negative quantities and are added."""


@dataclass(frozen=True, slots=True)
class PositionRollForwardRule:
    """Check that each position's quantity rolls from opening to closing.

    With ``sell_sign`` positive the identity is
    ``closing = opening + buys - sells + adjustments``; with negative sells it is
    ``closing = opening + buys + sells + adjustments``. ``adjustments`` is optional,
    signed, and added: splits, transfers, and corporate actions. Each position is
    one row (or several rows that agree). Use :func:`position_rolls_forward` to
    build one.
    """

    mapping: ColumnMapping
    sell_sign: SellSign
    tolerance: Tolerance = field(default_factory=Tolerance)
    null_policy: NullPolicy = NullPolicy.FAIL
    severity: Severity = Severity.ERROR
    max_violations: int = 20
    rule_id: str = "accounting.position_rolls_forward"
    name: str = "Position quantities roll forward"

    required_semantics: ClassVar[tuple[str, ...]] = (
        "opening_quantity",
        "buys",
        "sells",
        "closing_quantity",
    )

    def __post_init__(self) -> None:
        if self.max_violations < 0:
            raise ValueError("max_violations must be non-negative")
        if self.null_policy is NullPolicy.IGNORE:
            raise ValueError(
                "null_policy 'ignore' is not allowed: leaving out rows changes the totals; "
                "use 'fail' or 'skip'"
            )
        if not self.mapping.group_keys:
            raise ValueError(
                "name the columns that identify each position, such as portfolio and ticker"
            )
        self.mapping.required_columns(*self.semantics)
        self.mapping.required_aggregations(*self.semantics)

    @property
    def semantics(self) -> tuple[str, ...]:
        """Return the fields this rule reads, including optional adjustments."""
        optional = ("adjustments",) if "adjustments" in self.mapping.columns else ()
        return (*self.required_semantics, *optional)

    @property
    def equation(self) -> str:
        """Return the identity checked, in the file's sign convention."""
        sells = "+ sells" if self.sell_sign is SellSign.NEGATIVE else "- sells"
        adjust = " + adjustments" if "adjustments" in self.mapping.columns else ""
        return f"closing_quantity = opening_quantity + buys {sells}{adjust}"

    def evaluate(self, data: Any) -> ValidationResult:
        """Roll forward each position's closing quantity."""
        sign = -1 if self.sell_sign is SellSign.POSITIVE else 1

        def check(group: Group) -> dict[str, Any] | None:
            totals = {name: group.aggregate(name, self.mapping) for name in self.semantics}
            expected = precise_sum(
                [
                    totals["opening_quantity"],
                    totals["buys"],
                    totals["sells"] if sign > 0 else -totals["sells"],
                    totals.get("adjustments", 0),
                ]
            )
            observed = totals["closing_quantity"]
            if self.tolerance.is_close(observed, expected):
                return None
            return {
                "reason": "does_not_roll_forward",
                "observed": observed,
                "expected": expected,
                "difference": precise_sum([observed, -expected]),
            }

        return evaluate_groups(
            self,
            data,
            self.semantics,
            check,
            wording=_ROLLS,
            description={"equation": self.equation, "sell_sign": self.sell_sign.value},
        )

    def _grouped_result(
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


def position_rolls_forward(
    *,
    sell_sign: SellSign | str,
    opening_quantity: str,
    buys: str,
    sells: str,
    closing_quantity: str,
    group_by: Sequence[str],
    adjustments: str | None = None,
    row_key: str | None = None,
    tolerance: Numeric | Tolerance = 0,
    null_policy: NullPolicy | str = NullPolicy.FAIL,
    severity: Severity | str = Severity.ERROR,
    max_violations: int = 20,
) -> PositionRollForwardRule:
    """Create a rule checking that each position's quantity rolls forward.

    Args:
        sell_sign: ``"positive"`` when sells are recorded as positive quantities,
            ``"negative"`` when recorded as negative quantities. There is no
            default: guessing a sign convention would hide real breaks.
        opening_quantity: Column with the quantity at the start.
        buys: Column with the quantity bought.
        sells: Column with the quantity sold.
        closing_quantity: Column with the quantity at the end.
        group_by: Columns identifying each position, such as portfolio and ticker.
            Required: a file is not one position.
        adjustments: Optional column with other signed movements (splits,
            transfers, corporate actions), added to the opening quantity.
        row_key: Column used to label rows in the report.
        tolerance: Allowed difference, in units of the security.
        null_policy: ``"fail"`` or ``"skip"`` when a quantity is blank.
        severity: Severity recorded with the result.
        max_violations: Maximum failing positions listed in the report.
    """
    sign = SellSign(sell_sign)
    if isinstance(group_by, str):
        raise TypeError("group_by must be a list of column names")
    columns = {
        "opening_quantity": opening_quantity,
        "buys": buys,
        "sells": sells,
        "closing_quantity": closing_quantity,
    }
    if adjustments is not None:
        columns["adjustments"] = adjustments
    return PositionRollForwardRule(
        mapping=ColumnMapping(
            columns,
            group_keys=group_keys_for(group_by, None),
            row_key=row_key,
            aggregations={name: FieldAggregation.REQUIRE_UNIQUE for name in columns},
        ),
        sell_sign=sign,
        tolerance=coerce_tolerance(tolerance),
        null_policy=NullPolicy(null_policy),
        severity=Severity(severity),
        max_violations=max_violations,
    )
