"""Allowlisted rule factories with plain-language descriptions."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from finassert.core.models import Severity
from finassert.rules import (
    CashGrain,
    NullPolicy,
    OutflowSign,
    cash_reconciles,
    nav_reconciles,
    non_negative,
    weights_sum_to_one,
)


class ParameterKind(StrEnum):
    """How a policy parameter is written and validated."""

    COLUMN = "column"
    COLUMNS = "columns"
    TOLERANCE = "tolerance"
    CHOICE = "choice"
    INTEGER = "integer"


@dataclass(frozen=True, slots=True)
class ParameterSpec:
    """One documented, typed factory parameter.

    Args:
        name: Keyword passed to the factory and written in policy files.
        kind: Validation and editing behavior for the value.
        label: Short human label for forms and reports.
        description: Plain-language explanation, including units where relevant.
        required: Whether a policy must supply the value.
        default: Value used by the factory when the policy omits the parameter.
        choices: Allowed values for ``ParameterKind.CHOICE``.
        minimum: Inclusive lower bound for ``ParameterKind.INTEGER``.
        allow_relative: Whether a ``ParameterKind.TOLERANCE`` may set a nonzero
            relative bound. Rules that ignore the relative part must reject it.
    """

    name: str
    kind: ParameterKind
    label: str
    description: str
    required: bool = False
    default: Any = None
    choices: tuple[str, ...] = ()
    minimum: int | None = None
    allow_relative: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible description."""
        return {
            "name": self.name,
            "kind": self.kind.value,
            "label": self.label,
            "description": self.description,
            "required": self.required,
            "default": None if self.default is None else str(self.default),
            "choices": list(self.choices),
            "minimum": self.minimum,
            "allow_relative": self.allow_relative,
        }


@dataclass(frozen=True, slots=True)
class RuleFactorySpec:
    """A rule factory that policy files may name, with its documentation.

    Args:
        name: Factory name written as ``rule:`` in policy files.
        rule_id: Stable identifier of rules the factory produces.
        title: Short plain-language title.
        summary: One sentence stating what the rule checks.
        rationale: Why the invariant matters financially.
        inappropriate_when: Situations in which the rule should not be applied.
        parameters: Accepted parameters in display order.
        factory: Callable invoked with validated keyword arguments.
    """

    name: str
    rule_id: str
    title: str
    summary: str
    rationale: str
    inappropriate_when: str
    parameters: tuple[ParameterSpec, ...]
    factory: Callable[..., Any]

    def parameter(self, name: str) -> ParameterSpec:
        """Return the named parameter specification."""
        for parameter in self.parameters:
            if parameter.name == name:
                return parameter
        raise KeyError(name)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible description without the factory callable."""
        return {
            "name": self.name,
            "rule_id": self.rule_id,
            "title": self.title,
            "summary": self.summary,
            "rationale": self.rationale,
            "inappropriate_when": self.inappropriate_when,
            "parameters": [parameter.to_dict() for parameter in self.parameters],
        }


class RuleCatalog:
    """Caller-owned allowlist of factories that policies may reference.

    Factories are looked up by ``name`` or by the ``rule_id`` they produce.
    Duplicate names or rule identifiers fail unless replacement is requested.
    """

    def __init__(self) -> None:
        self._specs: dict[str, RuleFactorySpec] = {}

    def register(self, spec: RuleFactorySpec, *, replace: bool = False) -> None:
        """Register ``spec`` or raise on a name or rule-identifier collision."""
        if not replace:
            if spec.name in self._specs:
                raise ValueError(f"factory {spec.name!r} is already registered")
            if any(existing.rule_id == spec.rule_id for existing in self._specs.values()):
                raise ValueError(f"rule_id {spec.rule_id!r} is already registered")
        self._specs[spec.name] = spec

    def resolve(self, reference: str) -> RuleFactorySpec:
        """Return the factory registered under a name or produced rule identifier."""
        if reference in self._specs:
            return self._specs[reference]
        for spec in self._specs.values():
            if spec.rule_id == reference:
                return spec
        raise KeyError(reference)

    def names(self) -> tuple[str, ...]:
        """Return factory names in sorted order."""
        return tuple(sorted(self._specs))

    def references(self) -> tuple[str, ...]:
        """Return every accepted factory name and rule identifier, sorted."""
        return tuple(sorted({*self._specs, *(spec.rule_id for spec in self._specs.values())}))

    def specs(self) -> tuple[RuleFactorySpec, ...]:
        """Return specifications ordered by factory name."""
        return tuple(self._specs[name] for name in self.names())

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible catalog description."""
        return {"rules": [spec.to_dict() for spec in self.specs()]}


_SEVERITY = ParameterSpec(
    name="severity",
    kind=ParameterKind.CHOICE,
    label="Severity",
    description=(
        "Business impact recorded with the result. Any failure fails the report "
        "regardless of severity."
    ),
    default=Severity.ERROR.value,
    choices=tuple(item.value for item in Severity),
)

_NULL_POLICY = ParameterSpec(
    name="null_policy",
    kind=ParameterKind.CHOICE,
    label="Blank cells",
    description=(
        "What to do with blank cells: 'fail' treats them as a failure, 'ignore' "
        "leaves them out, and 'skip' records the whole check as not run."
    ),
    default=NullPolicy.FAIL.value,
    choices=tuple(item.value for item in NullPolicy),
)


def default_catalog() -> RuleCatalog:
    """Return a new catalog containing every built-in rule factory."""
    catalog = RuleCatalog()
    catalog.register(
        RuleFactorySpec(
            name="weights_sum_to_one",
            rule_id="portfolio.weights_sum_to_one",
            title="Portfolio weights add up to 100%",
            summary="Checks that the values in a weight column add up to exactly 1.",
            rationale=(
                "Weights that do not add to 1 mean some holdings are missing, duplicated, "
                "or mis-scaled, so exposures and performance attribution will be wrong."
            ),
            inappropriate_when=(
                "Weights are written as percentages (40 rather than 0.4), the file holds "
                "several portfolios, or the portfolio is deliberately levered or holds "
                "cash outside the weight column."
            ),
            parameters=(
                ParameterSpec(
                    name="column",
                    kind=ParameterKind.COLUMN,
                    label="Weight column",
                    description="Column holding each position's weight as a fraction of 1.",
                    default="weight",
                ),
                ParameterSpec(
                    name="tolerance",
                    kind=ParameterKind.TOLERANCE,
                    label="Allowed difference",
                    description=(
                        "How far the total may be from 1 and still pass, for example 0.0001."
                    ),
                    default="1e-8",
                ),
                _NULL_POLICY,
                _SEVERITY,
            ),
            factory=weights_sum_to_one,
        )
    )
    catalog.register(
        RuleFactorySpec(
            name="non_negative",
            rule_id="arithmetic.non_negative",
            title="No negative values",
            summary="Checks that no value in a column is below zero.",
            rationale=(
                "Quantities such as market value, notional, prices, or fees cannot be "
                "negative by definition; a negative value usually signals a sign or "
                "booking error."
            ),
            inappropriate_when=(
                "The column can legitimately be negative, such as weights or quantities "
                "of a portfolio with short positions, P&L, or cash balances."
            ),
            parameters=(
                ParameterSpec(
                    name="column",
                    kind=ParameterKind.COLUMN,
                    label="Column",
                    description="Column whose values must not be negative.",
                    required=True,
                ),
                ParameterSpec(
                    name="tolerance",
                    kind=ParameterKind.TOLERANCE,
                    label="Allowed shortfall",
                    description=(
                        "How far below zero a value may be and still pass, for example 0.01 "
                        "to tolerate rounding."
                    ),
                    default="0",
                    allow_relative=False,
                ),
                _NULL_POLICY,
                _SEVERITY,
                ParameterSpec(
                    name="max_violations",
                    kind=ParameterKind.INTEGER,
                    label="Rows listed",
                    description="Maximum number of offending rows listed in the report.",
                    default=20,
                    minimum=0,
                ),
            ),
            factory=non_negative,
        )
    )
    catalog.register(_cash_reconciles_spec())
    catalog.register(_nav_reconciles_spec())
    return catalog


_RECONCILE_NULLS = ParameterSpec(
    name="null_policy",
    kind=ParameterKind.CHOICE,
    label="Blank cells",
    description=(
        "What to do with blank amounts: 'fail' lists the rows as a failure, and 'skip' "
        "records the whole check as not run. Blanks are never treated as zero."
    ),
    default=NullPolicy.FAIL.value,
    choices=(NullPolicy.FAIL.value, NullPolicy.SKIP.value),
)

_GROUP_BY = ParameterSpec(
    name="group_by",
    kind=ParameterKind.COLUMNS,
    label="Reconcile separately for each",
    description=(
        "Columns that identify each account or portfolio, such as a portfolio code "
        "and a date. Leave empty to reconcile the whole file as one."
    ),
)

_CURRENCY = ParameterSpec(
    name="currency",
    kind=ParameterKind.COLUMN,
    label="Currency column",
    description=(
        "Column holding each row's currency, so each currency reconciles separately. "
        "Leave empty only if every group is in one currency; amounts are never converted."
    ),
)


def _amount_column(
    name: str, label: str, description: str, *, required: bool = True
) -> ParameterSpec:
    return ParameterSpec(
        name=name,
        kind=ParameterKind.COLUMN,
        label=label,
        description=description,
        required=required,
    )


def _reconcile_tolerance(description: str) -> ParameterSpec:
    return ParameterSpec(
        name="tolerance",
        kind=ParameterKind.TOLERANCE,
        label="Allowed difference",
        description=description,
        default="0",
    )


_MAX_GROUPS = ParameterSpec(
    name="max_violations",
    kind=ParameterKind.INTEGER,
    label="Groups listed",
    description="Maximum number of failing groups or rows listed in the report.",
    default=20,
    minimum=0,
)


def _cash_reconciles_spec() -> RuleFactorySpec:
    return RuleFactorySpec(
        name="cash_reconciles",
        rule_id="accounting.cash_reconciles",
        title="Cash balances roll forward",
        summary=(
            "Checks that opening cash plus inflows, less outflows, plus any cash P&L, "
            "equals closing cash for each account."
        ),
        rationale=(
            "A cash balance that does not roll forward means a movement is missing, "
            "duplicated, or booked with the wrong sign, or a balance is stale."
        ),
        inappropriate_when=(
            "Movements are recorded in a different currency from the balances, the file "
            "omits some movement types (such as fees or FX), or balances are as of "
            "different dates than the movements."
        ),
        parameters=(
            ParameterSpec(
                name="outflow_sign",
                kind=ParameterKind.CHOICE,
                label="Outflows are recorded as",
                description=(
                    "'positive' if money paid out appears as positive amounts (they are "
                    "subtracted), 'negative' if it appears as negative amounts (they are "
                    "added). There is no default: a wrong guess would hide real breaks."
                ),
                required=True,
                choices=tuple(item.value for item in OutflowSign),
            ),
            _amount_column(
                "opening_cash", "Opening balance", "Column with the balance at the start."
            ),
            _amount_column("inflows", "Inflows", "Column with cash received."),
            _amount_column("outflows", "Outflows", "Column with cash paid out."),
            _amount_column(
                "closing_cash", "Closing balance", "Column with the balance at the end."
            ),
            _amount_column(
                "cash_pnl",
                "Cash income or expense",
                "Optional column with interest, fees, or other cash P&L. Leave empty if none.",
                required=False,
            ),
            _GROUP_BY,
            _CURRENCY,
            ParameterSpec(
                name="grain",
                kind=ParameterKind.CHOICE,
                label="Each row is",
                description=(
                    "'summary': one row per account holds both balances and the total "
                    "flows. 'transactions': each row is a movement carrying the balance "
                    "before and after it, ordered by 'order_by'."
                ),
                default=CashGrain.SUMMARY.value,
                choices=tuple(item.value for item in CashGrain),
            ),
            _amount_column(
                "order_by",
                "Order transactions by",
                "Date or sequence column; needed for 'transactions'. Dates must be ISO "
                "(2026-01-31) or real date cells.",
                required=False,
            ),
            _reconcile_tolerance(
                "How far closing cash may be from the expected balance, in the "
                "currency's units, for example 0.01."
            ),
            _RECONCILE_NULLS,
            _SEVERITY,
            _MAX_GROUPS,
        ),
        factory=cash_reconciles,
    )


def _nav_reconciles_spec() -> RuleFactorySpec:
    return RuleFactorySpec(
        name="nav_reconciles",
        rule_id="accounting.nav_reconciles",
        title="Market values add up to the NAV",
        summary=(
            "Checks that the market values of every line in a portfolio add up to its "
            "reported net asset value (NAV)."
        ),
        rationale=(
            "If holdings do not add up to the NAV, a position is missing or duplicated, a "
            "price is stale, or the NAV was struck on different data."
        ),
        inappropriate_when=(
            "Liabilities, accruals, or cash are not rows in the file, liabilities are "
            "stored as positive numbers, or market values are in local currencies while "
            "the NAV is in the base currency."
        ),
        parameters=(
            _amount_column(
                "market_value",
                "Market value column",
                "Column with each line's signed market value; liabilities and short "
                "positions are negative.",
            ),
            _amount_column(
                "nav",
                "NAV column",
                "Column with the reported NAV, on every row or on some rows of each portfolio.",
            ),
            _GROUP_BY,
            _CURRENCY,
            _reconcile_tolerance(
                "How far the total may be from the NAV, in the currency's units, for example 0.01."
            ),
            _RECONCILE_NULLS,
            _SEVERITY,
            _MAX_GROUPS,
        ),
        factory=nav_reconciles,
    )
