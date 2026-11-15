"""Freshness regressions against the actual pane and Python engine."""

from __future__ import annotations

import json
import os
import re
from typing import Any

import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get("FINASSERT_EXCEL_PAGE"), reason="requires the bundled Excel browser job"
)


def current_export_available(page: Any) -> bool:
    """A historical result may stay visible, but current evidence must be gated."""
    return page.locator("#excel-write").is_visible() and page.locator("#excel-write").is_enabled()


def change_market_value(page: Any) -> None:
    # D4 changes in the worksheet; the pane holds an older copy.
    page.evaluate("window.__excel.sheets.Holdings.cells[3][3] = -1")


def test_explicit_reread_and_rerun_find_the_changed_cell(pane):
    """Positive control: the financial engine detects the seeded failure."""
    from playwright.sync_api import expect

    change_market_value(pane)
    pane.click("#excel-read")
    pane.click("#run")
    expect(pane.locator("#result-banner")).to_contain_text("✗ Failed")
    report = pane.evaluate("JSON.parse(window.finassertApp.result().artifact_json).report")
    failures = [r for r in report["results"] if r["rule_id"] == "arithmetic.non_negative"]
    assert report["passed"] is False
    assert failures[-1]["metadata"]["violations"] == [{"row": 4, "value": -1}]


def test_run_reads_current_workbook_values(pane):
    from playwright.sync_api import expect

    change_market_value(pane)
    pane.click("#run")
    expect(pane.locator("#result-banner")).to_contain_text("✗ Failed")
    assert pane.evaluate("window.finassertApp.result().passed") is False


def test_rereading_changed_source_invalidates_current_export(pane):
    change_market_value(pane)
    pane.click("#excel-read")
    assert not current_export_available(pane)


def test_editing_tolerance_invalidates_current_export(pane):
    pane.locator(".check").first.locator("input[inputmode='decimal']").first.fill("0.01")
    assert not current_export_available(pane)


def test_invalid_run_hides_current_report(pane):
    """Existing visible failure behavior is retained as a positive control."""
    from playwright.sync_api import expect

    pane.select_option("#add-check", "in_range")
    pane.click("#add-check-button")
    pane.click("#run")
    assert not current_export_available(pane)
    expect(pane.locator("#policy-issues")).to_be_visible()


def run_host_probe(page: Any) -> dict[str, Any]:
    from playwright.sync_api import expect

    if not page.locator("#excel-date-system").input_value():
        page.select_option("#excel-date-system", "1900")
    page.locator("#excel-spike summary").click()
    page.locator("#spike-portfolios").fill("10")
    page.locator("#spike-run").click()
    report = page.locator("#spike-report")
    expect(report).to_have_value(re.compile(r"(All steps passed|step\(s\) FAILED)"), timeout=30000)
    return json.loads(report.input_value().splitlines()[-1])


@pytest.mark.parametrize(
    "pane",
    [
        {"startUnbound": True, "calculationMode": "Automatic", "calculationState": "Done"},
        {"startUnbound": True, "calculationMode": "Manual", "calculationState": "Pending"},
        {"startUnbound": True, "calculationMode": "Automatic", "calculationState": "Calculating"},
    ],
    indirect=True,
)
def test_host_probe_records_calculation_and_events_without_changing_settings(pane):
    before = pane.evaluate("JSON.stringify(window.__excel.application)")
    captured = run_host_probe(pane)
    baseline = captured["environment"]["workflowBaseline"]
    application = json.loads(before)
    assert baseline["calculationMode"] == application["calculationMode"]
    assert baseline["calculationState"] == application["calculationState"]
    assert all(baseline["worksheetEvents"].values())
    assert "not detected" in baseline["dateSystem"]
    assert pane.evaluate("JSON.stringify(window.__excel.application)") == before


@pytest.mark.parametrize(
    "pane", [{"startUnbound": True, "requirements": {"1.9": False}}], indirect=True
)
def test_unsupported_planned_api_floor_is_reported_without_reading_it(pane):
    captured = run_host_probe(pane)
    step = next(s for s in captured["steps"] if s["name"] == "planned workflow API baseline")
    assert step["status"] == "FAIL"
    assert "workflowBaseline" not in captured["environment"]
    assert "read calculation metadata" not in pane.evaluate("window.__excel.log")
