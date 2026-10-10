"""Small, explicit custom-rule adapter."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from finassert.core.models import Outcome, Severity, ValidationResult

RuleEvaluator = Callable[[Any], bool | ValidationResult]


@dataclass(frozen=True, slots=True)
class FunctionRule:
    """Adapt a function returning a boolean or complete result into a rule."""

    rule_id: str
    name: str
    evaluator: RuleEvaluator
    severity: Severity = Severity.ERROR
    failure_message: str = "Custom financial invariant failed."

    def evaluate(self, data: Any) -> ValidationResult:
        """Call the configured evaluator exactly once."""
        evaluated = self.evaluator(data)
        if isinstance(evaluated, ValidationResult):
            return evaluated
        if not isinstance(evaluated, bool):
            raise TypeError("custom rule evaluators must return bool or ValidationResult")
        return ValidationResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            outcome=Outcome.PASSED if evaluated else Outcome.FAILED,
            severity=self.severity,
            message="Custom financial invariant passed." if evaluated else self.failure_message,
        )


def custom_rule(
    rule_id: str,
    name: str,
    evaluator: RuleEvaluator,
    *,
    severity: Severity | str = Severity.ERROR,
    failure_message: str = "Custom financial invariant failed.",
) -> FunctionRule:
    """Create a rule from a small deterministic callable."""
    return FunctionRule(rule_id, name, evaluator, Severity(severity), failure_message)
