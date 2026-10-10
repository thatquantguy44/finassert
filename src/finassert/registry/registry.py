"""Collision-safe in-process rule registry."""

from __future__ import annotations

from finassert.core.protocols import Rule


class RuleRegistry:
    """Store rule instances by stable identifier.

    The registry is intentionally explicit: duplicate identifiers fail unless
    the caller opts into replacement.
    """

    def __init__(self) -> None:
        self._rules: dict[str, Rule] = {}

    def register(self, rule: Rule, *, replace: bool = False) -> None:
        """Register ``rule`` or raise on an identifier collision."""
        if rule.rule_id in self._rules and not replace:
            raise ValueError(f"rule_id {rule.rule_id!r} is already registered")
        self._rules[rule.rule_id] = rule

    def get(self, rule_id: str) -> Rule:
        """Return a registered rule."""
        return self._rules[rule_id]

    def ids(self) -> tuple[str, ...]:
        """Return stable identifiers in sorted order."""
        return tuple(sorted(self._rules))
