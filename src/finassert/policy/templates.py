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


_TEMPLATES = (
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


def policy_templates() -> tuple[PolicyTemplate, ...]:
    """Return the built-in templates, ordered by name."""
    return tuple(sorted(_TEMPLATES, key=lambda template: template.name))


def get_template(name: str) -> PolicyTemplate:
    """Return the built-in template called ``name``."""
    for template in _TEMPLATES:
        if template.name == name:
            return template
    raise KeyError(name)
