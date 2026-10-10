"""Deterministic rule execution."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from finassert.core.exceptions import RuleEvaluationError
from finassert.core.models import Outcome, ValidationReport, ValidationResult
from finassert.core.protocols import Rule


def check(data: Any, rules: Iterable[Rule], *, raise_on_error: bool = False) -> ValidationReport:
    """Evaluate rules in the supplied order and return an immutable report.

    Args:
        data: Dataset understood by the configured rules.
        rules: Rules to evaluate. Iteration order is preserved.
        raise_on_error: Raise :class:`RuleEvaluationError` instead of recording
            an ``error`` outcome when a rule raises unexpectedly.
    """
    results: list[ValidationResult] = []
    for rule in rules:
        try:
            result = rule.evaluate(data)
            if result.rule_id != rule.rule_id:
                raise ValueError("rule returned a result with a different rule_id")
            results.append(result)
        except Exception as exc:
            if raise_on_error:
                raise RuleEvaluationError(f"Rule {rule.rule_id!r} could not be evaluated") from exc
            results.append(
                ValidationResult(
                    rule_id=rule.rule_id,
                    rule_name=rule.name,
                    outcome=Outcome.ERROR,
                    severity=rule.severity,
                    message=f"Evaluation error: {type(exc).__name__}: {exc}",
                    metadata={"exception_type": type(exc).__name__},
                )
            )
    return ValidationReport(tuple(results))
