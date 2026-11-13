import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pandas as pd
import pytest

import finassert as fa
from finassert.core.models import DiagnosticCollection, ValidationReport, ValidationResult
from finassert.reporting import artifact_to_json, build_artifact, to_json


@pytest.mark.parametrize("policy", ["fail", "skip"])
@pytest.mark.parametrize("cap", [0, 2, 20])
def test_missing_diagnostics_keep_full_count_with_bounded_rows(policy: str, cap: int) -> None:
    report = fa.check(
        {"weight": [None] * 100},
        [fa.weights_sum_to_one(null_policy=policy, max_violations=cap)],
    )
    result = report.results[0]
    assert len(result.metadata["missing_rows"]) == cap
    (diagnostic,) = result.diagnostics
    assert diagnostic.kind == "missing_rows"
    assert diagnostic.count == 100 and diagnostic.limit == cap and diagnostic.truncated
    assert len(diagnostic.observations) == cap
    assert json.loads(to_json(report))["results"][0]["diagnostics"][0] == diagnostic.to_dict()


def test_invalid_rows_and_violations_have_independent_totals() -> None:
    report = fa.check(
        {"v": [None] * 7 + [-1] * 10}, [fa.non_negative(column="v", max_violations=2)]
    )
    groups = {item.kind: item for item in report.results[0].diagnostics}
    assert groups["invalid_rows"].count == 7
    assert groups["violations"].count == 10
    assert all(len(item.observations) == 2 and item.truncated for item in groups.values())


def test_composite_and_nan_labels_produce_deterministic_strict_json() -> None:
    frame = pd.DataFrame({"v": [-1, -2]}, index=[("book", Decimal("1.20")), float("nan")])
    report = fa.check(frame, [fa.non_negative(column="v")])
    text = to_json(report)
    parsed = json.loads(text, parse_constant=lambda value: pytest.fail(f"non-JSON {value}"))
    diagnostics = {item["kind"]: item for item in parsed["results"][0]["diagnostics"]}
    rows = diagnostics["violations"]["observations"]
    assert rows == [{"row": ["book", "1.20"], "value": -1}, {"row": "NaN", "value": -2}]
    assert to_json(report) == text


@pytest.mark.parametrize(
    "value,expected",
    [(float("nan"), "NaN"), (float("inf"), "Infinity"), (-float("inf"), "-Infinity")],
)
def test_nonfinite_custom_observations_remain_explicit(value: float, expected: str) -> None:
    result = ValidationResult(
        "test.value", "Value", fa.Outcome.FAILED, fa.Severity.ERROR, "bad", observed=value
    )
    assert json.loads(to_json(ValidationReport((result,))))["results"][0]["observed"] == expected


def test_artifact_context_is_versioned_and_timestamp_is_explicit() -> None:
    report = fa.check({"weight": [1]}, [fa.weights_sum_to_one()])
    artifact = build_artifact(
        report, input_sheet="Positions", generated_at=datetime(2026, 11, 13, tzinfo=UTC)
    )
    assert artifact["schema_version"] == 1
    assert artifact["input"]["sheet"] == "Positions"
    assert artifact["generated_at"] == "2026-11-13T00:00:00Z"
    assert artifact_to_json(artifact) == artifact_to_json(artifact)
    with pytest.raises(ValueError, match="timezone-aware"):
        build_artifact(report, generated_at=datetime(2026, 11, 13))


def test_all_outcomes_and_custom_metadata_survive_artifact_roundtrip() -> None:
    results = tuple(
        ValidationResult(
            "test." + outcome.value,
            outcome.value,
            outcome,
            fa.Severity.ERROR,
            "message",
            observed=Decimal("0.0100"),
            metadata={"object": complex(1, 2)},
        )
        for outcome in fa.Outcome
    )
    payload = json.loads(artifact_to_json(build_artifact(ValidationReport(results))))["report"]
    assert payload["counts_by_outcome"] == {"passed": 1, "failed": 1, "error": 1, "skipped": 1}
    assert all(item["observed"] == "0.0100" for item in payload["results"])
    assert all(item["metadata"]["object"] == "(1+2j)" for item in payload["results"])


def test_invalid_diagnostic_totals_are_rejected() -> None:
    with pytest.raises(ValueError):
        DiagnosticCollection("rows", 0, 1, ({"row": 1},))


def test_artifact_and_text_match_reviewable_all_outcome_fixtures() -> None:
    report = fa.check(
        {"weight": [Decimal("1.0000")], "v": [-1], "blank": [None]},
        [
            fa.weights_sum_to_one(tolerance=0),
            fa.non_negative(column="v"),
            fa.non_negative(column="absent"),
            fa.weights_sum_to_one(column="blank", null_policy="skip"),
        ],
    )
    artifact = build_artifact(
        report,
        input_locator="synthetic.json",
        input_format="json",
        generated_at=datetime(2026, 11, 13, tzinfo=UTC),
    )
    folder = Path(__file__).parents[1] / "fixtures" / "reports"
    assert artifact_to_json(artifact) + "\n" == (folder / "all-outcomes-v1.json").read_text()
    assert report.summary() + "\n" == (folder / "all-outcomes.txt").read_text()
