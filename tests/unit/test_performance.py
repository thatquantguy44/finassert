"""Acceptance coverage for monthly performance preflight and reference math."""

from __future__ import annotations

import csv
import json
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from openpyxl import load_workbook

from finassert import monthly_performance_reference
from finassert.cli import main as cli_main
from finassert.policy import PolicyError, parse_policy
from finassert.reporting import artifact_to_json, build_artifact, render_artifact_html

FIXTURES = Path(__file__).parents[2] / "specs" / "0020" / "artifacts" / "fixtures"
EXPECTED = json.loads((FIXTURES / "expected.json").read_text())
NUMERIC_COLUMNS = {
    "strategy_return",
    "benchmark_return",
    "reported_strategy_cumulative",
    "reported_benchmark_cumulative",
}


def _rows(name: str) -> list[dict[str, Any]]:
    with (FIXTURES / name).open(newline="") as source:
        rows = list(csv.DictReader(source))
    for row in rows:
        for column in NUMERIC_COLUMNS.intersection(row):
            if row[column] != "":
                row[column] = Decimal(row[column])
            else:
                row[column] = None
    return rows


def _call(
    rows: list[dict[str, Any]],
    *,
    start: str = "2024-01-31",
    end: str = "2024-12-31",
    unit: str = "fraction",
    max_violations: int = 20,
):
    return monthly_performance_reference(
        rows,
        period_end="period_end",
        strategy_return="strategy_return",
        benchmark_return="benchmark_return",
        window_start=start,
        window_end=end,
        return_unit=unit,
        row_key="source_row_id",
        max_violations=max_violations,
    )


def _issue_codes(result) -> set[str]:
    return {issue.code for issue in result.issues}


def _policy_document(**overrides: Any) -> dict[str, Any]:
    parameters: dict[str, Any] = {
        "period_end": "period_end",
        "strategy_return": "strategy_return",
        "benchmark_return": "benchmark_return",
        "reported_strategy_cumulative": "reported_strategy_cumulative",
        "reported_benchmark_cumulative": "reported_benchmark_cumulative",
        "window_start": "2024-01-31",
        "window_end": "2024-12-31",
        "periodic_return_unit": "fraction",
        "reported_return_unit": "fraction",
        "strategy_id": "strategy-demo",
        "benchmark_id": "benchmark-demo",
        "base_currency": "usd",
        "valuation_convention": "calendar month-end total return",
        "strategy_fee_treatment": "net of management and transaction costs",
        "benchmark_fee_treatment": "gross of fees",
        "tolerance": "0.0001",
        "row_key": "source_row_id",
    }
    parameters.update(overrides)
    return {
        "version": 1,
        "name": "Monthly performance audit",
        "rules": [{"rule": "monthly_performance_audit", **parameters}],
    }


def _audit_policy(**overrides: Any):
    return parse_policy(_policy_document(**overrides))


def test_out_of_order_2024_fixture_matches_every_independent_period_value() -> None:
    rows = _rows(EXPECTED["annual_2024"]["source"])
    result = _call(rows)

    expected_periods = EXPECTED["annual_2024"]["expected_by_period"]
    assert result.available
    assert [period.period_end.isoformat() for period in result.periods] == [
        item["period_end"] for item in expected_periods
    ]
    for period, expected in zip(result.periods, expected_periods, strict=True):
        assert period.source_row == expected["source_row_id"]
        assert period.active_return == Decimal(expected["active_return"])
        assert period.strategy_cumulative_return == Decimal(expected["strategy_cumulative"])
        assert period.benchmark_cumulative_return == Decimal(expected["benchmark_cumulative"])
    assert result.periods[0].source_position == rows.index(
        next(row for row in rows if row["source_row_id"] == result.periods[0].source_row)
    )

    summary = result.summary
    assert summary is not None
    for field, value in EXPECTED["annual_2024"]["summary"].items():
        if value is not None:
            assert (
                getattr(summary, field) == Decimal(value)
                if field != "complete_months"
                else summary.complete_months == value
            )


@pytest.mark.parametrize("period_end", ["2024-01-31", "2024-06-30", "2024-12-31"])
def test_missing_boundary_or_interior_month_blocks_full_window(period_end: str) -> None:
    rows = [
        row for row in _rows("monthly_returns_2024_seeded.csv") if row["period_end"] != period_end
    ]

    result = _call(rows)

    assert not result.available
    assert result.periods == ()
    assert "missing_period" in _issue_codes(result)
    assert any(
        issue.period_end.isoformat() == period_end for issue in result.issues if issue.period_end
    )


def test_duplicate_month_blocks_without_selecting_a_row() -> None:
    rows = _rows("monthly_returns_2024_seeded.csv")
    duplicate = next(row.copy() for row in rows if row["period_end"] == "2024-06-30")
    duplicate["source_row_id"] = "duplicate-june"
    rows.append(duplicate)

    result = _call(rows)

    assert not result.available
    assert result.periods == ()
    assert result.issue_counts["duplicate_period"] == 2
    duplicate_issues = [issue for issue in result.issues if issue.code == "duplicate_period"]
    assert {issue.source_row for issue in duplicate_issues} == {"src-2024-06", "duplicate-june"}


def test_extra_month_is_reported_and_blocks_metrics() -> None:
    rows = _rows("monthly_returns_2024_seeded.csv")
    rows.append(
        {
            "source_row_id": "extra",
            "period_end": "2023-12-31",
            "strategy_return": Decimal("0"),
            "benchmark_return": Decimal("0"),
        }
    )

    result = _call(rows)

    assert not result.available
    assert "outside_window" in _issue_codes(result)
    issue = next(issue for issue in result.issues if issue.code == "outside_window")
    assert (issue.source_row, issue.period_end.isoformat()) == ("extra", "2023-12-31")


@pytest.mark.parametrize("column", ["strategy_return", "benchmark_return"])
def test_blank_returns_block_and_preserve_the_source_row(column: str) -> None:
    rows = _rows("monthly_returns_2024_seeded.csv")
    target = next(row for row in rows if row["period_end"] == "2024-06-30")
    target[column] = None

    result = _call(rows)

    assert not result.available
    issue = next(issue for issue in result.issues if issue.code == "blank_return")
    assert (issue.source_row, issue.field, issue.period_end.isoformat()) == (
        "src-2024-06",
        column,
        "2024-06-30",
    )


def test_invalid_period_and_missing_expected_period_are_both_reported() -> None:
    rows = _rows("monthly_returns_2024_seeded.csv")
    target = next(row for row in rows if row["period_end"] == "2024-03-31")
    target["period_end"] = "2024-03-30"

    result = _call(rows)

    assert not result.available
    assert {"invalid_period", "missing_period"}.issubset(_issue_codes(result))
    invalid = next(issue for issue in result.issues if issue.code == "invalid_period")
    assert (invalid.source_row, invalid.source_position) == (
        "src-2024-03",
        rows.index(target),
    )


@pytest.mark.parametrize(
    "value", [Decimal("-1"), Decimal("-1.1"), Decimal("NaN"), "not-a-number", True]
)
def test_invalid_or_nonfinite_return_blocks_the_reference(value: Any) -> None:
    rows = _rows("monthly_returns_2024_seeded.csv")
    next(row for row in rows if row["period_end"] == "2024-06-30")["strategy_return"] = value

    result = _call(rows)

    assert not result.available
    assert {"invalid_return", "return_at_or_below_minus_100_percent"} & _issue_codes(result)


def test_zero_return_is_valid_and_not_treated_as_blank() -> None:
    rows = _rows("monthly_returns_2024_seeded.csv")
    next(row for row in rows if row["period_end"] == "2024-05-31")["strategy_return"] = Decimal("0")

    result = _call(rows)

    assert result.available
    assert result.periods[4].strategy_return == Decimal("0")


def test_issue_examples_are_bounded_but_counts_cover_the_complete_scan() -> None:
    rows = _rows("monthly_returns_2024_seeded.csv")[:5]

    result = _call(rows, max_violations=2)

    assert not result.available
    assert len(result.issues) == 2
    assert result.issue_count == sum(result.issue_counts.values())
    assert result.issues_truncated
    assert result.max_violations == 2
    assert json.loads(json.dumps(result.to_dict(), allow_nan=False))["issues_truncated"]


def test_three_month_hand_case_matches_linking_and_tracking_error() -> None:
    case = EXPECTED["three_month_hand_case"]
    result = _call(
        _rows(case["source"]),
        start="2024-01-31",
        end="2024-03-31",
    )

    assert result.available
    assert [period.active_return for period in result.periods] == [
        Decimal(value) for value in case["active_returns"]
    ]
    assert [period.strategy_cumulative_return for period in result.periods] == [
        Decimal(value) for value in case["strategy_cumulative_by_period"]
    ]
    assert [period.benchmark_cumulative_return for period in result.periods] == [
        Decimal(value) for value in case["benchmark_cumulative_by_period"]
    ]
    assert result.summary is not None
    assert result.summary.annualized_geometric_unavailable_reason == (
        "fewer_than_12_complete_months"
    )
    assert result.summary.annualized_tracking_error == Decimal(
        case["summary"]["annualized_tracking_error_decimal_50dp"]
    )


def test_percent_and_fraction_three_month_fixtures_normalize_identically() -> None:
    fraction = _call(
        _rows("monthly_returns_3m_hand_case.csv"),
        start="2024-01-31",
        end="2024-03-31",
    )
    percent = _call(
        _rows("monthly_returns_3m_percent.csv"),
        start="2024-01-31",
        end="2024-03-31",
        unit="percent",
    )

    assert fraction.summary is not None and percent.summary is not None
    assert [row.strategy_return for row in fraction.periods] == [
        row.strategy_return for row in percent.periods
    ]
    assert [row.benchmark_return for row in fraction.periods] == [
        row.benchmark_return for row in percent.periods
    ]
    assert fraction.summary == percent.summary


def test_thirteen_month_noninteger_annualization_matches_independent_fixture() -> None:
    case = EXPECTED["thirteen_month_annualization"]
    result = _call(
        _rows(case["source"]),
        start=case["window_start"],
        end=case["window_end"],
    )

    assert result.summary is not None
    assert result.summary.complete_months == case["complete_months"]
    assert result.summary.strategy_cumulative_return == Decimal(case["strategy_cumulative_return"])
    assert result.summary.benchmark_cumulative_return == Decimal(
        case["benchmark_cumulative_return"]
    )
    assert result.summary.strategy_annualized_geometric_return == Decimal(
        case["strategy_annualized_geometric_expected"]
    )
    assert result.summary.benchmark_annualized_geometric_return == Decimal(
        case["benchmark_annualized_geometric_expected"]
    )
    assert result.summary.annualized_tracking_error == Decimal(0)


def test_two_month_identical_active_returns_have_zero_tracking_error() -> None:
    case = EXPECTED["zero_tracking_error_case"]
    result = _call(
        _rows(case["source"]),
        start="2025-01-31",
        end="2025-02-28",
    )

    assert result.summary is not None
    assert result.summary.annualized_tracking_error == Decimal(
        case["summary"]["annualized_tracking_error"]
    )
    assert result.summary.strategy_annualized_geometric_return is None


@pytest.mark.parametrize(
    ("start", "end", "unit"),
    [
        ("2024-01-30", "2024-12-31", "fraction"),
        ("2024-12-31", "2024-01-31", "fraction"),
        ("2024-01-31", "2024-12-31", "decimal"),
    ],
)
def test_invalid_window_or_unit_is_rejected(start: str, end: str, unit: str) -> None:
    with pytest.raises(ValueError):
        _call([], start=start, end=end, unit=unit)


def test_composite_audit_finds_seeded_strategy_tie_out_without_propagating_it() -> None:
    rows = _rows("monthly_returns_2024_seeded.csv")
    policy = _audit_policy()

    report = policy.check(rows)

    assert len(report.results) == 1
    result = report.results[0]
    assert result.rule_id == "performance.monthly_performance_audit"
    assert result.outcome.value == "failed"
    assert (
        result.metadata["reference"]["summary"]["strategy_cumulative_return"]
        == (EXPECTED["annual_2024"]["summary"]["strategy_cumulative_return"])
    )
    assert result.metadata["tie_out"]["tie_out_failure_counts"] == {"strategy_tie_out": 1}
    violations = next(item for item in result.diagnostics if item.kind == "tie_out_violations")
    finding = violations.observations[0]
    assert finding["source_row"] == "src-2024-06"
    assert finding["period_end"] == "2024-06-30"
    assert finding["expected"] == "0.061520150601"
    assert finding["observed"] == "0.071520150601"
    assert finding["difference"] == "0.010000000000"


def test_correcting_seeded_report_value_passes_without_changing_reference_values() -> None:
    rows = _rows("monthly_returns_2024_seeded.csv")
    policy = _audit_policy()
    failing = policy.check(rows).results[0]
    corrected = [row.copy() for row in rows]
    june = next(row for row in corrected if row["period_end"] == "2024-06-30")
    june["reported_strategy_cumulative"] = Decimal("0.061520150601")

    passed = policy.check(corrected).results[0]

    assert passed.outcome.value == "passed"
    assert passed.metadata["reference"] == failing.metadata["reference"]
    assert passed.metadata["tie_out"]["comparison_count"] == 24


def test_composite_audit_ties_out_benchmark_and_preserves_original_row_identity() -> None:
    rows = _rows("monthly_returns_2024_seeded.csv")
    june = next(row for row in rows if row["period_end"] == "2024-06-30")
    june["reported_benchmark_cumulative"] += Decimal("0.01")

    result = _audit_policy().check(rows).results[0]

    assert result.metadata["tie_out"]["tie_out_failure_counts"]["benchmark_tie_out"] == 1
    finding = next(
        item
        for item in next(
            diagnostic
            for diagnostic in result.diagnostics
            if diagnostic.kind == "tie_out_violations"
        ).observations
        if item["code"] == "benchmark_tie_out"
    )
    assert finding["field"] == "reported_benchmark_cumulative"
    assert finding["source_position"] == rows.index(june)
    assert finding["source_row"] == "src-2024-06"


@pytest.mark.parametrize(
    ("delta", "outcome"),
    [
        (Decimal("0.0001"), "passed"),
        (Decimal("0.0001000000000000000000000001"), "failed"),
    ],
)
def test_tie_out_tolerance_is_inclusive_and_uses_exact_decimal(
    delta: Decimal, outcome: str
) -> None:
    rows = _rows("monthly_returns_2024_seeded.csv")
    june = next(row for row in rows if row["period_end"] == "2024-06-30")
    june["reported_strategy_cumulative"] = Decimal("0.061520150601") + delta

    result = _audit_policy().check(rows).results[0]

    assert result.outcome.value == outcome


def test_reported_percent_units_are_normalized_independently() -> None:
    rows = _rows("monthly_returns_3m_percent.csv")
    policy = parse_policy(
        _policy_document(
            window_start="2024-01-31",
            window_end="2024-03-31",
            periodic_return_unit="percent",
            reported_return_unit="percent",
        )
    )

    report = policy.check(rows)
    result = report.results[0]

    assert result.outcome.value == "passed"
    assert result.metadata["reference"]["summary"]["strategy_cumulative_return"] == "0.0098"
    assert result.metadata["reference"]["summary"]["benchmark_cumulative_return"] == "0.0302"
    exported = build_artifact(report, policy=policy)["policy"]["rules"][0]
    assert exported["parameters"]["periodic_return_unit"] == "percent"
    assert exported["effective_parameters"]["periodic_return_unit"] == "percent"


def test_invalid_reported_value_fails_with_bounded_reason_coded_diagnostic() -> None:
    rows = _rows("monthly_returns_2024_seeded.csv")
    next(row for row in rows if row["period_end"] == "2024-06-30")[
        "reported_benchmark_cumulative"
    ] = None
    policy = _audit_policy(max_violations=1)

    result = policy.check(rows).results[0]

    assert result.outcome.value == "failed"
    assert result.metadata["tie_out"]["reported_input_issue_counts"] == {"blank_return": 1}
    diagnostic = next(item for item in result.diagnostics if item.kind == "reported_input_issues")
    assert diagnostic.count == 1
    assert diagnostic.observations[0]["code"] == "blank_return"
    assert diagnostic.observations[0]["field"] == "reported_benchmark_cumulative"


def test_tie_out_diagnostics_are_bounded_and_keep_complete_failure_counts() -> None:
    rows = _rows("monthly_returns_2024_seeded.csv")
    for row in rows:
        row["reported_strategy_cumulative"] = Decimal("1")
        row["reported_benchmark_cumulative"] = Decimal("1")

    result = _audit_policy(max_violations=2).check(rows).results[0]

    diagnostic = next(item for item in result.diagnostics if item.kind == "tie_out_violations")
    assert diagnostic.count == 24
    assert diagnostic.limit == 2
    assert len(diagnostic.observations) == 2
    assert diagnostic.truncated
    assert result.metadata["tie_out"]["tie_out_failure_counts"] == {
        "benchmark_tie_out": 12,
        "strategy_tie_out": 12,
    }


def test_artifact_exports_configured_and_effective_parameters_with_exact_decimals() -> None:
    policy = _audit_policy()
    digest = policy.digest
    report = policy.check(_rows("monthly_returns_2024_seeded.csv"))

    artifact = build_artifact(report, policy=policy)
    rule = artifact["policy"]["rules"][0]
    configured = rule["parameters"]
    effective = rule["effective_parameters"]

    assert "severity" not in configured and "max_violations" not in configured
    assert configured["base_currency"] == "usd"
    assert configured["tolerance"] == "0.0001"
    assert effective["base_currency"] == "USD"
    assert effective["severity"] == "error"
    assert effective["max_violations"] == 20
    assert effective["row_key"] == "source_row_id"
    assert effective["tolerance"] == {"absolute": "0.0001", "relative": 0}
    assert effective["window_start"] == "2024-01-31"
    assert policy.digest == digest
    encoded = artifact_to_json(artifact)
    assert json.loads(encoded)["policy"]["rules"][0]["effective_parameters"] == effective
    html = render_artifact_html(artifact)
    assert "strategy_fee_treatment" in html
    assert "net of management and transaction costs" in html


def test_policy_parameters_remain_in_error_artifacts_and_relative_tolerance_is_rejected() -> None:
    policy = _audit_policy()
    report = policy.check({})
    artifact = build_artifact(report, policy=policy)

    assert report.results[0].outcome.value == "error"
    assert artifact["policy"]["rules"][0]["effective_parameters"]["severity"] == "error"
    assert artifact["policy"]["rules"][0]["parameters"]["strategy_id"] == "strategy-demo"
    with pytest.raises(PolicyError, match="absolute"):
        parse_policy(
            {
                "version": 1,
                "rules": [
                    {
                        **_policy_document()["rules"][0],
                        "tolerance": {"absolute": "0.0001", "relative": "0.01"},
                    }
                ],
            }
        )


def test_all_audit_fields_are_present_in_effective_policy_parameters() -> None:
    policy = _audit_policy()
    rule = policy.describe()["rules"][0]

    assert set(rule["effective_parameters"]) == {
        "period_end",
        "strategy_return",
        "benchmark_return",
        "reported_strategy_cumulative",
        "reported_benchmark_cumulative",
        "window_start",
        "window_end",
        "periodic_return_unit",
        "reported_return_unit",
        "strategy_id",
        "benchmark_id",
        "base_currency",
        "valuation_convention",
        "strategy_fee_treatment",
        "benchmark_fee_treatment",
        "tolerance",
        "row_key",
        "severity",
        "max_violations",
    }


def test_cli_json_html_and_xlsx_exports_retain_the_complete_audit_policy(tmp_path: Path) -> None:
    config = tmp_path / "policy.json"
    config.write_text(json.dumps(_policy_document()))
    json_report = tmp_path / "report.json"
    html_report = tmp_path / "report.html"
    xlsx_report = tmp_path / "report.xlsx"

    exit_code = cli_main(
        [
            "check",
            "--config",
            str(config),
            "--input",
            str(FIXTURES / "monthly_returns_2024_seeded.csv"),
            "--format",
            "csv",
            "--output",
            str(json_report),
            "--html",
            str(html_report),
            "--xlsx",
            str(xlsx_report),
            "--quiet",
        ]
    )

    assert exit_code == 1
    artifact = json.loads(json_report.read_text())
    exported = artifact["policy"]["rules"][0]
    assert exported["parameters"]["base_currency"] == "usd"
    assert exported["effective_parameters"]["base_currency"] == "USD"
    assert exported["effective_parameters"]["tolerance"] == {
        "absolute": "0.0001",
        "relative": 0,
    }
    assert "strategy_fee_treatment" in html_report.read_text()

    workbook = load_workbook(xlsx_report, read_only=True, data_only=True)
    try:
        policy_sheet = workbook["Policy"]
        assert policy_sheet["A9"].value == "performance.monthly_performance_audit"
        xlsx_effective = json.loads(policy_sheet["F9"].value)
        assert xlsx_effective["strategy_id"] == "strategy-demo"
        assert xlsx_effective["max_violations"] == 20
    finally:
        workbook.close()
