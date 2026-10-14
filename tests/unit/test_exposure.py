from decimal import Decimal
from typing import Any

import pytest

import finassert as fa
from finassert.core.models import Outcome
from finassert.loaders import parse_csv


def only(data: Any, rule: Any) -> fa.ValidationResult:
    return fa.check(data, [rule]).results[0]


def book(**overrides: Any) -> dict[str, list[Any]]:
    data: dict[str, list[Any]] = {
        "portfolio": ["A", "A", "A", "B", "B"],
        "weight": [0.8, 0.5, -0.3, 0.6, 0.4],
        "mv": [800, 500, -300, 600, 400],
        "nav": [1000, 1000, 1000, 1000, 1000],
    }
    data.update(overrides)
    return data


# Gross and net exposure ------------------------------------------------------


def test_gross_exposure_counts_shorts_and_reports_the_ratio() -> None:
    rule = fa.gross_within_limit(value="weight", maximum=1.5, group_by=["portfolio"])

    result = only(book(), rule)

    assert result.outcome is Outcome.FAILED
    assert result.message == "1 of 2 group(s) are outside the limit."
    failure = result.metadata["failed_groups"][0]
    assert failure["group"] == {"portfolio": "A"}
    assert failure["reason"] == "above_maximum"
    assert failure["observed"] == pytest.approx(1.6)
    assert failure["maximum"] == 1.5


def test_net_exposure_lets_shorts_offset_longs() -> None:
    rule = fa.net_within_limit(value="weight", maximum=1.2, group_by=["portfolio"])

    assert only(book(), rule).outcome is Outcome.PASSED


def test_exposure_at_the_limit_passes() -> None:
    data = parse_csv("portfolio,mv,nav\nA,60.10,100\nA,-39.90,100\n")
    rule = fa.gross_within_limit(
        value="mv", base="nav", maximum=Decimal("1.0"), group_by=["portfolio"]
    )

    assert only(data, rule).outcome is Outcome.PASSED


def test_exposure_just_over_the_limit_fails() -> None:
    data = parse_csv("portfolio,mv,nav\nA,60.11,100\nA,-39.90,100\n")
    rule = fa.gross_within_limit(
        value="mv", base="nav", maximum=Decimal("1.0"), group_by=["portfolio"]
    )

    assert only(data, rule).outcome is Outcome.FAILED


def test_base_column_divides_exposure_by_nav() -> None:
    rule = fa.gross_within_limit(value="mv", base="nav", maximum=1.5, group_by=["portfolio"])

    failure = only(book(), rule).metadata["failed_groups"][0]

    assert failure["group"] == {"portfolio": "A"}
    assert failure["observed"] == pytest.approx(1.6)


def test_minimum_limit_catches_underinvestment() -> None:
    rule = fa.net_within_limit(value="weight", minimum=0.95, group_by=["portfolio"])

    result = only(book(weight=[0.5, 0.2, 0.1, 0.6, 0.4]), rule)

    assert result.metadata["failed_groups"][0]["reason"] == "below_minimum"
    assert result.metadata["failed_groups"][0]["group"] == {"portfolio": "A"}


def test_negative_net_limits_are_allowed_for_short_books() -> None:
    rule = fa.net_within_limit(value="weight", maximum=-0.1)
    data = {"weight": [-0.6, 0.4]}

    assert only(data, rule).outcome is Outcome.PASSED
    assert only({"weight": [-0.2, 0.15]}, rule).outcome is Outcome.FAILED


def test_zero_or_negative_base_fails_instead_of_dividing() -> None:
    rule = fa.gross_within_limit(value="mv", base="nav", maximum=2, group_by=["portfolio"])

    result = only(book(nav=[0, 0, 0, -5, -5]), rule)

    assert {item["reason"] for item in result.metadata["failed_groups"]} == {"base_not_positive"}


def test_missing_base_in_a_group_fails() -> None:
    rule = fa.gross_within_limit(value="mv", base="nav", maximum=2, group_by=["portfolio"])

    result = only(book(nav=[None, None, None, 1000, 1000]), rule)

    assert result.metadata["failed_groups"][0]["reason"] == "no_base"


def test_conflicting_bases_in_a_group_fail() -> None:
    rule = fa.gross_within_limit(value="mv", base="nav", maximum=2, group_by=["portfolio"])

    result = only(book(nav=[1000, 900, 1000, 1000, 1000]), rule)

    assert result.metadata["failed_groups"][0]["reason"] == "inconsistent_rows"


def test_currencies_are_checked_separately() -> None:
    rule = fa.gross_within_limit(
        value="weight", maximum=1.0, group_by=["portfolio"], currency="ccy"
    )
    data = {
        "portfolio": ["A", "A"],
        "ccy": ["USD", "EUR"],
        "weight": [0.9, 0.9],
    }

    result = only(data, rule)

    assert result.outcome is Outcome.PASSED
    assert result.metadata["currency"] == "checked separately for each value of 'ccy'"


def test_blank_value_fails_or_skips_and_is_never_zero() -> None:
    data = book(weight=[0.8, None, -0.3, 0.6, 0.4])

    failed = only(data, fa.gross_within_limit(value="weight", maximum=9))
    skipped = only(data, fa.gross_within_limit(value="weight", maximum=9, null_policy="skip"))

    assert failed.outcome is Outcome.FAILED
    assert skipped.outcome is Outcome.SKIPPED


def test_non_numeric_value_fails_even_when_skipping() -> None:
    data = book(weight=[0.8, "abc", -0.3, 0.6, 0.4])

    result = only(data, fa.gross_within_limit(value="weight", maximum=9, null_policy="skip"))

    assert result.outcome is Outcome.FAILED


def test_empty_file_is_skipped() -> None:
    assert only({"weight": []}, fa.gross_within_limit(value="weight", maximum=1)).outcome is (
        Outcome.SKIPPED
    )


@pytest.mark.parametrize(
    "arguments",
    [
        {},
        {"minimum": 2, "maximum": 1},
        {"maximum": float("inf")},
        {"maximum": 1, "null_policy": "ignore"},
        {"maximum": 1, "max_violations": -1},
    ],
)
def test_invalid_exposure_configuration_is_rejected(arguments: dict[str, Any]) -> None:
    with pytest.raises(ValueError):
        fa.gross_within_limit(value="weight", **arguments)


def test_group_by_must_be_a_list() -> None:
    with pytest.raises(TypeError):
        fa.gross_within_limit(value="weight", maximum=1, group_by="portfolio")  # type: ignore[arg-type]


# Single-position limits ------------------------------------------------------


def test_position_limit_lists_each_breach_with_its_size() -> None:
    rule = fa.position_within_limit(value="weight", maximum=0.7, group_by=["portfolio"])

    result = only(book(), rule)

    assert result.outcome is Outcome.FAILED
    failure = result.metadata["failed_groups"][0]
    assert failure["group"] == {"portfolio": "A"}
    assert failure["reason"] == "position_above_limit"
    assert failure["breach_count"] == 1
    assert failure["breaches"] == [{"row": 0, "value": 0.8, "size": 0.8}]
    assert result.message == "1 of 2 group(s) have a position above the limit."


def test_position_limit_counts_short_positions_by_absolute_size() -> None:
    rule = fa.position_within_limit(value="weight", maximum=0.25)

    result = only({"weight": [0.2, -0.3]}, rule)

    assert result.metadata["failed_groups"][0]["breaches"][0]["value"] == -0.3


def test_position_limit_uses_the_base_and_row_labels() -> None:
    rule = fa.position_within_limit(
        value="mv", base="nav", maximum=0.5, group_by=["portfolio"], row_key="ticker"
    )
    data = book(ticker=["AAA", "BBB", "CCC", "DDD", "EEE"])

    breaches = only(data, rule).metadata["failed_groups"][0]["breaches"]

    assert breaches == [{"row": "AAA", "value": 800, "size": pytest.approx(0.8)}]


def test_position_exactly_at_the_limit_passes() -> None:
    rule = fa.position_within_limit(value="weight", maximum=Decimal("0.4"))
    data = parse_csv("weight\n0.40\n-0.40\n0.2\n")

    assert only(data, rule).outcome is Outcome.PASSED


def test_position_limit_rejects_a_negative_limit() -> None:
    with pytest.raises(ValueError, match="cannot be negative"):
        fa.position_within_limit(value="weight", maximum=-0.1)
