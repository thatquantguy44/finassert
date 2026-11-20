"""Diagnostic selection against the real pane/Python bridge and a controlled host."""

import json
import os
import re

import pytest

if os.environ.get("FINASSERT_EXCEL_PAGE"):
    from playwright.sync_api import expect

pytestmark = pytest.mark.skipif(
    not os.environ.get("FINASSERT_EXCEL_PAGE"), reason="requires the bundled Excel browser job"
)


def failing_result(page):
    page.evaluate("window.__excel.sheets.Holdings.cells[3][3] = -1")
    page.click("#run")
    expect(page.locator("#excel-freshness")).to_have_attribute("data-state", "Current")
    return page.get_by_role("button", name=re.compile(r"^Select cell in row 4")).first


def custom_result(page, rules):
    page.select_option("#excel-date-system", "1900")
    page.click("#excel-read")
    expect(page.locator("#excel-freshness")).to_have_attribute("data-state", "Ready")
    document = json.dumps({"version": 1, "rules": rules})
    assert page.evaluate(
        "text => window.finassertApp.openPolicyText(text, 'navigation.json', 'navigation')",
        document,
    )
    page.click("#run")
    expect(page.locator("#excel-freshness")).to_have_attribute("data-state", "Current")


def test_keyboard_cell_navigation_reverifies_and_preserves_source(pane):
    button = failing_result(pane)
    before = pane.evaluate("JSON.stringify(window.__excel.sheets.Holdings)")
    reads = pane.evaluate("window.__excel.reads.length")
    # Move the user's selection: navigation still belongs to the bound source.
    pane.evaluate("window.__excel.selection = {r0:30,c0:20,rows:1,cols:1}")
    button.focus()
    button.press("Enter")
    expect(pane.locator("#excel-navigation-state")).to_contain_text("Selected cell in row 4")
    selected = pane.evaluate("window.__excel.navigation")
    assert (selected["r0"], selected["c0"], selected["rows"], selected["cols"]) == (3, 3, 1, 1)
    assert pane.evaluate("window.__excel.reads.length") - reads == 2
    assert pane.evaluate("JSON.stringify(window.__excel.sheets.Holdings)") == before
    assert pane.evaluate("window.__excel.maxActiveRuns") == 1


@pytest.mark.parametrize(
    "mutation",
    [
        "s.cells[3][3] = -5",  # missing/delayed event
        "[s.cells[3],s.cells[4]] = [s.cells[4],s.cells[3]]",  # silent sort
        "s.cells.splice(3,1)",  # silent deletion
        "window.__excel.recreateSheet()",  # replacement with same name
        "window.__excel.formulas['3,3'] = '=0-1'",  # same result, different formula
    ],
)
def test_changed_source_never_uses_old_target(pane, mutation):
    button = failing_result(pane)
    pane.evaluate(f"() => {{const s=window.__excel.sheets.Holdings; {mutation};}}")
    button.click()
    expect(pane.locator("#excel-navigation-state")).to_contain_text("Navigation unavailable")
    assert pane.evaluate("window.__excel.navigation || null") is None
    assert pane.evaluate("window.finassertApp.result().passed") is False


def test_edit_notification_disables_navigation_and_old_action(pane):
    button = failing_result(pane)
    pane.evaluate("window.__excel.change('RangeEdited')")
    expect(button).to_be_disabled()
    assert (
        pane.evaluate("window.finassertExcel.navigate(window.finassertApp.result(),0,0,0,0)")
        is False
    )
    assert pane.evaluate("window.__excel.navigation || null") is None


def test_cancel_during_navigation_preflight_cannot_select(pane):
    button = failing_result(pane)
    pane.evaluate("window.__excel.pauseReadAt = window.__excel.reads.length + 1")
    button.click()
    pane.wait_for_function("window.__excel.paused")
    pane.click("#excel-cancel")
    pane.evaluate("window.__excel.resume()")
    expect(pane.locator("#excel-navigation-state")).to_contain_text("Navigation unavailable")
    assert pane.evaluate("window.__excel.navigation || null") is None


def test_host_selection_failure_has_actionable_status(pane):
    button = failing_result(pane)
    pane.evaluate("window.__excel.failSelection = true")
    button.click()
    expect(pane.locator("#excel-navigation-state")).to_contain_text("Selection is protected")
    assert pane.evaluate("window.__excel.navigation || null") is None


@pytest.mark.parametrize(
    "pane",
    [
        {
            "startUnbound": True,
            "sheetName": "O'Brien ! <img>",
            "rowIndex": 6,
            "columnIndex": 2,
            "values": [["id", "value"], [999, -1], ["", ""], ["<img src=x onerror=alert(1)>", -2]],
        }
    ],
    indirect=True,
)
def test_business_keys_offsets_gaps_and_quoted_names_are_safe(pane):
    custom_result(pane, [{"rule": "in_range", "column": "value", "minimum": 0, "row_key": "id"}])
    buttons = pane.locator("#excel-findings-list button")
    assert buttons.count() == 2
    expect(buttons.first).to_contain_text("row 8 (row 999)")
    expect(buttons.last).to_contain_text("row 10")
    assert pane.locator("#excel-findings-list img, #excel-findings-list a").count() == 0
    buttons.last.click()
    expect(pane.locator("#excel-navigation-state")).to_contain_text("Selected cell in row 10")
    assert pane.evaluate("window.__excel.navigation.address") == "'O''Brien ! <img>'!D10"


@pytest.mark.parametrize("keys", [[999, 999], [1.5, "1.5"]])
def test_ambiguous_keys_are_displayed_without_navigation(pane, keys):
    # Replace the default source data while keeping its shape and binding.
    pane.evaluate(
        """keys => {const s=window.__excel.sheets.Holdings;
          s.cells[3][1]=keys[0]; s.cells[4][1]=keys[1]; s.cells[3][3]=-1;}""",
        keys,
    )
    document = json.dumps(
        {
            "version": 1,
            "rules": [
                {"rule": "in_range", "column": "market_value", "minimum": 0, "row_key": "ticker"}
            ],
        }
    )
    pane.evaluate(
        "text => window.finassertApp.openPolicyText(text,'ambiguous.json','ambiguous')", document
    )
    pane.click("#run")
    expect(pane.locator("#excel-findings-list")).to_contain_text("Ambiguous row key")
    assert pane.locator("#excel-findings-list button").count() == 0


def test_group_context_retained_rows_and_truncation_are_visible(pane):
    pane.evaluate("window.__excel.sheets.Holdings.cells[3][3] = 500")
    document = json.dumps(
        {
            "version": 1,
            "rules": [
                {
                    "rule": "nav_reconciles",
                    "market_value": "market_value",
                    "nav": "nav",
                    "group_by": ["portfolio"],
                }
            ],
        }
    )
    assert pane.evaluate(
        "text => window.finassertApp.openPolicyText(text,'group.json','group')", document
    )
    pane.click("#run")
    expect(pane.locator("#excel-findings-list")).to_contain_text('"portfolio": "Alpha"')
    expect(pane.locator("#excel-findings-list")).to_contain_text("example cap 20")
    button = pane.get_by_role("button", name=re.compile(r"^Select source row 4")).first
    button.click()
    expect(pane.locator("#excel-navigation-state")).to_contain_text("Selected source row 4")
    selected = pane.evaluate("window.__excel.navigation")
    assert (selected["c0"], selected["cols"]) == (0, 5)


def test_policy_change_and_snapshot_only_disable_targets(pane):
    button = failing_result(pane)
    pane.select_option("#template", "long-only-holdings")
    expect(button).to_be_disabled()
    pane.locator("#excel-open-settings").click()
    pane.select_option("#excel-capture-mode", "snapshot")
    pane.locator("#excel-back-to-validation").click()
    pane.click("#run")
    expect(pane.locator("#excel-freshness")).to_have_attribute("data-state", "Stale")
    for button in pane.locator("#excel-findings-list button").all():
        expect(button).to_be_disabled()


@pytest.mark.parametrize(
    "pane",
    [
        {
            "startUnbound": True,
            "values": [["entity", "ccy", "start", "end"], ["A", "USD", "2026-10-01", "2026-10-08"]],
        }
    ],
    indirect=True,
)
def test_missing_groups_and_periods_never_fabricate_a_target(pane):
    custom_result(
        pane,
        [
            {
                "rule": "forecast_coverage",
                "period_start": "start",
                "period_end": "end",
                "group_by": ["entity"],
                "currency": "ccy",
                "expected_scope": [{"entity": "A", "ccy": "USD"}, {"entity": "B", "ccy": "USD"}],
                "first_period": "2026-10-01",
                "periods": 2,
            }
        ],
    )
    expect(pane.locator("#excel-findings-list")).to_contain_text("No source row")
    expect(pane.locator("#excel-findings-list")).to_contain_text("missing_period")
    expect(pane.locator("#excel-findings-list")).to_contain_text('"entity": "B"')
    assert (
        pane.locator("#excel-findings-list").get_by_text("No source row", exact=True).count() == 3
    )
    assert pane.locator("#excel-findings-list button").count() == 0


def test_old_result_callbacks_do_not_navigate_a_new_result(pane):
    failing_result(pane)
    pane.evaluate("window.oldNavigationResult = window.finassertApp.result()")
    pane.click("#run")
    expect(pane.locator("#excel-freshness")).to_have_attribute("data-state", "Current")
    assert (
        pane.evaluate("window.finassertExcel.navigate(window.oldNavigationResult,2,1,0,0)") is False
    )
    assert pane.evaluate("window.__excel.navigation || null") is None


def test_navigation_honors_on_demand_and_four_capture_settings(pane):
    failing_result(pane)
    pane.locator("#excel-open-settings").click()
    pane.select_option("#excel-monitoring", "on-demand")
    pane.locator("#excel-confirmations").fill("4")
    pane.locator("#excel-back-to-validation").click()
    pane.click("#run")
    expect(pane.locator("#excel-freshness")).to_have_attribute("data-state", "Current")
    reads = pane.evaluate("window.__excel.reads.length")
    pane.get_by_role("button", name=re.compile(r"^Select cell in row 4")).first.click()
    expect(pane.locator("#excel-navigation-state")).to_contain_text("Selected cell in row 4")
    assert pane.evaluate("window.__excel.reads.length") - reads == 4


@pytest.mark.parametrize("mutation", ["s.tables[0].rows++", "s.tables[0].id = 'replacement'"])
def test_silent_table_resize_or_replacement_rejects_old_targets(pane, mutation):
    pane.select_option("#excel-table", "table-1")
    pane.click("#excel-bind-table")
    expect(pane.locator("#excel-freshness")).to_have_attribute("data-state", "Ready")
    button = failing_result(pane)
    pane.evaluate(f"() => {{const s=window.__excel.sheets.Holdings; {mutation};}}")
    button.click()
    expect(pane.locator("#excel-navigation-state")).to_contain_text("Navigation unavailable")
    assert pane.evaluate("window.__excel.navigation || null") is None
