from copy import deepcopy
from decimal import Decimal

import pandas as pd
import pytest
from test_treasury import config, rows

import finassert as fa
from finassert.rules.treasury import FacilityCapacityRule, _schedule


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
    cfg = configuration(**overrides)
    schedule = _schedule(
        [*cfg.pop("group_by"), "facility"],
        cfg.pop("currency"),
        cfg.pop("expected_scope"),
        cfg.pop("first_period"),
        cfg.pop("periods"),
    )
    tolerance = cfg.pop("tolerance", fa.Tolerance())
    if not isinstance(tolerance, fa.Tolerance):
        tolerance = fa.Tolerance(absolute=tolerance)
    return FacilityCapacityRule(
        schedule=schedule,
        facility_id="facility",
        opening_drawn="open",
        draws="draws",
        repayments="repayments",
        closing_drawn="close",
        commitment="commitment",
        unavailable_amount="unavailable",
        tolerance=tolerance,
        **cfg,
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
