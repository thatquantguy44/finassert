from copy import deepcopy
from dataclasses import FrozenInstanceError
from decimal import Decimal

import pandas as pd
import pytest
from test_treasury import config, rows

import finassert as fa
from finassert.policy import PolicyError, dump_policy, parse_policy, parse_policy_text


def data():
    return [{**row, "restricted": Decimal("10"), "minimum": row["close"] - 10} for row in rows()]


def rule(**overrides):
    return fa.minimum_cash_buffer(
        closing_cash="close",
        restricted_cash="restricted",
        minimum_buffer="minimum",
        **config(**overrides),
    )


def result(records, **overrides):
    return fa.check(records, [rule(**overrides)], raise_on_error=True).results[0]


def test_boundary_and_all_adapters_preserve_inputs_and_configuration():
    records = data()
    before = deepcopy(records)
    for source in (
        records,
        pd.DataFrame(records),
        {k: [r[k] for r in records] for k in records[0]},
    ):
        assert result(source).passed
    assert records == before
    with pytest.raises(FrozenInstanceError):
        rule().closing_cash = "changed"
    assert result(list(reversed(records))) == result(records)


@pytest.mark.parametrize("cap", [0, 1, 20])
def test_actual_shortfalls_include_tolerated_amounts_and_complete_counts(cap):
    records = data()
    records[0]["close"] -= Decimal("0.01")
    records[1]["restricted"] += Decimal("0.02")
    observed = result(records, tolerance=Decimal("0.01"), max_violations=cap)
    assert observed.outcome is fa.Outcome.FAILED
    assert observed.metadata["violation_count"] == 1
    assert observed.metadata["shortfall_count"] == 2
    assert len(observed.metadata["shortfalls"]) == min(cap, 2)
    assert observed.metadata["shortfalls_truncated"] == (cap < 2)
    if cap:
        assert observed.metadata["shortfalls"][0]["shortfall"] == Decimal("0.01")
        assert observed.metadata["shortfalls"][0]["within_tolerance"]
        assert observed.metadata["violations"][0]["row"] == "week-1"


def test_tolerated_shortfall_passes_but_is_visible_in_json_and_diagnostics():
    records = data()
    records[0]["close"] -= Decimal("0.01")
    observed = result(records, tolerance=Decimal("0.01"))
    assert observed.passed
    assert observed.to_dict()["metadata"]["shortfalls"][0]["shortfall"] == "0.01"
    assert any(d.kind == "cash_shortfalls" and d.count == 1 for d in observed.diagnostics)


def test_restricted_cash_and_negative_closing_remain_a_deficit():
    records = data()
    records[0].update(close=Decimal("-1"), restricted=Decimal("10"), minimum=0)
    violation = result(records).metadata["violations"][0]
    assert violation["observed"] == Decimal("-11")
    assert violation["shortfall"] == Decimal("11")


@pytest.mark.parametrize("column", ["close", "restricted", "minimum"])
@pytest.mark.parametrize("value", [None, True, "10", Decimal("NaN"), float("inf")])
def test_unusable_amounts_never_pass(column, value):
    records = data()
    records[0][column] = value
    assert result(records).outcome is fa.Outcome.FAILED
    expected = fa.Outcome.SKIPPED if value is None else fa.Outcome.FAILED
    assert result(records, null_policy="skip").outcome is expected


@pytest.mark.parametrize("column", ["restricted", "minimum"])
def test_negative_component_is_invalid_even_with_tolerance(column):
    records = data()
    records[0][column] = Decimal("-0.01")
    assert result(records, tolerance=1).outcome is fa.Outcome.FAILED


@pytest.mark.parametrize(
    "edit", [lambda r: r.pop(), lambda r: r.clear(), lambda r: r.append({**r[0], "id": "copy"})]
)
def test_missing_or_duplicate_coverage_errors(edit):
    records = data()
    edit(records)
    assert result(records).outcome is fa.Outcome.ERROR


def test_currencies_cannot_offset_and_large_decimal_difference_is_exact():
    records = data()
    eur = [
        {**r, "id": r["id"] + "-eur", "ccy": "EUR", "close": Decimal("1e40"), "minimum": 0}
        for r in records
    ]
    records[0].update(close=Decimal("1e40"), restricted=Decimal("0.01"), minimum=Decimal("1e40"))
    scope = [*config()["expected_scope"], {**config()["expected_scope"][0], "ccy": "EUR"}]
    observed = result([*records, *eur], expected_scope=scope)
    assert observed.metadata["violation_count"] == 1
    assert observed.metadata["violations"][0]["shortfall"] == Decimal("0.01")
    assert observed.metadata["violations"][0]["group"]["ccy"] == "USD"


def test_policy_round_trip_and_strict_parameters():
    entry = {
        "rule": "minimum_cash_buffer",
        "closing_cash": "close",
        "restricted_cash": "restricted",
        "minimum_buffer": "minimum",
        **config(),
    }
    policy = parse_policy({"version": 1, "rules": [entry]})
    assert policy.check(data()) == fa.check(data(), [rule()])
    assert parse_policy_text(dump_policy(policy), format="yaml").check(data()) == policy.check(
        data()
    )
    for patch in ({"minimum_buffer": None}, {"null_policy": "ignore"}, {"typo": 1}):
        with pytest.raises(PolicyError):
            parse_policy({"version": 1, "rules": [{**entry, **patch}]})
