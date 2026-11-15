"""E-02 source/date contracts against the actual pane, engine and Office stand-in."""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get("FINASSERT_EXCEL_PAGE"), reason="requires the bundled Excel browser job"
)

UNBOUND = {"startUnbound": True}


@pytest.mark.parametrize("pane", [UNBOUND], indirect=True)
def test_date_choice_is_required_and_never_assumed(pane):
    from playwright.sync_api import expect

    assert pane.locator("#excel-date-system").input_value() == ""
    pane.click("#excel-read")
    expect(pane.locator("#status")).to_contain_text("Choose the workbook's 1900 or 1904")
    assert pane.evaluate("window.__excel.reads") == []
    expect(pane.locator("#run")).to_be_disabled()
    pane.select_option("#excel-date-system", "1900")
    expect(pane.locator("#data-name")).to_contain_text("2 row(s)")
    pane.select_option("#template", "long-only-holdings")
    pane.click("#run")
    expect(pane.locator("#result-banner")).to_contain_text("✓ Passed")
    pane.select_option("#excel-date-system", "")
    expect(pane.locator("#run")).to_be_disabled()
    assert not pane.locator("#results").is_visible()
    assert pane.evaluate("window.finassertApp.result()") is None


@pytest.mark.parametrize("pane", [UNBOUND], indirect=True)
def test_selection_changes_do_not_move_fixed_binding(pane):
    from playwright.sync_api import expect

    pane.select_option("#excel-date-system", "1900")
    pane.click("#excel-read")
    expect(pane.locator("#excel-freshness")).to_have_attribute("data-state", "Ready")
    pane.select_option("#template", "long-only-holdings")
    pane.evaluate("window.__excel.selection = {r0:100,c0:10,rows:1,cols:1}")
    pane.click("#run")
    expect(pane.locator("#result-banner")).to_contain_text("✓ Passed")
    expect(pane.locator("#excel-source-summary")).to_contain_text("Holdings!A3:E5")
    assert all(r["r0"] == 2 and r["rows"] == 3 for r in pane.evaluate("window.__excel.reads"))


@pytest.mark.parametrize(
    "pane",
    [{**UNBOUND, "values": [["value"], [1], [""], [-1]], "rowIndex": 6, "columnIndex": 2}],
    indirect=True,
)
def test_offset_blank_rows_and_physical_failure_labels(pane):
    from playwright.sync_api import expect

    pane.select_option("#excel-date-system", "1900")
    pane.click("#excel-read")
    expect(pane.locator("#excel-source-summary")).to_contain_text("Holdings!C7:C10; header row 7")
    expect(pane.locator("#excel-source-summary")).to_contain_text(
        "3 physical data row(s), 1 column(s). 2 parsed"
    )
    pane.select_option("#add-check", "non_negative")
    pane.click("#add-check-button")
    pane.locator(".check select").first.select_option("value")
    pane.click("#run")
    expect(pane.locator("#result-banner")).to_contain_text("✗ Failed")
    report = pane.evaluate("JSON.parse(window.finassertApp.result().artifact_json).report")
    assert report["results"][0]["metadata"]["violations"] == [{"row": 10, "value": -1}]


@pytest.mark.parametrize(
    "pane",
    [{**UNBOUND, "values": [["value"], [1], [2], [-99]], "table": True, "totals": True}],
    indirect=True,
)
def test_table_excludes_totals_and_reads_all_hidden_filtered_rows(pane):
    from playwright.sync_api import expect

    pane.select_option("#excel-date-system", "1900")
    pane.select_option("#excel-table", "table-1")
    pane.click("#excel-bind-table")
    expect(pane.locator("#data-name")).to_contain_text("Holdings!A3:A5: 2 row(s), 1 column(s)")
    expect(pane.locator("#excel-source-summary")).to_contain_text(
        "Table totals excluded. Hidden and filtered rows included"
    )
    reads = pane.evaluate("window.__excel.reads")
    assert reads == [{"r0": 2, "c0": 0, "rows": 3, "cols": 1}]


@pytest.mark.parametrize("pane", [{**UNBOUND, "requirements": {"1.13": False}}], indirect=True)
def test_table_binding_works_without_the_range_merge_api_and_follows_resize(pane):
    from playwright.sync_api import expect

    pane.select_option("#excel-date-system", "1900")
    pane.select_option("#excel-table", "table-1")
    pane.click("#excel-bind-table")
    pane.evaluate("""() => {
      window.__excel.sheets.Holdings.tables[0].rows++;
      window.__excel.sheets.Holdings.tables[0].name = 'RenamedTable';
      window.__excel.sheets.Holdings.cells.push(['Alpha','CCC',0,0,1000]);
      window.__excel.selected = 'single';
    }""")
    pane.click("#excel-source-read")
    expect(pane.locator("#excel-source-summary")).to_contain_text('Table "RenamedTable"')
    expect(pane.locator("#data-name")).to_contain_text("Holdings!A3:E6: 3 row(s)")


@pytest.mark.parametrize("pane", [{**UNBOUND, "sheetName": "Holdings O'Brien"}], indirect=True)
def test_exact_host_address_preserves_sheet_quoting(pane):
    from playwright.sync_api import expect

    pane.select_option("#excel-date-system", "1900")
    pane.click("#excel-read")
    expect(pane.locator("#excel-source-summary")).to_contain_text("'Holdings O''Brien'!A3:E5")


@pytest.mark.parametrize(
    "pane",
    [{**UNBOUND, "values": [["date"], [46023]], "numberFormats": [["General"], ["yyyy-mm-dd"]]}],
    indirect=True,
)
def test_both_epochs_produce_the_same_intended_date(pane):
    from playwright.sync_api import expect

    pane.select_option("#excel-date-system", "1900")
    pane.click("#excel-read")
    expect(pane.locator("#excel-freshness")).to_have_attribute("data-state", "Ready")
    expect(pane.locator("#data-preview tbody")).to_contain_text("2026-01-01")
    before = pane.locator("#data-preview tbody").text_content()
    assert "2026-01-01" in before
    pane.evaluate("window.__excel.sheets.Holdings.cells[3][0] = 44561")
    pane.select_option("#excel-date-system", "1904")
    expect(pane.locator("#data-preview tbody")).to_have_text(before)
    expect(pane.locator("#excel-source-summary")).to_contain_text("Date system: 1904 (user choice)")


@pytest.mark.parametrize(
    "pane, message",
    [
        ({**UNBOUND, "selected": "single"}, "at least one data row"),
        ({**UNBOUND, "selected": "disjoint"}, "disjoint selections"),
        ({**UNBOUND, "mergedHeader": True}, "Unmerge the source header"),
        ({**UNBOUND, "values": [["a", "a"], [1, 2]]}, "could not be parsed"),
        ({**UNBOUND, "values": [["a", ""], [1, 2]]}, "could not be parsed"),
        ({**UNBOUND, "values": [["a"], [""]]}, "no nonblank data rows"),
        ({**UNBOUND, "values": [["a"], ["   "]]}, "no nonblank data rows"),
        ({**UNBOUND, "requirements": {"1.13": False}}, "Range binding needs ExcelApi 1.13"),
        (
            {**UNBOUND, "selection": {"r0": 0, "c0": 0, "rows": 1000000, "cols": 6}},
            "at most 5,000,000",
        ),
    ],
    indirect=["pane"],
)
def test_invalid_sources_cannot_evaluate_or_publish(pane, message):
    from playwright.sync_api import expect

    pane.select_option("#excel-date-system", "1900")
    pane.click("#excel-read")
    expect(pane.locator("#status")).to_contain_text(message)
    expect(pane.locator("#run")).to_be_disabled()
    assert pane.evaluate("window.finassertApp.result()") is None
    if "5,000,000" in message or "disjoint" in message or "Unmerge" in message:
        assert pane.evaluate("window.__excel.reads") == []


@pytest.mark.parametrize("pane", [UNBOUND], indirect=True)
def test_structural_edits_invalidate_range_and_rebinding_disposes_handler(pane):
    from playwright.sync_api import expect

    pane.select_option("#excel-date-system", "1900")
    pane.click("#excel-read")
    pane.click("#excel-read")
    assert pane.evaluate("window.__excel.handlers.filter(h => !h.removed).length") == 3
    pane.evaluate("window.__excel.change('RowInserted')")
    expect(pane.locator("#excel-source-summary")).to_have_text("No source bound.")
    expect(pane.locator("#run")).to_be_disabled()
    assert not pane.locator("#data-summary").is_visible()


@pytest.mark.parametrize("pane", [UNBOUND], indirect=True)
def test_recreated_sheet_is_not_resolved_by_display_name(pane):
    from playwright.sync_api import expect

    pane.select_option("#excel-date-system", "1900")
    pane.click("#excel-read")
    pane.evaluate("window.__excel.recreateSheet()")
    pane.click("#excel-source-read")
    expect(pane.locator("#status")).to_contain_text("bound worksheet no longer exists")
    assert not pane.locator("#data-summary").is_visible()


@pytest.mark.parametrize("pane", [UNBOUND], indirect=True)
def test_deleted_table_is_not_rebound_to_a_replacement_with_the_same_name(pane):
    from playwright.sync_api import expect

    pane.select_option("#excel-date-system", "1900")
    pane.select_option("#excel-table", "table-1")
    pane.click("#excel-bind-table")
    pane.evaluate("window.__excel.sheets.Holdings.tables[0].id = 'replacement-table'")
    pane.click("#excel-source-read")
    expect(pane.locator("#status")).to_contain_text("bound table no longer exists")
    assert not pane.locator("#data-summary").is_visible()


@pytest.mark.parametrize("pane", [UNBOUND], indirect=True)
def test_changed_headers_require_rebinding_and_mapping_review(pane):
    from playwright.sync_api import expect

    pane.select_option("#excel-date-system", "1900")
    pane.click("#excel-read")
    pane.evaluate("window.__excel.sheets.Holdings.cells[2][0] = 'renamed'")
    pane.click("#excel-source-read")
    expect(pane.locator("#status")).to_contain_text("review every column mapping")
    expect(pane.locator("#excel-source-summary")).to_have_text("No source bound.")


@pytest.mark.parametrize("pane", [UNBOUND], indirect=True)
def test_wide_ranges_use_bounded_requests_and_failed_reads_publish_nothing(pane):
    from playwright.sync_api import expect

    pane.evaluate("""() => {
      window.__excel.sheets.Holdings.cells = [Array.from({length:1000}, (_,i) => 'c'+i),
        ...Array.from({length:101}, () => Array(1000).fill(1))];
      window.__excel.selection = {r0:0,c0:0,rows:102,cols:1000};
    }""")
    pane.select_option("#excel-date-system", "1900")
    pane.click("#excel-read")
    expect(pane.locator("#data-name")).to_contain_text("101 row(s), 1000 column(s)")
    assert [r["rows"] for r in pane.evaluate("window.__excel.reads")] == [50, 50, 2]
    pane.evaluate("window.__excel.failReadAt = window.__excel.reads.length + 2")
    pane.click("#excel-source-read")
    expect(pane.locator("#status")).to_contain_text("synthetic payload limit")
    assert not pane.locator("#data-summary").is_visible()
    expect(pane.locator("#run")).to_be_disabled()
