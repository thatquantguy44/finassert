"""Live-only diagnostic identity resolution; canonical artifacts stay unchanged."""

import json
from dataclasses import replace
from datetime import date
from decimal import Decimal

import pytest

from finassert import nav_reconciles, web
from finassert._excel_navigation import build_navigation
from finassert.core.models import (
    DiagnosticCollection,
    Outcome,
    Severity,
    ValidationReport,
    ValidationResult,
)
from finassert.loaders import TableSource
from finassert.policy import parse_policy


def policy(**parameters):
    return parse_policy(
        {
            "version": 1,
            "rules": [{"rule": "in_range", "column": "value", "minimum": 0, **parameters}],
        }
    )


def targets(navigation):
    return [
        target
        for result in navigation["results"]
        for collection in result["collections"]
        for sample in collection["observations"]
        for target in sample["targets"]
    ]


def test_bridge_retains_physical_gaps_cell_mapping_counts_and_exact_values():
    payload = {
        "values": [["id", "value"], ["first", -1], ["", ""], ["second", -2]],
        "firstRow": 7,
        "date1904": False,
    }
    result = json.loads(
        web.run(
            json.dumps(payload),
            "'O''Brien'!C7:D10",
            json.dumps(
                {
                    "version": 1,
                    "rules": [
                        {"rule": "in_range", "column": "value", "minimum": 0, "max_violations": 1}
                    ],
                }
            ),
            source_format="excel-range",
        )
    )
    nav = result["navigation"]
    assert [(t["row"], t["column_index"]) for t in targets(nav)] == [(8, 1)]
    collection = next(c for c in nav["results"][0]["collections"] if c["kind"] == "violations")
    canonical = next(
        c
        for c in json.loads(result["artifact_json"])["report"]["results"][0]["diagnostics"]
        if c["kind"] == "violations"
    )
    assert {k: collection[k] for k in ("count", "limit", "truncated")} == {
        "count": 2,
        "limit": 1,
        "truncated": True,
    }
    assert [sample["observation"] for sample in collection["observations"]] == canonical[
        "observations"
    ]
    assert "navigation" not in result["artifact_json"]
    assert "navigation" not in json.loads(
        web.run("value\n-1\n", "file.csv", json.dumps(policy().to_document()))
    )


def test_numeric_business_key_is_not_an_excel_row():
    data = TableSource({"key": [999], "value": [-1]}, [8])
    configured = policy(row_key="key")
    target = targets(build_navigation(data, configured, configured.check(data)))[0]
    assert target["label"] == 999
    assert target["row"] == 8


@pytest.mark.parametrize(
    "keys", [["same", "same"], [Decimal("1"), "1"], [date(2026, 1, 1), "2026-01-01"], [1, 1.0]]
)
def test_duplicate_and_serialized_collision_keys_require_rerun(keys):
    data = TableSource({"key": keys, "value": [-1, 1]}, [8, 9])
    configured = policy(row_key="key")
    target = targets(build_navigation(data, configured, configured.check(data)))[0]
    assert target["status"] == "ambiguous"
    assert "rerun" in target["reason"]
    assert "row" not in target


@pytest.mark.parametrize(
    "key,status", [(2**53, "ambiguous"), (float("inf"), "ambiguous"), (None, "unavailable")]
)
def test_unsafe_key_is_not_navigable(key, status):
    data = TableSource({"key": [key], "value": [-1]}, [8])
    configured = policy(row_key="key")
    assert (
        targets(build_navigation(data, configured, configured.check(data)))[0]["status"] == status
    )


def test_groups_only_use_retained_examples_and_missing_periods_have_no_target():
    configured = policy()
    data = TableSource({"value": [-1, -2, -3]}, [8, 9, 10])
    observations = (
        {"group": {"desk": "<script>"}, "rows": [8], "rows_truncated": True},
        {"group": {"desk": "missing"}, "reason": "missing_period"},
    )
    report = ValidationReport(
        (
            ValidationResult(
                "test",
                "Test",
                Outcome.FAILED,
                Severity.ERROR,
                "Group failure",
                diagnostics=(DiagnosticCollection("failed_groups", 10, 2, observations),),
            ),
        )
    )
    nav = build_navigation(data, configured, report)
    samples = nav["results"][0]["collections"][0]["observations"]
    assert [t["row"] for t in targets(nav)] == [8]
    assert samples[0]["targets"][0]["column_index"] is None
    assert samples[1]["targets"] == []
    assert samples[0]["observation"] == observations[0]


def test_invalid_native_target_is_not_guessed():
    configured = policy()
    data = TableSource({"value": [-1]}, [8])
    report = ValidationReport(
        (
            ValidationResult(
                "test",
                "Test",
                Outcome.FAILED,
                Severity.ERROR,
                "Bad row",
                diagnostics=(DiagnosticCollection("violations", 1, 1, ({"row": 99},)),),
            ),
        )
    )
    assert targets(build_navigation(data, configured, report))[0]["status"] == "unavailable"


def test_zero_cap_does_not_reconstruct_findings():
    configured = policy(max_violations=0)
    data = TableSource({"value": [-1, -2]}, [8, 9])
    nav = build_navigation(data, configured, configured.check(data))
    assert targets(nav) == []
    assert (
        next(c for c in nav["results"][0]["collections"] if c["kind"] == "violations")["count"] == 2
    )


def test_group_mapping_resolves_retained_business_labels_before_serialization():
    configured = parse_policy(
        {
            "version": 1,
            "rules": [
                {"rule": "nav_reconciles", "market_value": "mv", "nav": "nav", "group_by": ["desk"]}
            ],
        }
    )
    # The Python factory supports a mapping row key; the pane catalog does not
    # currently expose this setting. Exercise the effective rule, not raw params.
    rule = nav_reconciles(market_value="mv", nav="nav", group_by=["desk"], row_key="key")
    configured = replace(configured, entries=(replace(configured.entries[0], rule=rule),))
    data = TableSource(
        {"desk": ["A", "A"], "key": [999, 888], "mv": [1, 2], "nav": [10, 10]}, [8, 10]
    )
    resolved = targets(build_navigation(data, configured, configured.check(data)))
    assert [(target["label"], target["row"], target["column_index"]) for target in resolved] == [
        (999, 8, None),
        (888, 10, None),
    ]
