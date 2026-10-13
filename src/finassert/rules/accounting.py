"""Accounting reconciliation rules (specification 0002, milestone 2).

Both rules check an accounting identity within each group of rows, for example
each portfolio and currency. Currencies are never converted: a file that holds
several currencies must name its currency column so each currency reconciles
separately. Every result records the equation and sign convention it checked.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, ClassVar

from finassert.adapters.contracts import ColumnMapping, FieldAggregation, GroupKey
from finassert.core.models import Outcome, Severity, ValidationResult
from finassert.numerical import Numeric, Tolerance, coerce_tolerance
from finassert.rules._grouping import Group, Wording, evaluate_groups
from finassert.rules._helpers import precise_sum
from finassert.rules.base import NullPolicy

_RECONCILE = Wording(
    action="reconcile",
    passes="reconcile",
    fails="do not reconcile",
    unusable="cannot be reconciled",
    file_passes="reconciles",
    file_fails="does not reconcile",
)


class OutflowSign(StrEnum):
    """How a file records cash leaving an account."""

    POSITIVE = "positive"
    """Outflows are positive amounts and are subtracted."""
    NEGATIVE = "negative"
    """Outflows are negative amounts and are added."""


class CashGrain(StrEnum):
    """What one row of a cash file describes."""

    SUMMARY = "summary"
    """One row per group holds the opening balance, flows, and closing balance."""
    TRANSACTIONS = "transactions"
    """Each row is a movement carrying the running balance before and after it."""


def _difference(observed: Numeric, expected: Numeric) -> Numeric:
    return precise_sum([observed, -expected])


def _currency_note(mapping: ColumnMapping, currency_key: str | None) -> str:
    column = currency_key or next(
        (key.column for key in mapping.group_keys if key.name == "currency"), None
    )
    if column is not None:
        return f"reconciled separately for each value of {column!r}"
    return "not grouped by currency: assumes all amounts in a group share one currency"


@dataclass(frozen=True, slots=True)
class CashReconciliationRule:
    """Check that cash balances roll forward within each group.

    With ``outflow_sign`` positive the identity is
    ``closing = opening + inflows - outflows + cash_pnl``; with negative
    outflows it is ``closing = opening + inflows + outflows + cash_pnl``.
    ``cash_pnl`` is optional. Use :func:`cash_reconciles` to build one.
    """

    mapping: ColumnMapping
    outflow_sign: OutflowSign
    tolerance: Tolerance = field(default_factory=Tolerance)
    null_policy: NullPolicy = NullPolicy.FAIL
    severity: Severity = Severity.ERROR
    max_violations: int = 20
    currency_key: str | None = None
    rule_id: str = "accounting.cash_reconciles"
    name: str = "Cash balances roll forward"

    required_semantics: ClassVar[tuple[str, ...]] = (
        "opening_cash",
        "inflows",
        "outflows",
        "closing_cash",
    )

    def __post_init__(self) -> None:
        _validate_common(self)
        self.mapping.required_aggregations(*self.semantics)
        if self.mapping.uses_ordered_aggregation and self.mapping.order_key is None:
            raise ValueError(
                "first/last balances need an ordering column; set order_by to a date or "
                "sequence column"
            )

    @property
    def semantics(self) -> tuple[str, ...]:
        """Return the fields this rule reads, including optional cash P&L."""
        optional = ("cash_pnl",) if "cash_pnl" in self.mapping.columns else ()
        return (*self.required_semantics, *optional)

    @property
    def equation(self) -> str:
        """Return the identity checked, in the file's sign convention."""
        flow = "+ outflows" if self.outflow_sign is OutflowSign.NEGATIVE else "- outflows"
        pnl = " + cash_pnl" if "cash_pnl" in self.mapping.columns else ""
        return f"closing_cash = opening_cash + inflows {flow}{pnl}"

    def evaluate(self, data: Any) -> ValidationResult:
        """Reconcile each group's closing balance."""
        sign = -1 if self.outflow_sign is OutflowSign.POSITIVE else 1

        def check(group: Group) -> dict[str, Any] | None:
            totals = {
                semantic: group.aggregate(semantic, self.mapping) for semantic in self.semantics
            }
            expected = precise_sum(
                [
                    totals["opening_cash"],
                    totals["inflows"],
                    totals["outflows"] if sign > 0 else -totals["outflows"],
                    totals.get("cash_pnl", 0),
                ]
            )
            observed = totals["closing_cash"]
            if self.tolerance.is_close(observed, expected):
                return None
            return {
                "reason": "does_not_reconcile",
                "observed": observed,
                "expected": expected,
                "difference": _difference(observed, expected),
            }

        return evaluate_groups(
            self,
            data,
            self.semantics,
            check,
            wording=_RECONCILE,
            description={
                "equation": self.equation,
                "outflow_sign": self.outflow_sign.value,
                "aggregations": {
                    semantic: self.mapping.aggregation_for(semantic).value
                    for semantic in self.semantics
                },
                "order_by": self.mapping.order_key,
                "currency": _currency_note(self.mapping, self.currency_key),
            },
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
        return _result(self, outcome, message, metadata, observed, expected)


@dataclass(frozen=True, slots=True)
class NavReconciliationRule:
    """Check that position market values add up to the reported NAV.

    Within each group, ``sum(market_value) = nav``. Market values carry their
    own signs, so liabilities and short positions are negative rows. The NAV
    may be repeated on every row or given on only some rows, but all the values
    given in a group must agree. Use :func:`nav_reconciles` to build one.
    """

    mapping: ColumnMapping
    tolerance: Tolerance = field(default_factory=Tolerance)
    null_policy: NullPolicy = NullPolicy.FAIL
    severity: Severity = Severity.ERROR
    max_violations: int = 20
    currency_key: str | None = None
    rule_id: str = "accounting.nav_reconciles"
    name: str = "Market values add up to the reported NAV"

    required_semantics: ClassVar[tuple[str, ...]] = ("market_value", "nav")
    equation: ClassVar[str] = "sum(market_value) = nav"

    def __post_init__(self) -> None:
        _validate_common(self)
        if self.mapping.aggregations.get("market_value") is not FieldAggregation.SUM:
            raise ValueError("market_value must be summed")
        if self.mapping.aggregations.get("nav") is not FieldAggregation.REQUIRE_UNIQUE:
            raise ValueError("nav must use the require_unique aggregation")

    def evaluate(self, data: Any) -> ValidationResult:
        """Reconcile each group's market values with its reported NAV."""

        def check(group: Group) -> dict[str, Any] | None:
            if not group.values["nav"]:
                return {"reason": "no_reported_nav"}
            nav = group.aggregate("nav", self.mapping)
            total = group.aggregate("market_value", self.mapping)
            if self.tolerance.is_close(total, nav):
                return None
            return {
                "reason": "does_not_reconcile",
                "observed": total,
                "expected": nav,
                "difference": _difference(total, nav),
            }

        return evaluate_groups(
            self,
            data,
            self.required_semantics,
            check,
            blank_allowed=("nav",),
            wording=_RECONCILE,
            description={
                "equation": self.equation,
                "currency": _currency_note(self.mapping, self.currency_key),
            },
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
        return _result(self, outcome, message, metadata, observed, expected)


def _validate_common(rule: CashReconciliationRule | NavReconciliationRule) -> None:
    if rule.max_violations < 0:
        raise ValueError("max_violations must be non-negative")
    if rule.null_policy is NullPolicy.IGNORE:
        raise ValueError(
            "null_policy 'ignore' is not allowed: leaving out rows changes the totals; "
            "use 'fail' or 'skip'"
        )
    rule.mapping.required_columns(*rule.required_semantics)


def _result(
    rule: CashReconciliationRule | NavReconciliationRule,
    outcome: Outcome,
    message: str,
    metadata: dict[str, Any],
    observed: Any,
    expected: Any,
) -> ValidationResult:
    return ValidationResult(
        rule_id=rule.rule_id,
        rule_name=rule.name,
        outcome=outcome,
        severity=rule.severity,
        message=message,
        observed=observed,
        expected=expected,
        tolerance=rule.tolerance.to_dict(),
        metadata=metadata,
    )


def _group_keys(group_by: Sequence[str], currency: str | None) -> tuple[GroupKey, ...]:
    if isinstance(group_by, str):
        raise TypeError("group_by must be a list of column names")
    keys = [GroupKey(column, column) for column in group_by]
    if currency is not None:
        keys.append(GroupKey("currency", currency))
    return tuple(keys)


def cash_reconciles(
    *,
    outflow_sign: OutflowSign | str,
    opening_cash: str | None = None,
    inflows: str | None = None,
    outflows: str | None = None,
    closing_cash: str | None = None,
    cash_pnl: str | None = None,
    group_by: Sequence[str] = (),
    currency: str | None = None,
    grain: CashGrain | str = CashGrain.SUMMARY,
    order_by: str | None = None,
    row_key: str | None = None,
    mapping: ColumnMapping | None = None,
    tolerance: Numeric | Tolerance = 0,
    null_policy: NullPolicy | str = NullPolicy.FAIL,
    severity: Severity | str = Severity.ERROR,
    max_violations: int = 20,
) -> CashReconciliationRule:
    """Create a rule checking that cash rolls from opening to closing balance.

    Name the columns directly, or pass a complete :class:`ColumnMapping` (with
    explicit aggregations) for full control; not both.

    Args:
        outflow_sign: ``"positive"`` when outflows are recorded as positive
            amounts, ``"negative"`` when recorded as negative amounts. There is
            no default: guessing a sign convention would hide real breaks.
        opening_cash: Column with the balance at the start.
        inflows: Column with cash received.
        outflows: Column with cash paid out.
        closing_cash: Column with the balance at the end.
        cash_pnl: Optional column with cash income or expense, such as interest.
        group_by: Columns identifying each account, such as a portfolio column.
        currency: Currency column; each currency reconciles separately. Omit
            only when every group holds a single currency.
        grain: ``"summary"`` for one row per group, or ``"transactions"`` for
            movement rows carrying running balances, which needs ``order_by``.
        order_by: Sequence number or timestamp ordering transaction rows; it must
            be unique within each group at its first and last rows.
        row_key: Column used to label rows in the report.
        mapping: A complete mapping, instead of the column arguments above.
        tolerance: Allowed difference, in the currency's units.
        null_policy: ``"fail"`` or ``"skip"`` when a value is blank.
        severity: Severity recorded with the result.
        max_violations: Maximum groups or rows listed in the report.
    """
    sign = OutflowSign(outflow_sign)
    currency_key = currency
    if mapping is None:
        named = {
            "opening_cash": opening_cash,
            "inflows": inflows,
            "outflows": outflows,
            "closing_cash": closing_cash,
        }
        absent = [name for name, column in named.items() if column is None]
        if absent:
            raise ValueError(f"name the column for: {', '.join(absent)}")
        columns = {name: column for name, column in named.items() if column is not None}
        if cash_pnl is not None:
            columns["cash_pnl"] = cash_pnl
        chosen = CashGrain(grain)
        if chosen is CashGrain.SUMMARY and order_by is not None:
            raise ValueError("order_by is only used with grain='transactions'")
        if chosen is CashGrain.TRANSACTIONS:
            if order_by is None:
                raise ValueError("transaction rows need order_by, a date or sequence column")
            balances = {
                "opening_cash": FieldAggregation.FIRST,
                "closing_cash": FieldAggregation.LAST,
            }
            flows = FieldAggregation.SUM
        else:
            balances = {
                "opening_cash": FieldAggregation.REQUIRE_UNIQUE,
                "closing_cash": FieldAggregation.REQUIRE_UNIQUE,
            }
            flows = FieldAggregation.REQUIRE_UNIQUE
        aggregations: dict[str, FieldAggregation] = {
            **balances,
            **{name: flows for name in ("inflows", "outflows", "cash_pnl") if name in columns},
        }
        mapping = ColumnMapping(
            columns,
            group_keys=_group_keys(group_by, currency),
            row_key=row_key,
            aggregations=aggregations,
            order_key=order_by,
        )
    elif (
        any(
            value is not None
            for value in (opening_cash, inflows, outflows, closing_cash, cash_pnl, currency)
        )
        or group_by
        or order_by
        or row_key
        or CashGrain(grain) is not CashGrain.SUMMARY
    ):
        raise ValueError("pass either mapping or column names, not both")
    return CashReconciliationRule(
        mapping=mapping,
        outflow_sign=sign,
        tolerance=coerce_tolerance(tolerance),
        null_policy=NullPolicy(null_policy),
        severity=Severity(severity),
        max_violations=max_violations,
        currency_key=currency_key,
    )


def nav_reconciles(
    *,
    market_value: str,
    nav: str,
    group_by: Sequence[str] = (),
    currency: str | None = None,
    row_key: str | None = None,
    tolerance: Numeric | Tolerance = 0,
    null_policy: NullPolicy | str = NullPolicy.FAIL,
    severity: Severity | str = Severity.ERROR,
    max_violations: int = 20,
) -> NavReconciliationRule:
    """Create a rule checking that market values add up to the reported NAV.

    Args:
        market_value: Column with each line's signed market value; liabilities
            and short positions are negative.
        nav: Column with the reported net asset value, repeated on every row or
            given on some rows of each group.
        group_by: Columns identifying each portfolio or fund.
        currency: Currency column; each currency reconciles separately. Omit when
            market values and NAV are stated in one currency per group.
        row_key: Column used to label rows in the report.
        tolerance: Allowed difference, in the currency's units.
        null_policy: ``"fail"`` or ``"skip"`` when a market value is blank.
        severity: Severity recorded with the result.
        max_violations: Maximum groups or rows listed in the report.
    """
    mapping = ColumnMapping(
        {"market_value": market_value, "nav": nav},
        group_keys=_group_keys(group_by, currency),
        row_key=row_key,
        aggregations={
            "market_value": FieldAggregation.SUM,
            "nav": FieldAggregation.REQUIRE_UNIQUE,
        },
    )
    return NavReconciliationRule(
        mapping=mapping,
        tolerance=coerce_tolerance(tolerance),
        null_policy=NullPolicy(null_policy),
        severity=Severity(severity),
        max_violations=max_violations,
        currency_key=currency,
    )
