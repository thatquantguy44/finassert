"""Verified snapshot exports, durable ownership and recoverable host failures."""

import json
import os
import re
from pathlib import Path

import pytest

if os.environ.get("FINASSERT_EXCEL_PAGE"):
    from playwright.sync_api import expect

pytestmark = pytest.mark.skipif(
    not os.environ.get("FINASSERT_EXCEL_PAGE"), reason="requires the bundled Excel browser job"
)


def current(page):
    expect(page.locator("#excel-freshness")).to_have_attribute("data-state", "Current")


def write(page):
    page.click("#excel-write")
    expect(page.locator("#excel-output-status")).to_contain_text("Results written")
    current(page)


def owner(page, name="finassert results"):
    return page.evaluate(
        """name => {const s=window.__excel.sheets[name];
          return window.__excel.settings['finassert.output.v1.'+s.id];}""",
        name,
    )


def select_replacement(page, sheet_id):
    page.select_option("#excel-replace-target", sheet_id)
    page.click("#excel-replace")


def test_json_html_and_sheet_share_canonical_results_and_snapshot_context(pane):
    source = pane.evaluate("JSON.stringify(window.__excel.sheets.Holdings)")
    original = pane.evaluate("JSON.parse(window.finassertApp.result().artifact_json)")
    context = original["input"]["excel"]
    assert context["data_row_count"] == context["physical_data_row_count"] == 2
    assert context["date_system"] == "1900" and context["date_system_source"] == "user"
    assert context["snapshot_sha256"] == pane.evaluate(
        "window.finassertExcel.status().snapshot.sha256"
    )
    assert "formula" not in context and "navigation" not in context
    with pane.expect_download() as downloaded:
        pane.click("#download-json")
    artifact = json.loads(Path(downloaded.value.path()).read_text())
    with pane.expect_download() as downloaded:
        pane.click("#download-html")
    html = Path(downloaded.value.path()).read_text()
    match = re.search(r'id="finassert-report">(.*?)</script>', html, re.S)
    embedded = json.loads(match[1])
    assert artifact["report"] == embedded["report"] == original["report"]
    assert artifact["policy"] == embedded["policy"] == original["policy"]
    assert artifact["generated_at"] == original["generated_at"]
    for exported in (artifact, embedded):
        actual = exported["input"]["excel"]
        assert {k: v for k, v in actual.items() if k != "verified_at"} == {
            k: v for k, v in context.items() if k != "verified_at"
        }
        assert actual["verified_at"] >= context["verified_at"]
    write(pane)
    expected = pane.evaluate("window.finassertApp.resultsSheet().rows")
    assert pane.evaluate("window.__excel.sheets['finassert results'].cells") == expected
    assert pane.evaluate("JSON.stringify(window.__excel.sheets.Holdings)") == source
    assert owner(pane)["state"] == "complete"


def test_new_output_never_rewrites_prior_evidence(pane):
    write(pane)
    first = pane.evaluate("JSON.stringify(window.__excel.sheets['finassert results'])")
    write(pane)
    expect(pane.locator("#excel-output-status")).to_contain_text("finassert results (2)")
    assert pane.evaluate("JSON.stringify(window.__excel.sheets['finassert results'])") == first
    assert owner(pane, "finassert results (2)")["state"] == "complete"


@pytest.mark.parametrize("pane", [{"sheetName": "O'Brien"}], indirect=True)
def test_native_literal_quote_semantics_preserve_staged_addresses_and_policy(pane):
    before = pane.evaluate("JSON.parse(window.finassertApp.result().artifact_json).input")
    assert before["locator"].startswith("'")
    write(pane)
    rows = pane.evaluate("window.__excel.sheets['finassert results'].cells")
    fields = {row[0]: row[1] for row in rows}
    assert fields["Checked"] == fields["Excel address"] == before["locator"]
    assert rows == pane.evaluate("window.finassertApp.resultsSheet().rows")
    pane.click("#excel-save-policy")
    expect(pane.locator("#status")).to_contain_text("Saved the checks")
    pane.click("#excel-load-policy")
    expect(pane.locator("#status")).to_contain_text("Opened the checks saved in this workbook")


def test_explicit_replacement_follows_owned_id_after_rename(pane):
    write(pane)
    sheet_id = owner(pane)["worksheet_id"]
    pane.evaluate("window.__excel.renameSheet('finassert results','Renamed evidence')")
    pane.click("#excel-output-refresh")
    expect(pane.locator("#excel-replace-target")).to_contain_text("Renamed evidence")
    select_replacement(pane, sheet_id)
    expect(pane.locator("#excel-output-status")).to_contain_text('"Renamed evidence"')
    current(pane)
    assert owner(pane, "Renamed evidence")["worksheet_id"] == sheet_id


def test_same_named_replacement_is_not_adopted(pane):
    write(pane)
    sheet_id = owner(pane)["worksheet_id"]
    pane.evaluate("""() => {window.__excel.removeSheet('finassert results');
      return Excel.run(async c => {c.workbook.worksheets.add('finassert results')
        .getRangeByIndexes(0,0,1,1).values=[['unrelated']]; await c.sync();});} """)
    select_replacement(pane, sheet_id)
    expect(pane.locator("#excel-output-status")).to_contain_text(
        "not a completed owned results sheet"
    )
    assert pane.evaluate("window.__excel.sheets['finassert results'].cells") == [["unrelated"]]


def test_owned_destination_cannot_replace_a_newly_bound_source(pane):
    write(pane)
    sheet_id = owner(pane)["worksheet_id"]
    pane.evaluate("""() => {const s=window.__excel.sheets['finassert results'];
      s.cells=[['value'],[-1]]; window.__excel.selectionSheet=s.name;
      window.__excel.selection={r0:0,c0:0,rows:2,cols:1};} """)
    pane.click("#excel-read")
    expect(pane.locator("#excel-freshness")).to_have_attribute("data-state", "Ready")
    pane.click("#run")
    current(pane)  # Missing mapped columns are core errors, still a verified result.
    pane.evaluate(
        """id => {const s=document.getElementById('excel-replace-target');
          s.replaceChildren(new Option('forged',id)); s.value=id;
          s.dispatchEvent(new Event('change'));}""",
        sheet_id,
    )
    pane.click("#excel-replace")
    expect(pane.locator("#excel-output-status")).to_contain_text("bound source")
    assert pane.evaluate("window.__excel.sheets['finassert results'].cells") == [["value"], [-1]]


@pytest.mark.parametrize("phase,after", [(1, False), (2, False), (2, True), (3, True)])
def test_failed_or_partial_writes_never_leave_completed_evidence(pane, phase, after):
    source = pane.evaluate("JSON.stringify(window.__excel.sheets.Holdings)")
    pane.evaluate(
        """args => {window.__excel[args.after?'failAfterWriteAt':'failWriteAt']
          =window.__excel.writes.length+args.phase;}""",
        {"phase": phase, "after": after},
    )
    pane.click("#excel-write")
    expect(pane.locator("#excel-output-status")).to_contain_text("partial sheet may remain")
    assert pane.evaluate("window.__excel.sheets['finassert results'].cells[0][0]").startswith(
        "INCOMPLETE"
    )
    assert owner(pane)["state"] == "incomplete"
    assert pane.evaluate("JSON.stringify(window.__excel.sheets.Holdings)") == source
    pane.evaluate("window.__excel.failWriteAt=null; window.__excel.failAfterWriteAt=null")
    pane.click("#run")
    current(pane)
    write(pane)
    assert owner(pane, "finassert results (2)")["state"] == "complete"
    assert owner(pane)["state"] == "incomplete"


def test_protected_owned_destination_reports_failure_and_preserves_old_cells(pane):
    write(pane)
    sheet_id = owner(pane)["worksheet_id"]
    before = pane.evaluate("JSON.stringify(window.__excel.sheets['finassert results'].cells)")
    pane.evaluate("window.__excel.sheets['finassert results'].protected=true")
    select_replacement(pane, sheet_id)
    expect(pane.locator("#excel-output-status")).to_contain_text("protected")
    assert (
        pane.evaluate("JSON.stringify(window.__excel.sheets['finassert results'].cells)") == before
    )
    assert owner(pane)["state"] == "incomplete"


def test_cancellation_during_output_quarantines_partial_sheet(pane):
    pane.evaluate(
        """() => {window.__outputPauseReached = new Promise(resolve => {
          window.__excel.onWrite = info => {if(info.r0===1) {
            window.__excel.pauseNextSync=true; resolve(true);}};});}"""
    )
    pane.click("#excel-write")
    assert pane.evaluate("() => window.__outputPauseReached") is True
    assert pane.evaluate("window.__excel.paused") is True
    pane.click("#excel-cancel")
    pane.evaluate("window.__excel.onWrite=null; window.__excel.resume()")
    expect(pane.locator("#excel-output-status")).to_contain_text("partial sheet may remain")
    assert owner(pane)["state"] == "incomplete"
    assert pane.evaluate("window.__excel.maxActiveRuns") == 1


def test_valid_policy_save_load_is_independent_of_bad_capture_settings(pane):
    pane.locator("#excel-open-settings").click()
    pane.locator("#excel-confirmations").fill("1")
    expect(pane.locator("#excel-freshness")).to_have_attribute("data-state", "Blocked")
    pane.locator("#excel-back-to-validation").click()
    pane.click("#excel-save-policy")
    expect(pane.locator("#status")).to_contain_text("Saved the checks")
    assert owner(pane, "finassert policy")["state"] == "complete"
    pane.click("#excel-save-policy")
    expect(pane.locator("#status")).to_contain_text("finassert policy (2)")
    pane.click("#excel-load-policy")
    expect(pane.locator("#status")).to_contain_text("Opened the checks saved in this workbook")


def test_output_cell_limits_are_checked_before_any_sheet_is_created(pane):
    document = {
        "version": 1,
        "name": "x" * 33000,
        "rules": [{"rule": "non_negative", "column": "market_value"}],
    }
    pane.evaluate(
        "text => window.finassertApp.openPolicyText(text,'wide.json','wide')", json.dumps(document)
    )
    pane.click("#run")
    current(pane)
    pane.click("#excel-write")
    expect(pane.locator("#excel-output-status")).to_contain_text("cell/row limits")
    assert pane.evaluate("Object.keys(window.__excel.sheets)") == ["Holdings"]


def test_saved_workbook_ownership_survives_a_new_pane(pane):
    write(pane)
    pane.click("#excel-save-policy")
    expect(pane.locator("#status")).to_contain_text("Saved the checks")
    saved = pane.evaluate(
        "({settings:window.__excel.settings,existingSheets:Object.values(window.__excel.sheets).filter(s=>s.name!=='Holdings'),values:window.__excel.sheets.Holdings.cells.slice(2)})"
    )
    config = {**saved, "selected": "range", "table": True}
    stub = (
        (Path(__file__).resolve().parents[2] / "scripts/excel_stub.js")
        .read_text()
        .replace("__CONFIG__", json.dumps(config))
    )
    pane.route(
        "https://appsforoffice.microsoft.com/lib/1/hosted/office.js",
        lambda route: route.fulfill(body=stub, content_type="application/javascript"),
    )
    pane.reload()
    expect(pane.locator("#status")).to_have_text(re.compile(r"^Ready\."), timeout=120000)
    pane.click("#excel-policy-refresh")
    expect(pane.locator("#excel-policy-sheet")).to_contain_text("finassert policy")
    entries = pane.evaluate("window.finassertOutput.list()")
    assert [e["owner"]["role"] for e in entries if e["owner"]] == ["results", "policy"]
    pane.click("#excel-load-policy")
    expect(pane.locator("#status")).to_contain_text("Opened the checks saved in this workbook")
