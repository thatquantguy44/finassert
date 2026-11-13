"""Ordinary policies and identical canonical findings across local interfaces."""

import importlib.util
import json
import subprocess
import sys
from copy import deepcopy
from decimal import Decimal
from pathlib import Path

import anyio
import pytest
from openpyxl import load_workbook

from finassert.assistant import Workspace, check_data, list_templates
from finassert.loaders import load_input
from finassert.policy import (
    default_catalog,
    fit_template,
    get_template,
    load_policy,
    policy_packs,
    treasury_pack_manifest,
)

EXAMPLES = Path(__file__).resolve().parents[2] / "examples" / "treasury"


@pytest.mark.parametrize(
    "dataset,policy_name",
    [("cash-forecast.csv", "cash-pack.yml"), ("facilities.csv", "facility-pack.yml")],
)
@pytest.mark.parametrize("broken", [False, True])
def test_python_cli_mcp_summary_and_reports_preserve_financial_truth(
    tmp_path, dataset, policy_name, broken
):
    source = load_input(EXAMPLES / dataset)
    rows = source.preview(source.row_count)
    if broken:
        rows[0]["minimum_buffer" if dataset.startswith("cash") else "commitment"] = (
            Decimal("999999") if dataset.startswith("cash") else 0
        )
    import csv

    data = tmp_path / "data.csv"
    with data.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)
    policy = load_policy(EXAMPLES / policy_name)
    report = policy.check(load_input(data))
    expected = report.to_dict()
    output, html, xlsx = (tmp_path / name for name in ("report.json", "report.html", "report.xlsx"))
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "finassert",
            "check",
            "--config",
            str(EXAMPLES / policy_name),
            "--input",
            str(data),
            "--output",
            str(output),
            "--html",
            str(html),
            "--xlsx",
            str(xlsx),
        ],
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert result.returncode == (1 if broken else 0), result.stderr
    assert json.loads(output.read_text())["report"] == expected
    mcp = check_data(
        Workspace([tmp_path, EXAMPLES]), str(data), policy_path=str(EXAMPLES / policy_name)
    )
    assert mcp["exit_code"] == result.returncode
    assert mcp["counts"] == expected["counts_by_outcome"]
    assert mcp["policy"]["digest"] == policy.digest
    for summary, canonical in zip(mcp["results"], expected["results"], strict=True):
        for key in (
            "rule_id",
            "outcome",
            "severity",
            "observed",
            "expected",
            "tolerance",
            "diagnostics",
        ):
            assert summary[key] == canonical[key]
    assert expected["results"][-1]["rule_id"] in html.read_text()
    book = load_workbook(xlsx)
    assert [r[2] for r in list(book["Results"].values)[1:]] == [
        r["outcome"] for r in expected["results"]
    ]
    assert book["Diagnostics"].max_row > (1 if broken or dataset == "facilities.csv" else 0)
    book.close()


def test_pack_manifest_is_detached_and_agrees_with_templates_catalog_and_fixture():
    manifest = treasury_pack_manifest()
    assert json.loads((EXAMPLES / "pack-manifest.json").read_text()) == manifest
    catalog_ids = {spec.rule_id for spec in default_catalog().specs()}
    for dataset in manifest["datasets"].values():
        policy = get_template(dataset["template"]).policy()
        ids = {rule.rule_id for rule in policy.rules}
        assert set(dataset["required_rules"]) == ids
        assert ids <= catalog_ids
    assert policy_packs() == (manifest,)
    assert list_templates()["packs"] == [manifest]
    manifest["datasets"].clear()
    assert treasury_pack_manifest()["datasets"]


def test_treasury_template_renaming_preserves_scope_values():
    template = get_template("treasury-facility-schedule")
    from finassert.policy.suggest import expected_columns

    columns = expected_columns(template.to_dict()["document"])
    headers = [column.replace("_", " ").title() for column in columns]
    fit = fit_template(template, headers)
    assert fit.fraction == 1
    adapted = fit.adapted().policy()
    original_scope = template.to_dict()["document"]["rules"][-1]["expected_scope"][0]
    scope = adapted.to_document()["rules"][-1]["expected_scope"][0]
    assert set(scope.values()) == set(original_scope.values())
    assert set(scope) == {key.replace("_", " ").title() for key in original_scope}


def test_explicit_preparation_is_exact_non_mutating_and_refuses_missing_values():
    spec = importlib.util.spec_from_file_location("treasury_prepare", EXAMPLES / "prepare.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    rows = [
        {
            "row_id": "original",
            "receipts": Decimal("1e40"),
            "financing_inflows": Decimal("0.01"),
            "payments": Decimal("1.25"),
            "financing_outflows": Decimal("0.75"),
        }
    ]
    before = deepcopy(rows)
    prepared = module.prepare_cash_rows(rows)
    assert prepared[0]["total_inflows"] == Decimal("10000000000000000000000000000000000000000.01")
    assert prepared[0]["total_outflows"] == Decimal("2.00")
    assert prepared[0]["row_id"] == "original"
    assert rows == before
    for value in (None, True, "1", Decimal("NaN"), -1):
        with pytest.raises(ValueError):
            module.prepare_cash_rows([{**rows[0], "receipts": value}])


def test_cli_discovers_the_same_versioned_pack():
    result = subprocess.run(
        [sys.executable, "-m", "finassert", "templates", "--json"],
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["packs"] == list(policy_packs())
    assert {item["name"] for item in payload["templates"]} >= {
        "treasury-cash-forecast",
        "treasury-facility-schedule",
    }


def test_treasury_pack_over_real_mcp_stdio():
    from mcp import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    params = StdioServerParameters(
        env={"PYTHONPATH": str(EXAMPLES.parents[1] / "src")},
        command=sys.executable,
        args=["-c", f'from finassert.assistant import main; main(["--root", {str(EXAMPLES)!r}])'],
    )

    async def session():
        async with stdio_client(params) as (read, write), ClientSession(read, write) as client:
            await client.initialize()
            result = await client.call_tool(
                "run_checks", {"path": "facilities.csv", "policy_path": "facility-pack.yml"}
            )
            assert not result.is_error
            payload = result.structured_content or json.loads(result.content[0].text)
            assert payload["status"] == "passed"
            facility = payload["results"][-1]
            assert facility["rule_id"] == "treasury.facility_capacity"
            assert facility["diagnostics"][0]["count"] == 208

    anyio.run(session)
