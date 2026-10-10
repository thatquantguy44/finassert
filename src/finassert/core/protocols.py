"""Public structural contracts used by the validation engine."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from finassert.core.models import Severity, ValidationResult


@runtime_checkable
class Rule(Protocol):
    """Contract implemented by all validation rules."""

    rule_id: str
    name: str
    severity: Severity

    def evaluate(self, data: Any) -> ValidationResult:
        """Evaluate this rule against ``data``."""


@runtime_checkable
class ColumnSource(Protocol):
    """Minimal tabular interface accepted without an integration dependency."""

    def column(self, name: str) -> tuple[list[Any], list[Any]]:
        """Return values and corresponding row labels for ``name``."""
