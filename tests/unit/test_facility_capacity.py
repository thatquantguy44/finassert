from copy import deepcopy
from decimal import Decimal

import pandas as pd
import pytest
from test_treasury import config, rows

import finassert as fa


def data():
    return [
        {
            **row,
            "facility": "revolver",
            "draws": Decimal("10"),
            "repayments": Decimal("0"),
            "commitment": Decimal("140"),
            "unavailable": Decimal("0"),
            "maturity": "2028-01-01",
        }
        for row in rows()
    ]


def configuration(**overrides):
    cfg = config()
    cfg["expected_scope"] = [{**scope, "facility": "revolver"} for scope in cfg["expected_scope"]]
    return {**cfg, **overrides}


def rule(**overrides):
    return fa.facility_capacity(
        facility_id="facility",
        opening_drawn="open",
        draws="draws",
        repayments="repayments",
        closing_drawn="close",
        commitment="commitment",
        unavailable_amount="unavailable",
        maturity_date="maturity",
        **configuration(**overrides),
    )


def result(records, **overrides):
    return fa.check(records, [rule(**overrides)], raise_on_error=True).results[0]


def test_principal_identity_and_capacity_all_adapters_without_mutation():
    records = data()
    before = deepcopy(records)
    for source in (
        records,
        pd.DataFrame(records),
        {k: [r[k] for r in records] for k in records[0]},
    ):
        observed = result(source)
        assert observed.passed
        assert observed.metadata["balances"][-1]["headroom"] == Decimal("10")
    assert result(list(reversed(records))) == result(records)
    assert records == before


def test_exact_capacity_and_reductions_preserve_negative_headroom():
    records = data()
    records[0]["unavailable"] = Decimal("30")
    assert result(records).passed
    records[0]["unavailable"] += Decimal("0.01")
    observed = result(records)
    assert observed.metadata["violations"][0]["reason"] == "capacity_exceeded"
    assert observed.metadata["balances"][0]["headroom"] == Decimal("-0.01")
    assert result(records, tolerance=Decimal("0.01")).passed


def test_identity_and_unavailable_amount_are_independent_failures():
    records = data()
    records[0]["close"] += Decimal("0.01")
    records[1]["unavailable"] = Decimal("141")
    observed = result(records)
    assert {v["reason"] for v in observed.metadata["violations"]} == {
        "principal_identity",
        "unavailable_exceeds_commitment",
        "capacity_exceeded",
        "facility_discontinuity",
    }


@pytest.mark.parametrize("cap", [0, 1, 2])
def test_diagnostic_caps_never_hide_counts(cap):
    records = data()
    for row in records:
        row["commitment"] = 0
    observed = result(records, max_violations=cap)
    assert observed.outcome is fa.Outcome.FAILED
    assert observed.metadata["violation_count"] == 3
    assert len(observed.metadata["violations"]) == cap
    assert observed.metadata["balance_count"] == 3
    assert len(observed.metadata["balances"]) == cap
    assert observed.metadata["violations_truncated"]


@pytest.mark.parametrize(
    "column", ["open", "draws", "repayments", "close", "commitment", "unavailable"]
)
@pytest.mark.parametrize("value", [-1, None, True, "10", Decimal("NaN"), Decimal("Infinity")])
def test_invalid_components_never_pass(column, value):
    records = data()
    records[0][column] = value
    assert result(records).outcome is fa.Outcome.FAILED


@pytest.mark.parametrize(
    "edit", [lambda r: r.pop(), lambda r: r.clear(), lambda r: r.append({**r[0], "id": "copy"})]
)
def test_coverage_preconditions_error(edit):
    records = data()
    edit(records)
    observed = result(records)
    assert observed.outcome is fa.Outcome.ERROR
    assert observed.metadata["checked_count"] == 0


def test_continuity_checks_both_row_identities_and_tolerance():
    records = data()
    records[1]["open"] += Decimal("0.01")
    records[1]["draws"] -= Decimal("0.01")  # Within-period principal still balances.
    observed = result(records)
    assert observed.metadata["continuity_checked_count"] == 2
    assert observed.metadata["violation_count"] == 1
    violation = observed.metadata["violations"][0]
    assert violation["reason"] == "facility_discontinuity"
    assert violation["row"] == "week-1" and violation["previous_row"] == "week-0"
    assert violation["difference"] == Decimal("0.01")
    assert result(records, tolerance=Decimal("0.01")).passed
    assert result(list(reversed(records))) == observed


@pytest.mark.parametrize("maturity", ["2026-09-30", "2026-10-01", "2026-10-08"])
def test_matured_facilities_require_zero_draws_and_closing(maturity):
    records = data()
    for row in records:
        row["maturity"] = maturity
    observed = result(records)
    reasons = [v["reason"] for v in observed.metadata["violations"]]
    count = 4 if maturity == "2026-10-08" else 6
    assert observed.metadata["violation_count"] == count
    assert set(reasons) == {"draw_after_maturity", "balance_after_maturity"}
    for row in records:
        row.update(open=0, close=0, draws=0, repayments=0)
    assert result(records).passed


@pytest.mark.parametrize("maturity", ["2026-10-04", "not-a-date", "2026-02-30", None])
def test_intraperiod_or_invalid_maturity_errors_even_with_no_reported_examples(maturity):
    records = data()
    records[0]["maturity"] = maturity
    observed = result(records, max_violations=0)
    assert observed.outcome is fa.Outcome.ERROR
    assert observed.metadata["checked_count"] == 0
    assert observed.metadata["violation_count"] == 1
    assert observed.metadata["violations"] == []


def test_maturity_exactly_at_final_end_does_not_assume_a_future_period():
    records = data()
    for row in records:
        row["maturity"] = records[-1]["end"]
    assert result(records).passed


def test_facilities_and_currencies_are_isolated():
    records = data()
    second = [{**r, "id": r["id"] + "-2", "facility": "second", "ccy": "EUR"} for r in records]
    second[1]["open"] += 1
    second[1]["draws"] -= 1
    scope = [
        *configuration()["expected_scope"],
        {**configuration()["expected_scope"][0], "facility": "second", "ccy": "EUR"},
    ]
    observed = result([*records, *second], expected_scope=scope)
    assert observed.metadata["violation_count"] == 1
    assert observed.metadata["violations"][0]["group"]["facility"] == "second"
    assert observed.metadata["violations"][0]["group"]["ccy"] == "EUR"


def test_facility_policy_round_trip_strictness_and_null_skip():
    from finassert.policy import PolicyError, dump_policy, parse_policy, parse_policy_text

    entry = {
        "rule": "facility_capacity",
        "facility_id": "facility",
        "opening_drawn": "open",
        "draws": "draws",
        "repayments": "repayments",
        "closing_drawn": "close",
        "commitment": "commitment",
        "unavailable_amount": "unavailable",
        "maturity_date": "maturity",
        **configuration(),
    }
    policy = parse_policy({"version": 1, "rules": [entry]})
    assert policy.check(data()) == fa.check(data(), [rule()])
    assert parse_policy_text(dump_policy(policy), format="yaml").digest == policy.digest
    for patch in ({"facility_id": "ccy"}, {"null_policy": "ignore"}, {"unknown": True}):
        with pytest.raises(PolicyError):
            parse_policy({"version": 1, "rules": [{**entry, **patch}]})
    records = data()
    records[0]["draws"] = None
    assert result(records, null_policy="skip").outcome is fa.Outcome.SKIPPED
    records[0]["draws"] = Decimal("NaN")
    assert result(records, null_policy="skip").outcome is fa.Outcome.FAILED
