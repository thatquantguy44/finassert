from copy import deepcopy
from datetime import date, timedelta
from decimal import Decimal

import pandas as pd
import pytest

import finassert as fa
from finassert.core import Outcome
from finassert.policy import PolicyError, dump_policy, parse_policy, parse_policy_text


def config(**overrides):
    return {
        "period_start": "start",
        "period_end": "end",
        "group_by": ["entity", "vintage", "scenario"],
        "currency": "ccy",
        "expected_scope": [
            {"entity": "A", "vintage": "2026-09-30", "scenario": "base", "ccy": "USD"}
        ],
        "first_period": "2026-10-01",
        "periods": 3,
        "row_key": "id",
        **overrides,
    }


def rows():
    return [
        {
            "id": f"week-{n}",
            "entity": "A",
            "vintage": "2026-09-30",
            "scenario": "base",
            "ccy": "USD",
            "start": (date(2026, 10, 1) + timedelta(days=n * 7)).isoformat(),
            "end": (date(2026, 10, 8) + timedelta(days=n * 7)).isoformat(),
            "open": Decimal(100 + n * 10),
            "close": Decimal(110 + n * 10),
        }
        for n in range(3)
    ]


def coverage(**overrides):
    return fa.forecast_coverage(**config(**overrides))


def continuity(**overrides):
    return fa.cash_continuity(opening_cash="open", closing_cash="close", **config(**overrides))


def result(data, rule):
    return fa.check(data, [rule]).results[0]


def test_passes_all_input_adapters_without_mutation():
    data = rows()
    before = deepcopy(data)
    for source in (data, {key: [r[key] for r in data] for key in data[0]}, pd.DataFrame(data)):
        report = fa.check(source, [coverage(), continuity()], raise_on_error=True)
        assert report.passed
        assert report.results[1].metadata["checked_count"] == 2
    assert data == before


def test_missing_whole_group_and_empty_data_never_pass():
    scope = [
        *config()["expected_scope"],
        {"entity": "B", "vintage": "2026-09-30", "scenario": "base", "ccy": "EUR"},
    ]
    observed = result(rows(), coverage(expected_scope=scope))
    assert observed.outcome is Outcome.FAILED
    assert observed.metadata["violation_count"] == 3
    assert all(v["group"]["entity"] == "B" for v in observed.metadata["violations"])
    assert result([], coverage()).metadata["violation_count"] == 3
    assert result([], continuity()).outcome is Outcome.ERROR


@pytest.mark.parametrize(
    "edit,reason",
    [
        (lambda data: data.pop(1), "missing_period"),
        (lambda data: data.append({**data[0], "id": "copy"}), "duplicate_period"),
        (lambda data: data[0].update(end="2026-10-10"), "invalid_period_end"),
        (lambda data: data[0].update(start="2026-10-02"), "unexpected_period"),
        (lambda data: data[0].update(start="2026-02-30"), "invalid_period"),
        (lambda data: data[0].update(start="20261001"), "invalid_period"),
        (lambda data: data[0].update(start=None), "invalid_period"),
        (lambda data: data[0].update(ccy="EUR"), "unexpected_scope"),
        (lambda data: data[0].update(entity=[]), "invalid_scope"),
        (lambda data: data[0].update(id="week-1"), "duplicate_row_identity"),
        (lambda data: data[0].update(id=" "), "invalid_row_identity"),
    ],
)
def test_structural_breaks_fail_coverage_and_error_continuity(edit, reason):
    data = rows()
    edit(data)
    observed = result(data, coverage())
    assert observed.outcome is Outcome.FAILED
    assert reason in [v["reason"] for v in observed.metadata["violations"]]
    broken = result(data, continuity())
    assert broken.outcome is Outcome.ERROR and broken.metadata["checked_count"] == 0


def test_cash_break_is_deterministic_exact_and_labels_both_rows():
    data = rows()
    data[1]["open"] += Decimal("0.01")
    observed = result(data, continuity())
    assert observed.outcome is Outcome.FAILED
    assert result(list(reversed(data)), continuity()) == observed
    (failure,) = observed.metadata["violations"]
    assert failure["row"] == "week-1" and failure["previous_row"] == "week-0"
    assert failure["difference"] == Decimal("0.01")
    assert observed.to_dict()["metadata"]["violations"][0]["difference"] == "0.01"
    assert result(data, continuity(tolerance=Decimal("0.01"))).passed
    assert not result(data, continuity(tolerance=Decimal("0.009"))).passed


def test_relative_tolerance_and_negative_cash():
    data = rows()
    for row in data:
        row["open"] *= -1
        row["close"] *= -1
    data[1]["open"] -= Decimal("1")
    assert result(data, continuity(tolerance=fa.Tolerance(relative=Decimal("0.01")))).passed
    assert not result(data, continuity()).passed


def test_currencies_vintages_entities_and_scenarios_are_isolated():
    data = rows()
    scope = config()["expected_scope"]
    for field, value in [
        ("ccy", "EUR"),
        ("vintage", "2026-09-29"),
        ("entity", "B"),
        ("scenario", "downside"),
    ]:
        data += [
            {
                **row,
                field: value,
                "id": row["id"] + field,
                "open": row["open"] + 100,
                "close": row["close"] + 100,
            }
            for row in rows()
        ]
        scope.append({**scope[0], field: value})
    assert result(data, continuity(expected_scope=scope)).passed


@pytest.mark.parametrize(
    "value",
    [None, "", True, "100", float("inf"), float("nan"), Decimal("Infinity"), Decimal("NaN")],
)
def test_unusable_cash_never_passes_including_uncompared_endpoints(value):
    for index, column in [(0, "open"), (-1, "close"), (1, "open")]:
        data = rows()
        data[index][column] = value
        assert result(data, continuity()).outcome is Outcome.FAILED


def test_only_blank_cash_can_skip_and_structure_never_skips():
    data = rows()
    data[0]["open"] = None
    assert result(data, continuity(null_policy="skip")).outcome is Outcome.SKIPPED
    data[1]["open"] = True
    assert result(data, continuity(null_policy="skip")).outcome is Outcome.FAILED
    assert result(data[:-1], continuity(null_policy="skip")).outcome is Outcome.ERROR


def test_diagnostic_caps_count_all_failures_and_zero_cap_does_not_pass():
    for rule in (coverage(max_violations=0), continuity(max_violations=1)):
        observed = result([], rule)
        assert observed.metadata["violation_count"] == 3
        assert len(observed.metadata["violations"]) == rule.max_violations
        assert observed.metadata["violations_truncated"] and not observed.passed


def test_one_week_requires_valid_schedule_and_balances():
    observed = result(rows()[:1], continuity(periods=1))
    assert observed.passed and observed.metadata["checked_count"] == 0


def test_missing_column_is_engine_error():
    data = rows()
    del data[0]["close"]
    assert result(data, continuity()).outcome is Outcome.ERROR


@pytest.mark.parametrize(
    "overrides",
    [
        {"expected_scope": []},
        {"expected_scope": [{"entity": "A"}]},
        {
            "expected_scope": [
                {"entity": "A", "vintage": "2026-09-30", "scenario": "base", "ccy": "usd"}
            ]
        },
        {"periods": 0},
        {"periods": True},
        {"periods": 100001},
        {"first_period": "2026-02-30"},
        {"first_period": "9999-12-31"},
        {"group_by": "entity"},
        {"group_by": ["ccy"]},
        {"max_violations": -1},
        {"max_violations": True},
        {"period_end": "start"},
    ],
)
def test_invalid_configuration_rejected_before_evaluation(overrides):
    with pytest.raises(ValueError):
        coverage(**overrides)


def test_scope_is_copied_and_duplicate_scopes_rejected():
    scope = config()["expected_scope"]
    rule = coverage(expected_scope=scope)
    scope[0]["entity"] = "changed"
    assert result(rows(), rule).passed
    with pytest.raises(ValueError, match="duplicate"):
        coverage(expected_scope=scope * 2)
    with pytest.raises(ValueError, match="exceeds"):
        coverage(expected_scope=[{**scope[0], "entity": str(i)} for i in range(2)], periods=60000)
    with pytest.raises(ValueError, match="null_policy"):
        continuity(null_policy="ignore")


def test_policy_parity_roundtrip_and_mapping_validation():
    policy = parse_policy(
        {
            "version": 1,
            "rules": [
                {"rule": "forecast_coverage", **config()},
                {
                    "rule": "treasury.cash_continuity",
                    "opening_cash": "open",
                    "closing_cash": "close",
                    **config(),
                },
            ],
        }
    )
    direct = fa.check(rows(), [coverage(), continuity()])
    assert policy.check(rows()) == direct
    reloaded = parse_policy_text(dump_policy(policy), format="yaml")
    assert reloaded.digest == policy.digest and reloaded.check(rows()) == direct
    for invalid in ([], "not JSON", [{"entity": 123}], [{"bad": "keys"}]):
        with pytest.raises(PolicyError):
            parse_policy(
                {
                    "version": 1,
                    "rules": [
                        {"rule": "forecast_coverage", **config(expected_scope=invalid)},
                    ],
                }
            )


def test_warning_failure_keeps_existing_severity_semantics():
    data = rows()
    data[1]["open"] += 1
    report = fa.check(data, [continuity(severity="warning")])
    assert report.passed and len(report.warnings) == 1


def test_leap_anchor_is_a_calendar_week():
    data = rows()[:1]
    data[0].update(start="2024-02-29", end="2024-03-07")
    assert result(data, coverage(first_period="2024-02-29", periods=1)).passed
