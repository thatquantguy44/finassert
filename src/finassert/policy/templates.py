"""Starter policies for common files, each with its assumptions spelled out.

A template is an ordinary version-1 policy. Its assumptions say when the checks
are meaningful, and its adaptation notes say what a user must change. Templates
never encode regulatory or house limits: they only check invariants that hold
by definition for the kind of file they describe.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from finassert.policy.catalog import RuleCatalog
from finassert.policy.io import dump_policy
from finassert.policy.schema import Policy, parse_policy


@dataclass(frozen=True, slots=True)
class PolicyTemplate:
    """A documented starter policy.

    Args:
        name: Identifier used on the command line, such as ``long-only-holdings``.
        title: Short plain-language title.
        summary: One sentence saying which files the template is for.
        adapt: What a user must check or change before relying on it.
        document: The policy document, including a non-empty ``assumptions`` list.
    """

    name: str
    title: str
    summary: str
    adapt: tuple[str, ...]
    document: Mapping[str, Any]

    def policy(self, *, catalog: RuleCatalog | None = None) -> Policy:
        """Return the template as a validated policy."""
        return parse_policy(_thaw(self.document), catalog=catalog)

    def to_yaml(self) -> str:
        """Return the policy as YAML, headed by comments on how to adapt it."""
        notes = "\n".join(f"#   - {line}" for line in self.adapt)
        header = (
            f"# {self.title} (finassert template '{self.name}')\n"
            f"# {self.summary}\n"
            "# Before relying on these checks:\n"
            f"{notes}\n"
            "# Check the assumptions below hold for your file.\n"
        )
        return header + dump_policy(self.policy()).removeprefix("# finassert policy\n")

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible description, including the policy document."""
        return {
            "name": self.name,
            "title": self.title,
            "summary": self.summary,
            "adapt": list(self.adapt),
            "document": _thaw(self.document),
        }


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list | tuple):
        return tuple(_freeze(item) for item in value)
    return value


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value


_TEMPLATES: tuple[PolicyTemplate, ...] = (
    PolicyTemplate(
        name="long-only-holdings",
        title="Long-only holdings file",
        summary="Daily holdings of one long-only portfolio, with cash held as a position.",
        adapt=(
            "Set each 'column' to the header your file uses.",
            "Set the weight 'tolerance' to how your weights are rounded; "
            '"0.0001" allows one basis point.',
        ),
        document=_freeze(
            {
                "version": 1,
                "name": "Long-only holdings",
                "description": "Holdings of a single long-only portfolio.",
                "assumptions": [
                    "The file holds exactly one portfolio.",
                    "Weights are fractions of total portfolio value (0.25, not 25).",
                    "Cash is a position in the file, so weights include it.",
                    "The portfolio holds no short positions and no instruments that can "
                    "have a negative market value, such as swaps or futures.",
                ],
                "rules": [
                    {"rule": "weights_sum_to_one", "column": "weight", "tolerance": "0.0001"},
                    {"rule": "non_negative", "column": "weight"},
                    {"rule": "non_negative", "column": "market_value"},
                ],
            }
        ),
    ),
    PolicyTemplate(
        name="target-allocation",
        title="Target (model) allocation",
        summary="A model portfolio or strategic asset allocation, before it is traded.",
        adapt=(
            "Set 'column' to the header holding the target weights.",
            "Set the 'tolerance' to how the targets are rounded; "
            '"0.0001" allows one basis point.',
        ),
        document=_freeze(
            {
                "version": 1,
                "name": "Target allocation",
                "description": "Target weights of one long-only model portfolio.",
                "assumptions": [
                    "The file holds the targets of exactly one model or mandate.",
                    "Targets are fractions of the whole (0.25, not 25).",
                    "The model is long-only: no target is negative.",
                ],
                "rules": [
                    {
                        "rule": "weights_sum_to_one",
                        "column": "target_weight",
                        "tolerance": "0.0001",
                    },
                    {"rule": "non_negative", "column": "target_weight"},
                ],
            }
        ),
    ),
)


_TEMPLATES += (
    PolicyTemplate(
        name="cash-reconciliation",
        title="Daily cash reconciliation",
        summary="One row per portfolio, currency, and day with balances and total flows.",
        adapt=(
            "Set each column to the header your file uses.",
            "Set 'outflow_sign' to how your file records money paid out.",
            "Set the 'tolerance' in currency units; \"0.01\" allows one cent.",
        ),
        document=_freeze(
            {
                "version": 1,
                "name": "Daily cash reconciliation",
                "description": "Cash balances roll forward for every portfolio and currency.",
                "assumptions": [
                    "Each row covers one portfolio, currency, and day.",
                    "Inflows, outflows, and cash income or expense include every "
                    "movement between the two balances, fees and FX included.",
                    "Opening and closing balances are as of the start and end of the "
                    "same day as the movements.",
                ],
                "rules": [
                    {
                        "rule": "cash_reconciles",
                        "outflow_sign": "positive",
                        "opening_cash": "opening_balance",
                        "inflows": "inflows",
                        "outflows": "outflows",
                        "cash_pnl": "cash_income",
                        "closing_cash": "closing_balance",
                        "group_by": ["portfolio", "date"],
                        "currency": "currency",
                        "tolerance": "0.01",
                    }
                ],
            }
        ),
    ),
    PolicyTemplate(
        name="multi-portfolio-holdings",
        title="Holdings of several portfolios",
        summary="One file of positions for many portfolios, with weights, market values, and NAV.",
        adapt=(
            "Set each column to the header your file uses.",
            "Remove the NAV check if your file has no NAV column, and add a "
            "'non_negative' check on the weight column if your portfolios are long-only.",
            "Set the weight 'tolerance' to how your weights are rounded; "
            '"0.0001" allows one basis point.',
        ),
        document=_freeze(
            {
                "version": 1,
                "name": "Holdings of several portfolios",
                "description": "Each portfolio's weights add up to 1 and its holdings to its NAV.",
                "assumptions": [
                    "Each row is one position of one portfolio, and every position, "
                    "including cash and liabilities, is a row.",
                    "A security appears once per portfolio; several lots of one security "
                    "are combined before this check.",
                    "Weights are fractions of the portfolio's NAV (0.25, not 25).",
                    "Market values and NAV are in each portfolio's base currency, and "
                    "liabilities and short positions have negative market values.",
                    "The NAV is given on every row, or on at least one row, of each portfolio.",
                ],
                "rules": [
                    {
                        "rule": "required_fields",
                        "columns": ["portfolio", "ticker", "weight", "market_value"],
                    },
                    {"rule": "no_duplicates", "columns": ["portfolio", "ticker"]},
                    {
                        "rule": "weights_sum_to_one",
                        "column": "weight",
                        "group_by": ["portfolio"],
                        "tolerance": "0.0001",
                    },
                    {
                        "rule": "nav_reconciles",
                        "market_value": "market_value",
                        "nav": "nav",
                        "group_by": ["portfolio"],
                        "tolerance": "0.01",
                    },
                ],
            }
        ),
    ),
    PolicyTemplate(
        name="nav-reconciliation",
        title="Holdings add up to the NAV",
        summary="Holdings of several funds, each line with a market value and the fund's NAV.",
        adapt=(
            "Set each column to the header your file uses.",
            "Set the 'tolerance' in currency units; \"0.01\" allows one cent.",
        ),
        document=_freeze(
            {
                "version": 1,
                "name": "NAV reconciliation",
                "description": "Holdings of each fund add up to its reported NAV.",
                "assumptions": [
                    "Every asset, liability, accrual, and cash balance is a line in the file.",
                    "Liabilities and short positions have negative market values.",
                    "Market values and the NAV are in each fund's base currency.",
                    "The NAV is given on every line, or on at least one line, of each fund.",
                ],
                "rules": [
                    {
                        "rule": "nav_reconciles",
                        "market_value": "market_value",
                        "nav": "nav",
                        "group_by": ["fund"],
                        "tolerance": "0.01",
                    }
                ],
            }
        ),
    ),
)


_TEMPLATES += (
    PolicyTemplate(
        name="position-valuation",
        title="Position market values",
        summary="One row per position with quantity, price, and market value.",
        adapt=(
            "Set each column to the header your file uses.",
            "Add the 'multiplier' column if your file holds futures or options, and set "
            "'row_key' to a column such as the ticker so the report names each position.",
            "Set the 'tolerance' in the market value's units; \"0.01\" allows one cent.",
        ),
        document=_freeze(
            {
                "version": 1,
                "name": "Position market values",
                "description": "Every market value equals its quantity times its price.",
                "assumptions": [
                    "Each row is one position, with shorts as negative quantities.",
                    "Prices are quoted per unit, not per 100 of par or as a percentage.",
                    "Price and market value are in the same currency.",
                    "The market value excludes accrued interest, or the price includes it.",
                ],
                "rules": [
                    {
                        "rule": "required_fields",
                        "columns": ["quantity", "price", "market_value"],
                    },
                    {
                        "rule": "market_value_reconciles",
                        "quantity": "quantity",
                        "price": "price",
                        "market_value": "market_value",
                        "tolerance": "0.01",
                    },
                ],
            }
        ),
    ),
    PolicyTemplate(
        name="return-reconciliation",
        title="Reported returns",
        summary="One row per portfolio and period with beginning and ending values and a return.",
        adapt=(
            "Set each column to the header your file uses.",
            "Set 'return_unit' to 'percent' if a 5% return is written as 5 rather than 0.05.",
            "Add a 'net_flows' column if money moved in or out during the period, and "
            "read the assumptions: flows are treated as happening at the end of the period.",
            "Set the 'tolerance' in the return's unit; \"0.0001\" allows one basis point "
            "when returns are fractions.",
        ),
        document=_freeze(
            {
                "version": 1,
                "name": "Reported returns",
                "description": "Reported returns follow from beginning and ending values.",
                "assumptions": [
                    "Each row is one portfolio and one period.",
                    "The return is simple (not time-weighted or Modified Dietz), so flows "
                    "are assumed to happen at the end of the period.",
                    "The return is gross of any fees the values do not already reflect.",
                    "Values are in one currency per row.",
                ],
                "rules": [
                    {
                        "rule": "simple_return_reconciles",
                        "beginning_value": "beginning_value",
                        "ending_value": "ending_value",
                        "reported_return": "return",
                        "return_unit": "fraction",
                        "tolerance": "0.0001",
                    }
                ],
            }
        ),
    ),
)


_TEMPLATES += (
    PolicyTemplate(
        name="position-rollforward",
        title="Position quantity roll-forward",
        summary="One row per portfolio and security: opening and closing quantities and trades.",
        adapt=(
            "Set each column to the header your file uses.",
            "Set 'sell_sign' to how your file records quantities sold: 'positive' if sells "
            "are positive numbers, 'negative' if they are negative.",
            "Add an 'adjustments' column for splits, transfers, or corporate actions if "
            "your file has them; without it they show up as breaks.",
            "Set the 'tolerance' in units of the security if quantities are fractional.",
        ),
        document=_freeze(
            {
                "version": 1,
                "name": "Position quantity roll-forward",
                "description": "Every position's quantity rolls from opening to closing.",
                "assumptions": [
                    "Each row is one position of one portfolio over one period, and the "
                    "buys and sells are the totals for that period.",
                    "Opening and closing quantities are as of the start and end of the "
                    "same period as the trades.",
                    "Splits, transfers, and corporate actions are in the adjustments "
                    "column, or the file has none.",
                    "Quantities are in units of the security, not market value.",
                ],
                "rules": [
                    {
                        "rule": "required_fields",
                        "columns": [
                            "portfolio",
                            "ticker",
                            "opening_quantity",
                            "buys",
                            "sells",
                            "closing_quantity",
                        ],
                    },
                    {"rule": "no_duplicates", "columns": ["portfolio", "ticker"]},
                    {
                        "rule": "position_rolls_forward",
                        "sell_sign": "positive",
                        "opening_quantity": "opening_quantity",
                        "buys": "buys",
                        "sells": "sells",
                        "closing_quantity": "closing_quantity",
                        "group_by": ["portfolio", "ticker"],
                    },
                ],
            }
        ),
    ),
)


def policy_templates() -> tuple[PolicyTemplate, ...]:
    """Return the built-in templates, ordered by name."""
    return tuple(sorted(_TEMPLATES, key=lambda template: template.name))


def get_template(name: str) -> PolicyTemplate:
    """Return the built-in template called ``name``."""
    for template in _TEMPLATES:
        if template.name == name:
            return template
    raise KeyError(name)
