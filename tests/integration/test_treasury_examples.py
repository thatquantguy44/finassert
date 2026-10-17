"""The synthetic schedules independently exercise coverage, balances and funding flows."""

import json
import subprocess
import sys
from copy import deepcopy
from decimal import Decimal
from pathlib import Path

import pytest

import finassert as fa
from finassert import web
from finassert.loaders import load_input
from finassert.policy import load_policy, parse_policy_text

EXAMPLES = Path(__file__).resolve().parents[2] / "examples" / "treasury"
CASES = json.loads((EXAMPLES / "failure-cases.json").read_text())


def records(name):
    source = load_input(EXAMPLES / name)
    return source.preview(source.row_count)


def test_cash_and_facility_equations_and_full_scope():
    cash = records("cash-forecast.csv")
    facilities = records("facilities.csv")
    assert len(cash) == len(facilities) == 208
    assert load_policy(EXAMPLES / "policy.yml").check(cash).passed
    for row, facility in zip(cash, facilities, strict=True):
        assert row["closing_cash"] == (
            row["opening_cash"]
            + row["receipts"]
            - row["payments"]
            + row["financing_inflows"]
            - row["financing_outflows"]
            + row["cash_adjustments"]
        )
        assert facility["closing_drawn"] == (
            facility["opening_drawn"] + facility["draws"] - facility["repayments"]
        )
        assert facility["draws"] == row["financing_inflows"]
        assert row["closing_cash"] - row["restricted_cash"] >= row["minimum_buffer"]
    derived = [
        {
            **r,
            "total_in": r["receipts"] + r["financing_inflows"],
            "total_out": r["payments"] + r["financing_outflows"],
        }
        for r in cash
    ]
    rule = fa.cash_reconciles(
        opening_cash="opening_cash",
        closing_cash="closing_cash",
        inflows="total_in",
        outflows="total_out",
        cash_pnl="cash_adjustments",
        outflow_sign="positive",
        group_by=["forecast_as_of", "entity_id", "scenario_id", "period_start"],
        currency="currency",
        row_key="row_id",
    )
    assert fa.check(derived, [rule]).passed
    # Equal-and-opposite weekly breaks cannot disappear through series-level netting.
    derived[0]["closing_cash"] += 1
    derived[1]["closing_cash"] -= 1
    broken = fa.check(derived, [rule]).results[0]
    assert not broken.passed and broken.metadata["failed_group_count"] == 2


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["name"])
def test_failure_recipes(case):
    data = deepcopy(records(case["dataset"]))
    ids = set(case["row_ids"])
    if case["operation"] == "remove":
        data = [r for r in data if r["row_id"] not in ids]
    elif case["operation"] == "duplicate":
        data += [{**r, "row_id": r["row_id"] + "-copy"} for r in data if r["row_id"] in ids]
    else:
        for row in data:
            if row["row_id"] in ids:
                row.update({key: Decimal(value) for key, value in case["values"].items()})
    if "coverage" in case:
        report = load_policy(EXAMPLES / "policy.yml").check(data)
        assert report.results[0].outcome.value == case["coverage"]
        assert report.results[1].outcome.value == case["continuity"]
    if "future_buffer" in case:
        assert any(r["closing_cash"] - r["restricted_cash"] < r["minimum_buffer"] for r in data)
    if "future_capacity" in case:
        assert any(r["closing_drawn"] > r["commitment"] - r["unavailable_amount"] for r in data)


def test_fixtures_regenerate_identically():
    paths = [*EXAMPLES.glob("*.csv"), *EXAMPLES.glob("*.json"), EXAMPLES / "policy.yml"]
    before = {p: p.read_bytes() for p in paths}
    subprocess.run([sys.executable, str(EXAMPLES / "generate.py")], check=True, timeout=30)
    assert before == {p: p.read_bytes() for p in paths}


def test_cli_matches_python_and_exports_html(tmp_path):
    output, html = tmp_path / "report.json", tmp_path / "report.html"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "finassert",
            "check",
            "--config",
            str(EXAMPLES / "policy.yml"),
            "--input",
            str(EXAMPLES / "cash-forecast.csv"),
            "--output",
            str(output),
            "--html",
            str(html),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
    direct = load_policy(EXAMPLES / "policy.yml").check(load_input(EXAMPLES / "cash-forecast.csv"))
    assert json.loads(output.read_text())["report"] == direct.to_dict()
    assert "treasury.cash_continuity" in html.read_text()


def test_web_bridge_preserves_structured_scope_and_digest():
    loaded = json.loads(web.read_policy((EXAMPLES / "policy.yml").read_text(), "policy.yml"))
    assert loaded["ok"]
    assert len(loaded["policy"]["rules"][0]["expected_scope"]) == 16
    evaluated = json.loads(
        web.run(
            (EXAMPLES / "cash-forecast.csv").read_text(),
            "cash-forecast.csv",
            json.dumps(loaded["policy"]),
        )
    )
    assert evaluated["ok"] and evaluated["passed"]
    assert parse_policy_text(evaluated["policy_yaml"], format="yaml").digest == (
        load_policy(EXAMPLES / "policy.yml").digest
    )
