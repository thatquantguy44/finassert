from dataclasses import dataclass
from typing import Any

import pytest

import finassert as fa
from finassert.core.exceptions import RuleEvaluationError
from finassert.core.models import Outcome, Severity, ValidationResult


def test_multiple_rules_preserve_order_and_aggregate() -> None:
    report = fa.check(
        {"weight": [0.4, 0.6], "market_value": [10, -2]},
        rules=[fa.weights_sum_to_one(), fa.non_negative(column="market_value")],
    )

    assert not report.passed
    assert [result.rule_id for result in report.results] == [
        "portfolio.weights_sum_to_one",
        "arithmetic.non_negative",
    ]
    assert report.counts_by_outcome == {"passed": 1, "failed": 1, "error": 0, "skipped": 0}
    assert "finassert FAIL" in report.summary()


def test_empty_rule_set_passes_vacuously() -> None:
    report = fa.check({}, rules=[])

    assert report.passed
    assert report.results == ()


@dataclass
class ExplodingRule:
    rule_id: str = "test.explodes"
    name: str = "Exploding rule"
    severity: Severity = Severity.ERROR

    def evaluate(self, data: Any) -> ValidationResult:
        raise RuntimeError("boom")


def test_evaluation_exception_becomes_error_result() -> None:
    report = fa.check({}, [ExplodingRule()])

    assert report.results[0].outcome is Outcome.ERROR
    assert report.results[0].metadata == {"exception_type": "RuntimeError"}
    assert not report.passed


def test_strict_mode_propagates_as_library_exception() -> None:
    with pytest.raises(RuleEvaluationError, match=r"test\.explodes"):
        fa.check({}, [ExplodingRule()], raise_on_error=True)


def test_structured_serialization_is_json_compatible() -> None:
    report = fa.check({"weight": [0.5, 0.5]}, [fa.weights_sum_to_one()])

    serialized = report.to_dict()
    assert serialized["passed"] is True
    assert serialized["results"][0]["passed"] is True
    assert serialized["results"][0]["outcome"] == "passed"


def test_custom_rule_boolean_behavior() -> None:
    rule = fa.custom_rule("custom.has_rows", "Has rows", lambda data: bool(data["values"]))

    assert fa.check({"values": [1]}, [rule]).passed
    assert not fa.check({"values": []}, [rule]).passed
