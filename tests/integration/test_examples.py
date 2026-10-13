"""The sample files in examples/ must keep showing exactly the break they describe."""

from decimal import Decimal
from pathlib import Path

import pytest

from finassert.loaders import load_input
from finassert.policy import get_template, load_policy

EXAMPLES = Path(__file__).resolve().parents[2] / "examples"


def outcomes(report: object) -> dict[str, str]:
    return {result.rule_id: result.outcome.value for result in report.results}  # type: ignore[attr-defined]


def test_positions_example_with_its_policy() -> None:
    report = load_policy(EXAMPLES / "policy.yml").check(load_input(EXAMPLES / "positions.csv"))
    assert outcomes(report) == {
        "portfolio.weights_sum_to_one": "passed",
        "arithmetic.non_negative": "failed",
    }
    assert report.results[1].metadata["violations"] == [{"row": 5, "value": -1500000}]


def test_cash_example_breaks_only_alpha_eur() -> None:
    report = get_template("cash-reconciliation").policy().check(load_input(EXAMPLES / "cash.csv"))
    (result,) = report.results
    assert result.outcome.value == "failed"
    (failure,) = result.metadata["failed_groups"]
    assert failure["group"] == {"portfolio": "Alpha", "date": "2026-01-02", "currency": "EUR"}
    assert failure["observed"] == 450000 and failure["expected"] == 455000
    assert failure["rows"] == [3]


def test_holdings_example_breaks_only_betas_weights() -> None:
    policy = get_template("multi-portfolio-holdings").policy()
    report = policy.check(load_input(EXAMPLES / "holdings.csv"))
    assert outcomes(report) == {
        "data.required_fields": "passed",
        "data.no_duplicates": "passed",
        "portfolio.weights_sum_to_one": "failed",
        "accounting.nav_reconciles": "passed",
    }
    (failure,) = report.results[2].metadata["failed_groups"]
    assert failure["group"] == {"portfolio": "Beta"}


@pytest.mark.parametrize(
    ("edit", "rule_id"),
    [
        ("Alpha,MSFT,0.40,400000.00,1000000.00\n", "data.no_duplicates"),
        ("Beta,,0.20,0.00,1000000.00\n", "data.required_fields"),
    ],
)
def test_holdings_example_catches_a_pasted_row_and_a_blank_ticker(edit: str, rule_id: str) -> None:
    text = (EXAMPLES / "holdings.csv").read_text(encoding="utf-8") + edit
    from finassert.loaders import parse_csv

    report = get_template("multi-portfolio-holdings").policy().check(parse_csv(text))
    assert outcomes(report)[rule_id] == "failed"


def test_valuation_example_breaks_only_the_stale_tsla_price() -> None:
    policy = get_template("position-valuation").policy()
    report = policy.check(load_input(EXAMPLES / "valuation.csv"))
    assert outcomes(report) == {
        "data.required_fields": "passed",
        "accounting.market_value_reconciles": "failed",
    }
    (failure,) = report.results[1].metadata["failed_rows"]
    assert failure["row"] == 5
    assert failure["observed"] == 72000 and failure["expected"] == 72030


def test_returns_example_breaks_only_betas_return() -> None:
    report = (
        get_template("return-reconciliation").policy().check(load_input(EXAMPLES / "returns.csv"))
    )
    (result,) = report.results
    assert result.outcome.value == "failed"
    (failure,) = result.metadata["failed_rows"]
    assert failure["row"] == 3
    assert failure["observed"] == Decimal("0.035")
    assert failure["expected"] == Decimal("0.03")


def test_limits_example_breaks_only_betas_jnj_position() -> None:
    report = load_policy(EXAMPLES / "limits-policy.yml").check(
        load_input(EXAMPLES / "holdings.csv")
    )
    assert outcomes(report) == {
        "exposure.gross_within_limit": "passed",
        "exposure.net_within_limit": "passed",
        "exposure.position_within_limit": "failed",
    }
    (failure,) = report.results[2].metadata["failed_groups"]
    assert failure["group"] == {"portfolio": "Beta"}
    assert [item["row"] for item in failure["breaches"]] == ["JNJ"]
