from decimal import Decimal

import pytest

from finassert.loaders import parse_csv
from finassert.policy import (
    PolicyTemplate,
    default_catalog,
    get_template,
    parse_policy_text,
    policy_templates,
)


@pytest.mark.parametrize("template", policy_templates(), ids=lambda item: item.name)
def test_templates_are_valid_documented_policies(template: PolicyTemplate) -> None:
    policy = template.policy()
    assert policy.assumptions, "templates must state their assumptions"
    assert template.title and template.summary and template.adapt
    names = default_catalog().names()
    assert all(entry.factory in names for entry in policy.entries)


@pytest.mark.parametrize("template", policy_templates(), ids=lambda item: item.name)
def test_template_yaml_reloads_to_the_same_policy(template: PolicyTemplate) -> None:
    text = template.to_yaml()
    assert text.startswith(f"# {template.title} (finassert template '{template.name}')")
    for line in template.adapt:
        assert line in text
    reloaded = parse_policy_text(text, format="yaml")
    assert reloaded.digest == template.policy().digest


def test_long_only_template_catches_short_positions() -> None:
    policy = get_template("long-only-holdings").policy()
    data = parse_csv("weight,market_value\n0.6,600\n0.5,500\n-0.1,-100\n")
    report = policy.check(data)
    assert [result.passed for result in report.results] == [True, False, False]
    assert report.results[1].metadata["violations"] == [{"row": 4, "value": Decimal("-0.1")}]


def test_target_allocation_template_checks_rounding_to_one_basis_point() -> None:
    policy = get_template("target-allocation").policy()
    within = parse_csv("target_weight\n0.3333\n0.3333\n0.3333\n")
    beyond = parse_csv("target_weight\n0.333\n0.333\n0.333\n")
    assert policy.check(within).passed
    assert not policy.check(beyond).passed


def test_templates_are_immutable_and_listed_by_name() -> None:
    names = [template.name for template in policy_templates()]
    assert names == sorted(names)
    template = get_template("target-allocation")
    with pytest.raises(TypeError):
        template.document["version"] = 2  # type: ignore[index]
    document = template.to_dict()["document"]
    document["rules"].clear()
    assert template.policy().rules
    with pytest.raises(KeyError):
        get_template("missing")


def test_cash_template_reconciles_a_daily_cash_file() -> None:
    policy = get_template("cash-reconciliation").policy()
    data = parse_csv(
        "portfolio,date,currency,opening_balance,inflows,outflows,cash_income,closing_balance\n"
        "A,2026-01-02,USD,100.00,25.00,10.00,0.05,115.05\n"
        "A,2026-01-02,EUR,50.00,0,5.00,0,45.02\n"
    )
    failure = policy.check(data).results[0].metadata["failed_groups"]
    assert [item["group"] for item in failure] == [
        {"portfolio": "A", "date": "2026-01-02", "currency": "EUR"}
    ]
    assert failure[0]["rows"] == [3]


def test_nav_template_reconciles_each_fund() -> None:
    policy = get_template("nav-reconciliation").policy()
    data = parse_csv(
        "fund,security,market_value,nav\n"
        "F1,AAA,600.00,1000.00\nF1,BBB,450.00,1000.00\nF1,Fees payable,-50.00,1000.00\n"
        "F2,CCC,99.00,100.00\n"
    )
    result = policy.check(data).results[0]
    assert result.metadata["failed_group_count"] == 1
    assert result.metadata["failed_groups"][0]["group"] == {"fund": "F2"}
