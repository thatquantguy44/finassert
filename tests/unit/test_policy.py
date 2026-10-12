from decimal import Decimal
from pathlib import Path

import pytest

import finassert as fa
from finassert.core.models import Outcome
from finassert.policy import (
    ParameterKind,
    ParameterSpec,
    PolicyError,
    RuleCatalog,
    RuleFactorySpec,
    default_catalog,
    dump_policy,
    load_policy,
    parse_policy,
    parse_policy_text,
)
from finassert.rules import WeightsSumToOneRule

VALID = """\
version: 1
name: Daily positions
description: Long-only book
assumptions:
  - One portfolio per file
rules:
  - rule: weights_sum_to_one
    column: weight
    tolerance: "0.0001"
  - rule: non_negative
    column: market_value
    null_policy: ignore
    max_violations: 5
"""


def issues_of(text: str, *, format: str = "yaml") -> list[str]:
    with pytest.raises(PolicyError) as caught:
        parse_policy_text(text, format=format)
    return [str(issue) for issue in caught.value.issues]


def test_valid_policy_resolves_rules_in_order() -> None:
    policy = parse_policy_text(VALID, format="yaml")

    assert policy.name == "Daily positions"
    assert policy.assumptions == ("One portfolio per file",)
    assert [rule.rule_id for rule in policy.rules] == [
        "portfolio.weights_sum_to_one",
        "arithmetic.non_negative",
    ]
    weights = policy.rules[0]
    assert isinstance(weights, WeightsSumToOneRule)
    assert weights.tolerance.absolute == Decimal("0.0001")


def test_policy_results_match_python_api() -> None:
    policy = parse_policy_text(VALID, format="yaml")
    data = {"weight": [0.4, 0.6], "market_value": [10, None, -1]}
    direct = fa.check(
        data,
        [
            fa.weights_sum_to_one(tolerance=Decimal("0.0001")),
            fa.non_negative(column="market_value", null_policy="ignore", max_violations=5),
        ],
    )

    assert policy.check(data) == direct


def test_quoted_and_unquoted_exponent_text_become_decimal() -> None:
    # PyYAML reads unquoted 1e-8 as text; it is accepted as an exact decimal.
    policy = parse_policy_text(
        "version: 1\nrules:\n  - rule: weights_sum_to_one\n    tolerance: 1e-8\n",
        format="yaml",
    )
    assert policy.entries[0].parameters["tolerance"] == Decimal("1e-8")


def test_unquoted_float_stays_float() -> None:
    policy = parse_policy_text(
        "version: 1\nrules:\n  - rule: weights_sum_to_one\n    tolerance: 0.001\n",
        format="yaml",
    )
    assert policy.entries[0].parameters["tolerance"] == 0.001
    assert isinstance(policy.entries[0].parameters["tolerance"], float)


def test_tolerance_mapping_builds_relative_tolerance() -> None:
    policy = parse_policy_text(
        "version: 1\nrules:\n  - rule: weights_sum_to_one\n"
        '    tolerance:\n      relative: "0.01"\n',
        format="yaml",
    )
    rule = policy.rules[0]
    assert isinstance(rule, WeightsSumToOneRule)
    assert rule.tolerance.relative == Decimal("0.01")
    assert rule.tolerance.absolute == 0


def test_rule_may_be_named_by_rule_id() -> None:
    policy = parse_policy(
        {"version": 1, "rules": [{"rule": "arithmetic.non_negative", "column": "x"}]}
    )
    assert policy.entries[0].factory == "non_negative"


def test_empty_rule_list_is_valid_and_passes_vacuously() -> None:
    policy = parse_policy({"version": 1, "rules": []})
    assert policy.check({}).passed


@pytest.mark.parametrize(
    ("document", "expected"),
    [
        ({"rules": []}, "Missing 'version'"),
        ({"version": 2, "rules": []}, "Unsupported version 2"),
        ({"version": True, "rules": []}, "Unsupported version True"),
        ({"version": 1}, "Missing 'rules'"),
        ({"version": 1, "rules": {}}, "'rules' must be a list"),
        ({"version": 1, "rules": ["x"]}, "must be a set of settings"),
        ({"version": 1, "rules": [{"column": "x"}]}, "Missing 'rule'"),
        ({"version": 1, "rules": [{"rule": 3}]}, "'rule' must be the name"),
        ({"version": 1, "rules": [{"rule": "non_negative"}]}, "needs 'column'"),
        ({"version": 1, "name": 3, "rules": []}, "'name' must be text"),
        ({"version": 1, "assumptions": "x", "rules": []}, "must be a list of sentences"),
        ({"version": 1, "assumptions": [1], "rules": []}, "Each assumption must be text"),
        ([], "must be a set of named settings"),
    ],
)
def test_structural_problems_are_reported(document: object, expected: str) -> None:
    with pytest.raises(PolicyError) as caught:
        parse_policy(document)
    assert any(expected in str(issue) for issue in caught.value.issues), caught.value.issues


@pytest.mark.parametrize(
    ("entry", "expected"),
    [
        ({"tolerance": "1,000"}, "not a plain number"),
        ({"tolerance": "5%"}, "not a plain number"),
        ({"tolerance": "NaN"}, "not a plain number"),
        ({"tolerance": float("inf")}, "finite"),
        ({"tolerance": "-1"}, "cannot be negative"),
        ({"tolerance": True}, "must be a number"),
        ({"tolerance": {"absolut": "1"}}, "Did you mean 'absolute'"),
        ({"column": ""}, "column name written as text"),
        ({"column": 5}, "column name written as text"),
        ({"null_policy": "Skip"}, "Did you mean 'skip'"),
        ({"severity": "critical"}, "must be one of: error, warning, info"),
    ],
)
def test_parameter_problems_are_reported(entry: dict[str, object], expected: str) -> None:
    with pytest.raises(PolicyError) as caught:
        parse_policy({"version": 1, "rules": [{"rule": "weights_sum_to_one", **entry}]})
    assert any(expected in str(issue) for issue in caught.value.issues), caught.value.issues


@pytest.mark.parametrize(
    ("entry", "expected"),
    [
        ({"max_violations": -1}, "at least 0"),
        ({"max_violations": 2.5}, "whole number"),
        ({"max_violations": True}, "whole number"),
        ({"tolerance": {"relative": "0.1"}}, "supports only an absolute amount"),
    ],
)
def test_non_negative_parameter_problems(entry: dict[str, object], expected: str) -> None:
    with pytest.raises(PolicyError) as caught:
        parse_policy({"version": 1, "rules": [{"rule": "non_negative", "column": "x", **entry}]})
    assert any(expected in str(issue) for issue in caught.value.issues), caught.value.issues


def test_misspellings_get_suggestions_and_line_numbers() -> None:
    text = (
        "version: 1\n"
        "rule:\n"
        "  - x\n"
        "rules:\n"
        "  - rule: non_negativ\n"
        "    column: x\n"
        "  - rule: weights_sum_to_one\n"
        "    tolerence: 0.1\n"
    )
    found = issues_of(text)

    assert "line 2, rule: Unknown setting 'rule'." in found[0]
    assert "Did you mean 'rules'?" in found[0]
    assert found[1].startswith("line 5, rules[1].rule: Unknown rule 'non_negativ'.")
    assert "Did you mean 'non_negative'?" in found[1]
    assert found[2].startswith("line 8, rules[2].tolerence: Rule 'weights_sum_to_one' has no")
    assert "Did you mean 'tolerance'?" in found[2]


def test_all_problems_are_reported_together() -> None:
    with pytest.raises(PolicyError) as caught:
        parse_policy(
            {
                "version": 1,
                "rules": [
                    {"rule": "weights_sum_to_one", "tolerance": "x"},
                    {"rule": "non_negative"},
                ],
            }
        )
    assert len(caught.value.issues) == 2
    assert "2 problem(s)" in str(caught.value)


def test_duplicate_yaml_keys_are_rejected() -> None:
    found = issues_of("version: 1\nrules: []\nrules: []\n")
    assert found == ["line 3, rules: Setting 'rules' appears more than once."]


def test_duplicate_json_keys_are_rejected() -> None:
    found = issues_of('{"version": 1, "rules": [], "rules": []}', format="json")
    assert "appears more than once" in found[0]


def test_yaml_syntax_errors_name_the_line() -> None:
    found = issues_of("version: 1\nrules: [\n")
    assert found[0].startswith("line 3, policy: The file is not valid YAML")


def test_empty_yaml_file_is_rejected() -> None:
    assert issues_of("") == ["policy: The policy file is empty."]


def test_json_syntax_errors_name_the_line() -> None:
    # A missing colon is located the same way on every supported Python; the
    # position reported for trailing commas changed in Python 3.13.
    found = issues_of('{\n"version": 1,\n"rules" []\n}', format="json")
    assert found[0].startswith("line 3, policy: The file is not valid JSON")


def test_unknown_format_is_rejected() -> None:
    assert "Unknown policy format" in issues_of("", format="toml")[0]


def test_load_policy_infers_format_from_extension(tmp_path: Path) -> None:
    yaml_path = tmp_path / "policy.yaml"
    yaml_path.write_text(VALID, encoding="utf-8")
    json_path = tmp_path / "policy.json"
    json_path.write_text('{"version": 1, "rules": []}', encoding="utf-8")
    other = tmp_path / "policy.txt"
    other.write_text("", encoding="utf-8")

    assert load_policy(yaml_path).name == "Daily positions"
    assert load_policy(json_path).rules == ()
    with pytest.raises(PolicyError, match="Cannot tell the policy format"):
        load_policy(other)


def test_factory_errors_become_policy_issues() -> None:
    def broken(**_: object) -> object:
        raise ValueError("unsupported combination")

    catalog = RuleCatalog()
    catalog.register(
        RuleFactorySpec(
            name="broken",
            rule_id="test.broken",
            title="Broken",
            summary="s",
            rationale="r",
            inappropriate_when="i",
            parameters=(),
            factory=broken,
        )
    )
    with pytest.raises(PolicyError, match="could not be configured: unsupported combination"):
        parse_policy({"version": 1, "rules": [{"rule": "broken"}]}, catalog=catalog)


def test_catalog_rejects_collisions_and_unknown_names() -> None:
    catalog = default_catalog()
    spec = catalog.resolve("non_negative")
    with pytest.raises(ValueError, match="already registered"):
        catalog.register(spec)
    with pytest.raises(ValueError, match="rule_id"):
        catalog.register(
            RuleFactorySpec(
                name="other",
                rule_id=spec.rule_id,
                title="t",
                summary="s",
                rationale="r",
                inappropriate_when="i",
                parameters=(),
                factory=spec.factory,
            )
        )
    catalog.register(spec, replace=True)
    with pytest.raises(KeyError):
        catalog.resolve("missing")
    with pytest.raises(KeyError):
        spec.parameter("missing")


def test_every_built_in_rule_is_fully_documented() -> None:
    catalog = default_catalog()
    assert catalog.names() == ("non_negative", "weights_sum_to_one")
    for spec in catalog.specs():
        for text in (spec.title, spec.summary, spec.rationale, spec.inappropriate_when):
            assert text.strip()
        for parameter in spec.parameters:
            assert parameter.label.strip() and parameter.description.strip()
            assert parameter.required or parameter.default is not None
    described = catalog.to_dict()["rules"]
    assert [item["name"] for item in described] == list(catalog.names())


def test_parameter_spec_serializes_defaults_as_text() -> None:
    spec = ParameterSpec("n", ParameterKind.INTEGER, "N", "d", default=20, minimum=0)
    assert spec.to_dict()["default"] == "20"


@pytest.mark.parametrize(
    "tolerance",
    [1e-8, 0.1, 1e20, 1.5e-300, 0.0, 3, "1E-8", "0.00010", {"absolute": 1e-8, "relative": "0.5"}],
)
def test_dump_policy_round_trips_exactly(tolerance: object) -> None:
    policy = parse_policy(
        {
            "version": 1,
            "name": 'Quotes " and: colons',
            "description": "Ünïcode ✓",
            "assumptions": ["- leading dash", "#hash"],
            "rules": [
                {"rule": "weights_sum_to_one", "column": "Mkt Val (USD)", "tolerance": tolerance}
            ],
        }
    )
    text = dump_policy(policy)
    reloaded = parse_policy_text(text, format="yaml")

    assert reloaded.to_document() == policy.to_document()
    assert type(reloaded.entries[0].parameters["tolerance"]) is type(
        policy.entries[0].parameters["tolerance"]
    )
    assert reloaded.digest == policy.digest
    data = {"Mkt Val (USD)": [0.5, 0.5]}
    assert reloaded.check(data) == policy.check(data)


def test_dump_policy_writes_empty_rule_lists() -> None:
    text = dump_policy(parse_policy({"version": 1, "rules": []}))
    assert "rules: []" in text
    assert parse_policy_text(text, format="yaml").rules == ()


def test_digest_distinguishes_decimal_from_float() -> None:
    as_decimal = parse_policy(
        {"version": 1, "rules": [{"rule": "weights_sum_to_one", "tolerance": "0.1"}]}
    )
    as_float = parse_policy(
        {"version": 1, "rules": [{"rule": "weights_sum_to_one", "tolerance": 0.1}]}
    )
    assert as_decimal.digest != as_float.digest
    assert as_decimal.digest.startswith("sha256:")


def test_describe_includes_plain_language_rule_titles() -> None:
    described = parse_policy_text(VALID, format="yaml").describe()
    assert described["rules"][0]["title"] == "Portfolio weights add up to 100%"
    assert described["assumptions"] == ["One portfolio per file"]


def test_policy_outcomes_are_unchanged_by_loading() -> None:
    report = parse_policy_text(VALID, format="yaml").check({"weight": [1], "market_value": [-1]})
    assert [result.outcome for result in report.results] == [Outcome.PASSED, Outcome.FAILED]


def test_non_utf8_policy_is_a_policy_error(tmp_path: Path) -> None:
    path = tmp_path / "policy.yml"
    path.write_bytes("version: 1\nname: caf\xe9\nrules: []\n".encode("latin-1"))
    with pytest.raises(PolicyError, match="not UTF-8"):
        load_policy(path)


@pytest.mark.parametrize(
    "text",
    [
        "&a [*a]\n",
        "version: 1\nrules: &r []\nname: *r\n",
        "version: 1\nbase: &t {rule: non_negative, column: x}\nrules:\n  - *t\n",
    ],
)
def test_yaml_anchors_and_aliases_are_rejected(text: str) -> None:
    found = issues_of(text)
    assert "anchors and aliases" in found[0]


def test_dump_policy_round_trips_an_empty_tolerance_mapping() -> None:
    policy = parse_policy(
        {"version": 1, "rules": [{"rule": "weights_sum_to_one", "tolerance": {}}]}
    )
    text = dump_policy(policy)
    assert "tolerance: {}" in text
    assert parse_policy_text(text, format="yaml").to_document() == policy.to_document()
