from decimal import Decimal

import pytest

import finassert as fa
from finassert.adapters import ColumnMapping, FieldAggregation
from finassert.core.exceptions import GroupAggregationError
from finassert.rules.grouped import aggregate_values


@pytest.mark.parametrize(
    ("aggregation", "expected"),
    [
        (FieldAggregation.SUM, Decimal("6.0")),
        (FieldAggregation.FIRST, Decimal("1.0")),
        (FieldAggregation.LAST, Decimal("3.0")),
    ],
)
def test_group_aggregations_preserve_order_and_decimal(
    aggregation: FieldAggregation,
    expected: Decimal,
) -> None:
    values = [Decimal("1.0"), Decimal("2.0"), Decimal("3.0")]

    assert aggregate_values(values, aggregation) == expected


def test_require_unique_returns_repeated_value() -> None:
    assert aggregate_values(
        [Decimal("10.00"), Decimal("10.00")], FieldAggregation.REQUIRE_UNIQUE
    ) == Decimal("10.00")


def test_require_unique_rejects_distinct_values() -> None:
    with pytest.raises(GroupAggregationError, match="distinct"):
        aggregate_values([100, 101], FieldAggregation.REQUIRE_UNIQUE)


@pytest.mark.parametrize("values", [[], [float("nan")], [float("inf")], [True]])
def test_group_aggregation_rejects_empty_or_non_finite_values(values: list[object]) -> None:
    with pytest.raises(fa.GroupAggregationError):
        aggregate_values(values, FieldAggregation.SUM)  # type: ignore[arg-type]


def test_grouped_rule_protocol_is_structural() -> None:
    class ExampleGroupedRule:
        rule_id = "example.grouped"
        name = "Example grouped rule"
        severity = fa.Severity.ERROR
        mapping = ColumnMapping(
            {"value": "market_value"},
            aggregations={"value": FieldAggregation.SUM},
        )
        required_semantics = ("value",)

        def evaluate(self, data: object) -> fa.ValidationResult:
            return fa.ValidationResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                outcome=fa.Outcome.PASSED,
                severity=self.severity,
                message="passed",
            )

    assert isinstance(ExampleGroupedRule(), fa.GroupedRule)
