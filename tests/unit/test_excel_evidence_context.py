"""Strict live provenance, canonical view parity, and unchanged file artifacts."""

import json
import re

import pytest

from finassert import web
from finassert._excel_evidence import parse_context
from finassert.excel import results_sheet


def context(**changes):
    return {
        "schema_version": 1,
        "kind": "range",
        "worksheet_name": "O'Brien",
        "worksheet_id": "sheet-1",
        "address": "'O''Brien'!C7:D10",
        "header_row": 7,
        "data_row_count": 2,
        "physical_data_row_count": 3,
        "column_count": 2,
        "hidden_rows": "include_all",
        "date_system": "1904",
        "date_system_source": "user",
        "captured_at": "2026-11-15T10:00:00.123Z",
        "verified_at": "2026-11-15T10:00:01.123Z",
        "snapshot_sha256": "sha256:" + "a" * 64,
        **changes,
    }


def live_result(*, limit=1, values=None):
    payload = {
        "firstRow": 7,
        "date1904": True,
        "values": values
        or [["key", "value"], ["A", "-0.1000000000000000001"], ["", ""], ["B", -2]],
    }
    policy = {
        "version": 1,
        "name": "=HYPERLINK(<script>)",
        "rules": [{"rule": "in_range", "column": "value", "minimum": 0, "max_violations": limit}],
    }
    return json.loads(
        web.run(
            json.dumps(payload),
            context()["address"],
            json.dumps(policy),
            source_format="excel-range",
        )
    )


def test_context_views_share_exact_bounded_diagnostics_and_provenance():
    original = live_result()
    old = json.loads(original["artifact_json"])
    stamped = json.loads(web.excel_evidence(original["artifact_json"], json.dumps(context())))
    assert stamped["ok"] is True
    artifact = json.loads(stamped["artifact_json"])
    assert artifact["input"]["excel"] == context()
    assert {k: v for k, v in artifact.items() if k != "input"} == {
        k: v for k, v in old.items() if k != "input"
    }
    embedded = re.search(r'id="finassert-report">(.*?)</script>', stamped["html"], re.S)
    assert embedded and json.loads(embedded[1]) == artifact
    rows, _ = results_sheet(artifact)
    pairs = {row[0]: row[1] for row in rows if row[0].startswith("Excel ")}
    assert pairs["Excel data row count"] == 2
    assert pairs["Excel physical data row count"] == 3
    assert pairs["Excel snapshot sha256"] == context()["snapshot_sha256"]
    assert pairs["Excel verified at"] == context()["verified_at"]
    assert "violations: 2 total; example cap 1; 1 shown; truncated: True" in stamped["html"]
    samples = [
        json.loads(row[4]) for row in rows if isinstance(row[4], str) and row[4].startswith("{")
    ]
    canonical = artifact["report"]["results"][0]["diagnostics"]
    assert samples == next(c["observations"] for c in canonical if c["kind"] == "violations")
    assert samples[0]["value"] == "-0.1000000000000000001"
    assert "<script>" not in stamped["html"]
    assert any(row[0] == "Policy" and row[1].startswith("'=HYPERLINK") for row in rows)


def test_live_views_do_not_apply_a_second_hidden_example_cap():
    result = live_result(limit=51, values=[["key", "value"], *[[f"K{i}", -1] for i in range(55)]])
    stamped = json.loads(
        web.excel_evidence(
            result["artifact_json"],
            json.dumps(context(data_row_count=55, physical_data_row_count=55)),
        )
    )
    assert stamped["ok"]
    assert stamped["html"].count("<pre>") == 51
    rows, _ = results_sheet(json.loads(stamped["artifact_json"]))
    assert sum(row[4].startswith("{") for row in rows) == 51


@pytest.mark.parametrize(
    "changes",
    [
        {"schema_version": 2},
        {"schema_version": True},
        {"hidden_rows": "visible_only"},
        {"date_system": "auto"},
        {"date_system_source": "guess"},
        {"header_row": True},
        {"data_row_count": 4},
        {"physical_data_row_count": 0},
        {"column_count": 1.5},
        {"header_row": 1048576},
        {"snapshot_sha256": "sha256:unknown"},
        {"captured_at": "2026-11-15"},
        {"captured_at": "2026-11-15Z"},
        {"verified_at": "2026-11-15T09:00:00Z"},
        {"worksheet_id": ""},
        {"table_id": "not-a-table"},
        {"kind": "table"},
        {"values": [["unbounded"]]},
    ],
)
def test_invalid_or_unbounded_context_is_rejected(changes):
    with pytest.raises(ValueError):
        parse_context(context(**changes))


def test_table_context_requires_both_id_and_name_and_is_detached():
    raw = context(kind="table", table_id="table-1", table_name="Positions")
    parsed = parse_context(raw)
    raw["table_name"] = "changed"
    assert parsed["table_name"] == "Positions"


def test_file_artifacts_and_mismatched_locators_do_not_gain_live_provenance():
    file_result = json.loads(
        web.run("value\n-1\n", "input.csv", json.dumps({"version": 1, "rules": []}))
    )
    assert "excel" not in json.loads(file_result["artifact_json"])["input"]
    assert not json.loads(web.excel_evidence(file_result["artifact_json"], json.dumps(context())))[
        "ok"
    ]
    assert not json.loads(
        web.excel_evidence(
            live_result()["artifact_json"], json.dumps(context(address="other!A1:A3"))
        )
    )["ok"]
