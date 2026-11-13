from decimal import Decimal
from typing import Any

import pytest

import finassert as fa
from finassert.core.models import Outcome
from finassert.loaders import parse_csv
from finassert.rules import ReturnUnit


def only(data: Any, rule: Any) -> fa.ValidationResult:
    return fa.check(data, [rule]).results[0]


# Market value ----------------------------------------------------------------


def holdings() -> dict[str, list[Any]]:
    return {
        "ticker": ["AAA", "BBB", "FUT"],
        "qty": [100, -50, 2],
        "price": [10.5, 20.0, 4500.0],
        "mult": [1, 1, 50],
        "mv": [1050.0, -1000.0, 450000.0],
    }


def test_market_value_passes_with_multiplier_and_shorts() -> None:
    rule = fa.market_value_reconciles(
        quantity="qty", price="price", market_value="mv", multiplier="mult"
    )

    result = only(holdings(), rule)

    assert result.outcome is Outcome.PASSED
    assert result.message == "All 3 position(s) pass the check."
    assert result.metadata["equation"] == "market_value = quantity * price * multiplier"


def test_market_value_failure_names_the_row_and_difference() -> None:
    data = holdings()
    data["mv"][1] = -900.0
    rule = fa.market_value_reconciles(
        quantity="qty", price="price", market_value="mv", multiplier="mult", row_key="ticker"
    )

    result = only(data, rule)

    assert result.outcome is Outcome.FAILED
    assert result.metadata["failed_rows"] == [
        {
            "row": "BBB",
            "reason": "does_not_reconcile",
            "quantity": -50,
            "price": 20.0,
            "multiplier": 1,
            "observed": -900.0,
            "expected": -1000.0,
            "difference": 100.0,
        }
    ]


def test_market_value_without_multiplier_ignores_the_column() -> None:
    rule = fa.market_value_reconciles(quantity="qty", price="price", market_value="mv")

    result = only(holdings(), rule)

    assert result.outcome is Outcome.FAILED
    assert [item["row"] for item in result.metadata["failed_rows"]] == [2]


def test_market_value_is_exact_for_decimals_and_honours_tolerance() -> None:
    data = parse_csv("qty,price,mv\n3,0.333,1.00\n")
    strict = fa.market_value_reconciles(quantity="qty", price="price", market_value="mv")
    loose = fa.market_value_reconciles(
        quantity="qty", price="price", market_value="mv", tolerance=Decimal("0.001")
    )

    assert only(data, strict).outcome is Outcome.FAILED  # 3 * 0.333 = 0.999
    assert only(data, loose).outcome is Outcome.PASSED  # difference is exactly 0.001


def test_market_value_handles_mixed_decimal_and_float_inputs() -> None:
    data = {"qty": [Decimal("2")], "price": [1.5], "mv": [Decimal("3.0")]}
    rule = fa.market_value_reconciles(quantity="qty", price="price", market_value="mv")

    assert only(data, rule).outcome is Outcome.PASSED


def test_market_value_blank_cells_fail_or_skip_and_are_not_zero() -> None:
    data = holdings()
    data["price"][0] = None  # type: ignore[call-overload]
    failing = fa.market_value_reconciles(quantity="qty", price="price", market_value="mv")
    skipping = fa.market_value_reconciles(
        quantity="qty", price="price", market_value="mv", null_policy="skip"
    )

    failed = only(data, failing)

    assert failed.outcome is Outcome.FAILED
    assert failed.metadata["unusable_rows"] == [{"row": 0, "blank": ["price"]}]
    assert only(data, skipping).outcome is Outcome.SKIPPED


def test_market_value_non_numeric_cells_fail_even_when_skipping() -> None:
    data = holdings()
    data["qty"][0] = "ten"  # type: ignore[call-overload]
    rule = fa.market_value_reconciles(
        quantity="qty", price="price", market_value="mv", null_policy="skip"
    )

    result = only(data, rule)

    assert result.outcome is Outcome.FAILED
    assert result.metadata["unusable_rows"] == [{"row": 0, "invalid": ["quantity"]}]


def test_market_value_empty_file_is_skipped() -> None:
    rule = fa.market_value_reconciles(quantity="qty", price="price", market_value="mv")

    assert only({"qty": [], "price": [], "mv": []}, rule).outcome is Outcome.SKIPPED


def test_market_value_missing_column_is_an_error() -> None:
    rule = fa.market_value_reconciles(quantity="qty", price="price", market_value="nope")

    assert only(holdings(), rule).outcome is Outcome.ERROR


@pytest.mark.parametrize(
    "arguments",
    [
        {"price": "qty"},
        {"multiplier": "mv"},
        {"null_policy": "ignore"},
        {"max_violations": -1},
    ],
)
def test_market_value_rejects_invalid_configuration(arguments: dict[str, Any]) -> None:
    named: dict[str, Any] = {"quantity": "qty", "price": "price", "market_value": "mv"}
    named.update(arguments)
    with pytest.raises(ValueError):
        fa.market_value_reconciles(**named)


def test_market_value_failures_are_capped() -> None:
    data = {"qty": [1] * 5, "price": [1] * 5, "mv": [2] * 5}
    rule = fa.market_value_reconciles(
        quantity="qty", price="price", market_value="mv", max_violations=2
    )

    metadata = only(data, rule).metadata

    assert len(metadata["failed_rows"]) == 2
    assert metadata["failed_count"] == 5
    assert metadata["failed_rows_truncated"] is True


# Returns ---------------------------------------------------------------------


def returns(**overrides: Any) -> dict[str, list[Any]]:
    data: dict[str, list[Any]] = {
        "fund": ["X", "Y"],
        "begin": [100.0, 200.0],
        "end": [110.0, 190.0],
        "flows": [0.0, -10.0],
        "ret": [0.10, 0.0],
    }
    data.update(overrides)
    return data


def test_return_reconciles_with_flows() -> None:
    rule = fa.simple_return_reconciles(
        beginning_value="begin",
        ending_value="end",
        net_flows="flows",
        reported_return="ret",
        return_unit="fraction",
    )

    assert only(returns(), rule).outcome is Outcome.PASSED


def test_return_failure_reports_expected_and_difference() -> None:
    rule = fa.simple_return_reconciles(
        beginning_value="begin",
        ending_value="end",
        reported_return="ret",
        return_unit="fraction",
        row_key="fund",
    )

    result = only(returns(), rule)

    failure = result.metadata["failed_rows"][0]
    assert failure["row"] == "Y"
    assert failure["observed"] == 0.0
    assert failure["expected"] == pytest.approx(-0.05)
    assert (
        result.metadata["equation"] == "return = (ending_value - beginning_value) / beginning_value"
    )


def test_return_unit_percent_scales_by_100() -> None:
    rule = fa.simple_return_reconciles(
        beginning_value="begin",
        ending_value="end",
        net_flows="flows",
        reported_return="ret",
        return_unit=ReturnUnit.PERCENT,
    )

    assert only(returns(ret=[10.0, 0.0]), rule).outcome is Outcome.PASSED
    assert only(returns(), rule).outcome is Outcome.FAILED


def test_return_tolerance_is_in_the_reported_unit() -> None:
    data = parse_csv("begin,end,ret\n100,105.00,0.0501\n")

    def run(tolerance: str) -> Outcome:
        rule = fa.simple_return_reconciles(
            beginning_value="begin",
            ending_value="end",
            reported_return="ret",
            return_unit="fraction",
            tolerance=Decimal(tolerance),
        )
        return only(data, rule).outcome

    assert run("0.0001") is Outcome.PASSED  # 0.0501 - 0.05 is exactly 0.0001
    assert run("0.00009") is Outcome.FAILED


def test_zero_beginning_value_fails_instead_of_dividing() -> None:
    rule = fa.simple_return_reconciles(
        beginning_value="begin",
        ending_value="end",
        reported_return="ret",
        return_unit="fraction",
    )

    result = only(returns(begin=[0.0, 200.0], ret=[0.0, -0.05]), rule)

    assert result.outcome is Outcome.FAILED
    assert result.metadata["failed_rows"][0]["reason"] == "zero_beginning_value"


def test_return_unit_has_no_default() -> None:
    with pytest.raises(TypeError):
        fa.simple_return_reconciles(  # type: ignore[call-arg]
            beginning_value="begin", ending_value="end", reported_return="ret"
        )


def test_return_rejects_an_unknown_unit_and_repeated_columns() -> None:
    with pytest.raises(ValueError):
        fa.simple_return_reconciles(
            beginning_value="begin",
            ending_value="end",
            reported_return="ret",
            return_unit="bps",
        )
    with pytest.raises(ValueError, match="different column"):
        fa.simple_return_reconciles(
            beginning_value="begin",
            ending_value="begin",
            reported_return="ret",
            return_unit="fraction",
        )


def test_return_blank_flows_are_not_read_as_zero() -> None:
    rule = fa.simple_return_reconciles(
        beginning_value="begin",
        ending_value="end",
        net_flows="flows",
        reported_return="ret",
        return_unit="fraction",
    )

    result = only(returns(flows=[None, -10.0]), rule)

    assert result.outcome is Outcome.FAILED
    assert result.metadata["unusable_rows"] == [{"row": 0, "blank": ["net_flows"]}]
