"""Allowlisted rule factories with plain-language descriptions."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from finassert.core.models import Severity
from finassert.rules import NullPolicy, non_negative, weights_sum_to_one


class ParameterKind(StrEnum):
    """How a policy parameter is written and validated."""

    COLUMN = "column"
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
    return catalog
