"""E-01 reproductions against the real pane/engine and the Office stand-in.

Run explicitly in the browser job with FINASSERT_EXCEL_PAGE pointing to a built,
bundled add-in. Strict xfails track #23; E-03 must replace them when implemented.
"""

from __future__ import annotations

import json
import os
import re
import sys
import threading
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import pytest

ROOT = Path(__file__).resolve().parents[2]
PAGE = os.environ.get("FINASSERT_EXCEL_PAGE")
pytestmark = pytest.mark.skipif(
    not PAGE, reason="run explicitly with the bundled Excel browser job"
)

VALUES = [
    ["portfolio", "ticker", "weight", "market_value", "nav"],
    ["Alpha", "AAA", 0.4, 400, 1000],
    ["Alpha", "BBB", 0.6, 600, 1000],
]
ISSUE = "https://github.com/thatquantguy44/finassert/issues/23"


@pytest.fixture(scope="module")
def served_page():
    """Serve the supplied bundle on loopback, without fetching any runtime files."""
    if not PAGE:
        pytest.skip("FINASSERT_EXCEL_PAGE is required")
    path = Path(PAGE).resolve()
    if not path.is_file() or not (path.parent / "pyodide" / "pyodide.js").is_file():
        raise RuntimeError("FINASSERT_EXCEL_PAGE must name a built bundled-runtime add-in")
    sys.path.insert(0, str(ROOT / "scripts"))
    from serve_excel import make_server

    server = make_server(path.parent, port=0, quiet=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}/{path.name}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.fixture
def pane(served_page, request):
    from playwright.sync_api import expect, sync_playwright

    config = {"values": VALUES, "selected": "range", "table": True, **getattr(request, "param", {})}
    stub = (
        (ROOT / "scripts" / "excel_stub.js").read_text().replace("__CONFIG__", json.dumps(config))
    )
    origin = urlsplit(served_page).netloc
    unexpected = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context()
        page = context.new_page()

        def route(request_route):
            url = request_route.request.url
            if url == "https://appsforoffice.microsoft.com/lib/1/hosted/office.js":
                request_route.fulfill(body=stub, content_type="application/javascript")
            elif urlsplit(url).netloc == origin:
                request_route.continue_()
            else:
                unexpected.append(url)
                request_route.abort()

        page.route("**/*", route)
        page.goto(served_page)
        expect(page.locator("#status")).to_have_text(re.compile(r"^Ready\."), timeout=120000)
        page.click("#excel-read")
        page.select_option("#template", "long-only-holdings")
        page.click("#run")
        if not page.evaluate("window.finassertApp.result()?.passed === true"):
            raise RuntimeError("the untouched passing fixture must pass before testing freshness")
        try:
            yield page
        finally:
            browser.close()
    if unexpected:
        raise RuntimeError(f"bundled regression attempted unexpected network access: {unexpected}")


def current_export_available(page: Any) -> bool:
    """A historical result may stay visible, but current evidence must be gated."""
    return page.locator("#excel-write").is_visible() and page.locator("#excel-write").is_enabled()


def change_market_value(page: Any) -> None:
    # D4 changes in the worksheet; the pane holds an older copy.
    page.evaluate("window.__excel.sheets.Holdings.cells[3][3] = -1")


def test_explicit_reread_and_rerun_find_the_changed_cell(pane):
    """Positive control: the financial engine detects the seeded failure."""
    change_market_value(pane)
    pane.click("#excel-read")
    pane.click("#run")
    report = pane.evaluate("JSON.parse(window.finassertApp.result().artifact_json).report")
    failures = [r for r in report["results"] if r["rule_id"] == "arithmetic.non_negative"]
    assert report["passed"] is False
    assert failures[-1]["metadata"]["violations"] == [{"row": 4, "value": -1}]


@pytest.mark.xfail(strict=True, raises=AssertionError, reason=f"{ISSUE}: E-03 must reread on Run")
def test_run_reads_current_workbook_values(pane):
    change_market_value(pane)
    pane.click("#run")
    assert pane.evaluate("window.finassertApp.result().passed") is False


@pytest.mark.xfail(
    strict=True, raises=AssertionError, reason=f"{ISSUE}: source reread leaves old export"
)
def test_rereading_changed_source_invalidates_current_export(pane):
    change_market_value(pane)
    pane.click("#excel-read")
    assert not current_export_available(pane)


@pytest.mark.xfail(
    strict=True, raises=AssertionError, reason=f"{ISSUE}: policy edit leaves old export"
)
def test_editing_tolerance_invalidates_current_export(pane):
    pane.locator(".check").first.locator("input[inputmode='decimal']").first.fill("0.01")
    assert not current_export_available(pane)


def test_invalid_run_hides_current_report(pane):
    """Existing visible failure behavior is retained as a positive control."""
    pane.select_option("#add-check", "in_range")
    pane.click("#add-check-button")
    pane.click("#run")
    assert not current_export_available(pane)
    assert pane.locator("#policy-issues").is_visible()


def run_host_probe(page: Any) -> dict[str, Any]:
    from playwright.sync_api import expect

    page.locator("#excel-spike summary").click()
    page.locator("#spike-portfolios").fill("10")
    page.locator("#spike-run").click()
    report = page.locator("#spike-report")
    expect(report).to_have_value(re.compile(r"(All steps passed|step\(s\) FAILED)"), timeout=30000)
    return json.loads(report.input_value().splitlines()[-1])


@pytest.mark.parametrize(
    "pane",
    [
        {"calculationMode": "Automatic", "calculationState": "Done"},
        {"calculationMode": "Manual", "calculationState": "Pending"},
        {"calculationMode": "Automatic", "calculationState": "Calculating"},
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


@pytest.mark.parametrize("pane", [{"requirements": {"1.9": False}}], indirect=True)
def test_unsupported_planned_api_floor_is_reported_without_reading_it(pane):
    captured = run_host_probe(pane)
    step = next(s for s in captured["steps"] if s["name"] == "planned workflow API baseline")
    assert step["status"] == "FAIL"
    assert "workflowBaseline" not in captured["environment"]
    assert "read calculation metadata" not in pane.evaluate("window.__excel.log")
