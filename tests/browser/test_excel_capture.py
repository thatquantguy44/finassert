"""Configurable capture/freshness integration, with real Python and controlled host races."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

if os.environ.get("FINASSERT_EXCEL_PAGE"):
    from playwright.sync_api import expect

pytestmark = pytest.mark.skipif(
    not os.environ.get("FINASSERT_EXCEL_PAGE"), reason="requires the bundled Excel browser job"
)


def workflow(page, state):
    expect(page.locator("#excel-freshness")).to_have_attribute("data-state", state)


def settings(page):
    if page.locator("#excel-workflow-settings").get_attribute("open") is None:
        page.locator("#excel-workflow-settings summary").click()


def pause_next_read(page):
    page.evaluate("window.__excel.pauseReadAt = window.__excel.reads.length + 1")
    page.click("#run")
    page.wait_for_function("window.__excel.paused === true")
    workflow(page, "Reading")


def test_verified_result_preserves_outcomes_and_has_a_snapshot_identity(pane):
    workflow(pane, "Current")
    status = pane.evaluate("window.finassertExcel.status()")
    assert status["snapshot"]["sha256"].startswith("sha256:")
    assert status["snapshot"]["capturedAt"] <= status["snapshot"]["verifiedAt"]
    assert pane.evaluate("window.finassertApp.result().passed") is True
    expect(pane.locator("#excel-write")).to_be_enabled()


@pytest.mark.parametrize("event", ["value", "format", "calculation", "policy_name", "policy_rule"])
def test_relevant_changes_make_a_result_historical_immediately(pane, event):
    if event == "value":
        pane.evaluate("window.__excel.change('RangeEdited')")
    elif event == "format":
        pane.evaluate("window.__excel.formatChanged()")
    elif event == "calculation":
        pane.evaluate("window.__excel.recalculate()")
    elif event == "policy_name":
        pane.locator("#policy-name").fill("Changed policy")
    else:
        pane.locator(".check input[inputmode='decimal']").first.fill("0.02")
    workflow(pane, "Stale")
    expect(pane.locator("#result-banner")).to_contain_text("Historical")
    expect(pane.locator("#excel-write")).to_be_disabled()
    expect(pane.locator("#download-json")).to_be_disabled()
    assert pane.evaluate("window.finassertApp.result().passed") is True


def test_unrelated_cells_and_selection_do_not_invalidate(pane):
    pane.evaluate("""() => {
      window.__excel.change('RangeEdited', 'Holdings', 'Z99');
      window.__excel.formatChanged('Z99');
      window.__excel.selected = 'single';
    }""")
    workflow(pane, "Current")
    expect(pane.locator("#excel-write")).to_be_enabled()


def test_monitoring_is_configurable_but_exports_always_reverify(pane):
    settings(pane)
    pane.select_option("#excel-monitoring", "on-demand")
    workflow(pane, "Stale")
    pane.click("#run")
    workflow(pane, "Current")
    pane.evaluate("""() => {
      window.__excel.sheets.Holdings.cells[3][3] = -1;
      window.__excel.change('RangeEdited');
    }""")
    workflow(pane, "Current")
    expect(pane.locator("#excel-freshness")).to_contain_text("Live alerts are off")
    pane.click("#excel-write")
    workflow(pane, "Blocked")
    assert pane.evaluate("window.__excel.sheets['finassert results']") is None
    expect(pane.locator("#result-banner")).to_contain_text("Historical")


@pytest.mark.parametrize("control", ["#excel-write", "#download-json", "#download-html"])
def test_missing_event_cannot_authorize_export(pane, control):
    downloads = []
    pane.on("download", lambda download: downloads.append(download))
    pane.evaluate("window.__excel.sheets.Holdings.cells[3][3] = -1")
    pane.click(control)
    workflow(pane, "Blocked")
    assert not downloads
    assert pane.evaluate("window.__excel.sheets['finassert results']") is None


@pytest.mark.parametrize("control", ["#excel-write", "#download-json", "#download-html"])
def test_unchanged_current_results_export_after_a_fresh_preflight(pane, control):
    before = pane.evaluate("JSON.stringify(window.__excel.sheets.Holdings.cells)")
    reads = pane.evaluate("window.__excel.reads.length")
    if control == "#excel-write":
        pane.click(control)
    else:
        with pane.expect_download() as downloaded:
            pane.click(control)
        assert Path(downloaded.value.path()).stat().st_size > 100
    workflow(pane, "Current")
    assert pane.evaluate("window.__excel.reads.length") - reads == 2
    assert pane.evaluate("JSON.stringify(window.__excel.sheets.Holdings.cells)") == before


def test_disposed_event_callbacks_cannot_invalidate_a_new_binding(pane):
    pane.evaluate("window.__oldHandlers = window.__excel.handlers.slice()")
    pane.click("#excel-read")
    workflow(pane, "Ready")
    pane.click("#run")
    workflow(pane, "Current")
    pane.evaluate("window.__oldHandlers.forEach(h => h.callback({changeType:'RowInserted'}))")
    workflow(pane, "Current")
    assert pane.evaluate("window.__excel.handlers.filter(h => !h.removed).length") == 3


@pytest.mark.parametrize(
    "name,control",
    [("finassert results", "#excel-write"), ("finassert policy", "#excel-save-policy")],
)
def test_existing_unowned_sheets_are_never_cleared_by_name(pane, name, control):
    pane.evaluate(
        """name => Excel.run(async context => {
          const sheet=context.workbook.worksheets.add(name);
          sheet.getRangeByIndexes(0,0,1,1).values=[['unrelated content']];
          await context.sync();
        })""",
        name,
    )
    pane.click(control)
    workflow(pane, "Current")
    expect(pane.locator("#status")).to_contain_text(name + " (2)")
    assert pane.evaluate("name => window.__excel.sheets[name].cells", name) == [
        ["unrelated content"]
    ]


def test_failed_parse_never_turns_a_live_result_into_a_file_export(pane):
    pane.evaluate("window.__excel.sheets.Holdings.cells[2][1] = 'portfolio'")
    pane.click("#run")
    workflow(pane, "Blocked")
    assert pane.evaluate("window.finassertApp.result().passed") is True
    assert pane.evaluate("window.finassertExcel.withCurrentResult(() => true)") is False
    expect(pane.locator("#download-json")).to_be_disabled()


@pytest.mark.parametrize("pane", [{"startUnbound": True}], indirect=True)
def test_a_single_wide_row_cannot_exceed_the_configured_cell_limit(pane):
    settings(pane)
    pane.locator("#excel-block-cells").fill("1000")
    pane.evaluate("window.__excel.selection = {r0:0,c0:0,rows:2,cols:1001}")
    pane.select_option("#excel-date-system", "1900")
    pane.click("#excel-read")
    workflow(pane, "Blocked")
    expect(pane.locator("#excel-freshness")).to_contain_text("One source row exceeds")
    assert pane.evaluate("window.__excel.reads") == []


def test_configurable_snapshot_only_never_becomes_current(pane):
    settings(pane)
    pane.select_option("#excel-capture-mode", "snapshot")
    workflow(pane, "Stale")
    before = pane.evaluate("window.__excel.reads.length")
    pane.click("#run")
    expect(pane.locator("#excel-freshness")).to_contain_text("Snapshot-only result")
    workflow(pane, "Stale")
    assert pane.evaluate("window.__excel.reads.length") - before == 1
    assert pane.evaluate("window.finassertApp.result().passed") is True
    assert pane.evaluate("window.finassertExcel.status().snapshot.verifiedAt") is None
    expect(pane.locator("#excel-write")).to_be_disabled()
    pane.click("#excel-settings-reset")
    pane.click("#run")
    workflow(pane, "Current")


def test_confirmation_count_and_request_bounds_are_configurable(pane):
    settings(pane)
    pane.locator("#excel-confirmations").fill("4")
    pane.locator("#excel-block-rows").fill("2")
    before = pane.evaluate("window.__excel.reads.length")
    pane.click("#run")
    workflow(pane, "Current")
    reads = pane.evaluate(f"window.__excel.reads.slice({before})")
    assert [r["rows"] for r in reads] == [2, 1] * 4


@pytest.mark.parametrize(
    "control,value",
    [
        ("#excel-confirmations", "1"),
        ("#excel-block-rows", "0"),
        ("#excel-block-cells", "50001"),
        ("#excel-capture-timeout", "301"),
    ],
)
def test_invalid_settings_block_and_defaults_recover(pane, control, value):
    settings(pane)
    pane.locator(control).fill(value)
    workflow(pane, "Blocked")
    expect(pane.locator("#run")).to_be_disabled()
    expect(pane.locator("#excel-write")).to_be_disabled()
    pane.click("#excel-settings-reset")
    pane.click("#run")
    workflow(pane, "Current")


@pytest.mark.parametrize("change", ["policy", "date", "settings", "external_input", "cancel"])
def test_superseded_reads_cannot_publish_or_overlap(pane, change):
    pause_next_read(pane)
    reads = pane.evaluate("window.__excel.reads.length")
    assert pane.evaluate("window.finassertExcel.run()") is False
    assert pane.evaluate("window.__excel.reads.length") == reads
    if change == "policy":
        pane.locator("#policy-name").fill("Changed during capture")
    elif change == "date":
        pane.evaluate("""() => {
          const node=document.getElementById('excel-date-system');
          node.value='1904'; node.dispatchEvent(new Event('change'));
        }""")
    elif change == "settings":
        pane.evaluate("""() => {
          const node=document.getElementById('excel-confirmations');
          node.value='3'; node.dispatchEvent(new Event('change'));
        }""")
    elif change == "external_input":
        pane.evaluate("window.finassertApp.useData('new.csv', 'x\\n1', '')")
    else:
        pane.click("#excel-cancel")
    pane.evaluate("window.__excel.resume()")
    workflow(pane, "Blocked")
    assert pane.evaluate("window.__excel.maxActiveRuns") == 1
    expect(pane.locator("#excel-write")).to_be_disabled()


def test_a_mixed_chunk_capture_is_discarded_without_an_event(pane):
    settings(pane)
    pane.locator("#excel-block-rows").fill("2")
    pane.evaluate("""() => { window.__excel.onRead = () => {
      window.__excel.sheets.Holdings.cells[3][3] = -1;
      window.__excel.onRead = null;
    }; }""")
    pane.click("#run")
    workflow(pane, "Blocked")
    expect(pane.locator("#excel-freshness")).to_contain_text("changed between captures")
    expect(pane.locator("#result-banner")).to_contain_text("Historical")


@pytest.mark.parametrize("change", ["values", "formulas", "formats", "calculation", "policy"])
def test_changes_during_evaluation_reject_the_candidate(pane, change):
    pane.evaluate(
        """(change) => {
      const original=window.finassertApp.evaluate;
      window.finassertApp.evaluate=() => {
        const candidate=original();
        if(change==='values') window.__excel.sheets.Holdings.cells[3][3]=-1;
        if(change==='formulas') window.__excel.formulas['3,3']='=200*2';
        if(change==='formats') window.__excel.numberFormats=
          [[],[],['General','General','General','0%','General']];
        if(change==='calculation') window.__excel.application.calculationState='Pending';
        if(change==='policy') document.getElementById('policy-name').value='Silent policy edit';
        return candidate;
      };
    }""",
        change,
    )
    pane.click("#run")
    workflow(pane, "Blocked")
    expect(pane.locator("#excel-write")).to_be_disabled()
    expect(pane.locator("#result-banner")).to_contain_text("Historical")


def test_timeout_applies_after_a_pending_host_request_returns(pane):
    settings(pane)
    pane.locator("#excel-capture-timeout").fill("1")
    pause_next_read(pane)
    pane.wait_for_timeout(1100)
    pane.evaluate("window.__excel.resume()")
    workflow(pane, "Blocked")
    expect(pane.locator("#excel-freshness")).to_contain_text("timed out between requests")


def test_calculation_guards_require_settled_values_and_manual_confirmation(pane):
    settings(pane)
    pane.evaluate("window.__excel.application.calculationState='Pending'")
    pane.click("#run")
    workflow(pane, "Blocked")
    pane.evaluate("""() => {
      window.__excel.application.calculationState='Done';
      window.__excel.application.calculationMode='Manual';
    }""")
    pane.click("#run")
    expect(pane.locator("#excel-freshness")).to_contain_text("Manual calculation mode")
    pane.locator("#excel-manual-calculated").check()
    pane.click("#run")
    workflow(pane, "Current")
    assert not pane.locator("#excel-manual-calculated").is_checked()
    assert pane.evaluate("window.__excel.application.calculationMode") == "Manual"
    pane.locator("#excel-manual-calculated").check()
    workflow(pane, "Current")
    pane.click("#excel-write")
    workflow(pane, "Current")
    assert not pane.locator("#excel-manual-calculated").is_checked()
    assert pane.evaluate("window.__excel.sheets['finassert results']") is not None


def test_configuration_is_session_only(pane):
    settings(pane)
    pane.select_option("#excel-capture-mode", "snapshot")
    pane.reload()
    expect(pane.locator("#status")).to_contain_text("Ready.", timeout=120000)
    workflow(pane, "Unbound")
    assert pane.locator("#excel-capture-mode").input_value() == "verified"
    assert pane.locator("#excel-monitoring").input_value() == "events"
    assert pane.locator("#excel-date-system").input_value() == ""


@pytest.mark.parametrize("change", ["edit", "failed_load"])
def test_file_results_in_the_excel_pane_clear_on_policy_changes(pane, change):
    pane.set_input_files(
        "#data-file",
        {
            "name": "holdings.csv",
            "mimeType": "text/csv",
            "buffer": b"portfolio,ticker,weight,market_value,nav\nAlpha,AAA,1,400,1000\n",
        },
    )
    expect(pane.locator("#data-name")).to_contain_text("holdings.csv: 1 row(s)")
    pane.click("#run")
    expect(pane.locator("#result-banner")).to_contain_text("Passed")
    if change == "edit":
        pane.locator("#policy-name").fill("File policy changed")
    else:
        pane.evaluate("window.finassertApp.openPolicyText('this: [', 'bad.yml', 'Bad policy')")
    expect(pane.locator("#results")).to_be_hidden()
    assert pane.evaluate("window.finassertApp.result()") is None


def test_fixed_snapshot_encoding_vectors_and_private_formula_identity(pane):
    path = Path(__file__).resolve().parents[2] / "specs/0016/artifacts/e03-capture-vectors.json"
    vectors = json.loads(path.read_text())["vectors"]
    actual = pane.evaluate(
        """async (raw) => {
      const vectors=JSON.parse(raw), out=[];
      for(const v of vectors) out.push({
        canonical:window.finassertCapture.canonical(v.source,v.payload),
        ...await window.finassertCapture.fingerprints(v.source,v.payload,v.formulas) });
      return out;
    }""",
        json.dumps(vectors),
    )
    for vector, result in zip(vectors, actual, strict=True):
        assert result["canonical"] == vector["canonical"]
        assert result["snapshot"] == vector["sha256"]
        assert result["formula"] == vector["formula_sha256"]
