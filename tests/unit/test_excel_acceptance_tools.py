"""Acceptance harness controls; generated exports here are not native evidence."""

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

pytest.importorskip("openpyxl")
from openpyxl import load_workbook

from finassert import web
from finassert.excel import policy_text_from_rows, results_sheet
from finassert.policy.templates import get_template
from finassert.reporting.html import render_artifact_html
from finassert.workbook import read_workbook

ARTIFACTS = Path(__file__).resolve().parents[2] / "specs/0016/artifacts"


def module(name):
    spec = importlib.util.spec_from_file_location(name, ARTIFACTS / f"{name}.py")
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


@pytest.fixture(params=["1900", "1904"])
def exported(tmp_path, request):
    module("prepare_e06_fixtures").prepare(tmp_path)
    epoch = request.param
    workbook = tmp_path / f"holdings-{epoch}.xlsx"
    policy_path = tmp_path / "long-only-holdings.yml"
    source = read_workbook(workbook, sheet="Holdings O'Brien", header_row=7, max_row=9)
    assert source.column("date")[0][0].isoformat() == "2026-01-01"
    assert source.column("market_value")[1] == [8, 9]
    from datetime import datetime

    from openpyxl.utils.datetime import to_excel

    native_book = load_workbook(workbook)
    native_sheet = native_book["Holdings O'Brien"]
    cells = list(native_sheet.iter_rows(min_row=7, max_row=9, min_col=3, max_col=8))
    payload = {
        "firstRow": 7,
        "date1904": epoch == "1904",
        "values": [
            [
                to_excel(cell.value, native_book.epoch)
                if isinstance(cell.value, datetime)
                else cell.value
                for cell in row
            ]
            for row in cells
        ],
        "numberFormats": [[cell.number_format for cell in row] for row in cells],
    }
    native_book.close()
    result = json.loads(
        web.run(
            json.dumps(payload),
            "'Holdings O''Brien'!C7:H9",
            json.dumps(get_template("long-only-holdings").to_dict()["document"]),
            source_format="excel-range",
        )
    )
    assert result["ok"]
    artifact = json.loads(result["artifact_json"])
    artifact["input"]["excel"] = {
        "schema_version": 1,
        "kind": "range",
        "worksheet_name": "Holdings O'Brien",
        "worksheet_id": "synthetic-harness-only",
        "address": artifact["input"]["locator"],
        "header_row": 7,
        "data_row_count": 2,
        "physical_data_row_count": 2,
        "column_count": 6,
        "hidden_rows": "include_all",
        "date_system": epoch,
        "date_system_source": "user",
        "captured_at": "2026-11-15T12:00:00Z",
        "verified_at": "2026-11-15T12:00:01Z",
        "snapshot_sha256": "sha256:" + "a" * 64,
    }
    # Model separate pre-action checks of the same captured snapshot.
    html_artifact = copy.deepcopy(artifact)
    html_artifact["input"]["excel"]["verified_at"] = "2026-11-15T12:00:02Z"
    sheet_artifact = copy.deepcopy(artifact)
    sheet_artifact["input"]["excel"]["verified_at"] = "2026-11-15T12:00:03Z"
    book = load_workbook(workbook)
    assert book["Holdings O'Brien"].row_dimensions[9].hidden
    assert book["Holdings O'Brien"].tables["AcceptanceHoldings"].autoFilter.ref == "C7:H9"
    assert policy_text_from_rows(list(book["finassert policy"].values))
    output = book.create_sheet("finassert results (2)")
    for row in results_sheet(sheet_artifact)[0]:
        output.append(row)
    book.save(workbook)
    book.close()
    json_path = tmp_path / "report.json"
    html_path = tmp_path / "report.html"
    json_path.write_text(json.dumps(artifact))
    html_path.write_text(render_artifact_html(html_artifact))
    return module("verify_e06_exports"), [
        json_path,
        html_path,
        workbook,
        policy_path,
        "finassert results (2)",
    ]


def test_export_harness_ties_out_both_epochs_and_preserves_workbook(exported):
    verifier, args = exported
    before = args[2].read_bytes()
    assert verifier.verify(*args)["status"] == "PASS"
    assert args[2].read_bytes() == before


def test_export_harness_rejects_changed_canonical_diagnostics(exported):
    verifier, args = exported
    artifact = json.loads(args[0].read_text())
    artifact["report"]["results"][2]["diagnostics"][1]["count"] = 999
    args[0].write_text(json.dumps(artifact))
    with pytest.raises(ValueError, match="JSON and HTML"):
        verifier.verify(*args)


def test_export_harness_rejects_changed_source_even_when_exports_agree(exported):
    verifier, args = exported
    book = load_workbook(args[2])
    book["Holdings O'Brien"]["F8"] = 400
    book.save(args[2])
    book.close()
    with pytest.raises(ValueError, match="CLI and native canonical reports"):
        verifier.verify(*args)


def test_export_harness_rejects_sheet_edits(exported):
    verifier, args = exported
    book = load_workbook(args[2])
    book[args[4]]["B6"] = "Incorrect counts"
    book.save(args[2])
    book.close()
    with pytest.raises(ValueError, match="Results sheet differs"):
        verifier.verify(*args)


def test_export_harness_rejects_incorrect_explicit_date_system(exported):
    verifier, args = exported
    book = load_workbook(args[2])
    from openpyxl.utils.datetime import CALENDAR_MAC_1904, CALENDAR_WINDOWS_1900

    book.epoch = CALENDAR_WINDOWS_1900 if book.epoch == CALENDAR_MAC_1904 else CALENDAR_MAC_1904
    book.save(args[2])
    book.close()
    with pytest.raises(ValueError, match="Workbook epoch differs"):
        verifier.verify(*args)
