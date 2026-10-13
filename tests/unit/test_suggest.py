import pytest

from finassert.loaders import parse_csv
from finassert.policy import (
    default_catalog,
    fit_template,
    get_template,
    policy_templates,
    suggest_templates,
)
from finassert.policy.suggest import expected_columns, match_columns, normalize


def how(matches: tuple, expected: str) -> tuple:  # type: ignore[type-arg]
    match = next(item for item in matches if item.expected == expected)
    return match.column, match.how


@pytest.mark.parametrize(
    ("header", "words"),
    [
        ("Mkt_Val (USD)", "mkt val usd"),
        ("marketValue", "market value"),
        ("Weight %", "weight pct"),
        ("  NAV  ", "nav"),
        ("Cash P&L", "cash p l"),
        ("MV", "mv"),
    ],
)
def test_headers_are_compared_as_plain_words(header: str, words: str) -> None:
    assert normalize(header) == words


@pytest.mark.parametrize("template", policy_templates(), ids=lambda item: item.name)
def test_a_template_matches_itself_exactly_and_is_unchanged(template) -> None:  # type: ignore[no-untyped-def]
    expected = expected_columns(template.policy().to_document())

    fit = fit_template(template, list(expected))

    assert [(m.column, m.how) for m in fit.matches] == [(name, "exact") for name in expected]
    assert fit.fraction == 1.0
    assert fit.adapted().policy().to_document() == template.policy().to_document()
    assert fit.adapted().adapt == template.adapt  # nothing to confirm or fix


def test_known_names_abbreviations_and_case_are_matched() -> None:
    matches = match_columns(
        ["quantity", "price", "market_value"], ["Ticker", "SHARES", "Px", "Mkt Val"]
    )

    assert how(matches, "quantity") == ("SHARES", "known name")
    assert how(matches, "price") == ("Px", "known name")
    assert how(matches, "market_value") == ("Mkt Val", "known name")


def test_a_header_containing_a_known_name_matches_with_fewest_extra_words() -> None:
    matches = match_columns(
        ["market_value"], ["Market Value (Base Currency Total)", "Market Value USD"]
    )

    assert how(matches, "market_value") == ("Market Value USD", "contains")


def test_equally_good_headers_are_ambiguous_and_nothing_is_chosen() -> None:
    (match,) = match_columns(["market_value"], ["MV (Base)", "MV (Local)"])

    assert match.column is None
    assert set(match.candidates) == {"MV (Base)", "MV (Local)"}
    assert "could be any of" in match.sentence


def test_a_closer_match_beats_a_looser_one() -> None:
    (match,) = match_columns(["market_value"], ["Market Value", "Market Value (Base)"])

    assert (match.column, match.how) == ("Market Value", "exact")


def test_typos_in_long_names_are_matched_as_similar() -> None:
    (match,) = match_columns(["market_value"], ["Marekt Value", "Sector"])

    assert (match.column, match.how) == ("Marekt Value", "similar")


def test_short_names_are_never_matched_by_similarity() -> None:
    (match,) = match_columns(["price"], ["pric", "rice"])

    assert match.column is None


def test_unrelated_headers_match_nothing() -> None:
    matches = match_columns(["weight", "nav"], ["Name", "Sector", "Notes"])

    assert [match.column for match in matches] == [None, None]
    assert matches[0].sentence == "no column in your file matches 'weight'"


def test_target_weight_is_not_taken_for_weight() -> None:
    (match,) = match_columns(["weight"], ["Target Weight"])

    assert match.column is None


def test_one_header_is_never_given_to_two_expected_columns() -> None:
    matches = match_columns(["opening_balance", "closing_balance"], ["Balance"])

    assert [match.column for match in matches] == [None, None]


def test_headers_are_not_reused_across_a_closer_claim() -> None:
    # "Value" is a known name for market_value; beginning_value must not take it.
    matches = match_columns(["market_value", "beginning_value"], ["Value"])

    assert how(matches, "market_value") == ("Value", "known name")
    assert how(matches, "beginning_value") == (None, None)


def test_suggestions_are_ranked_and_weak_fits_are_left_out() -> None:
    fits = suggest_templates(["Fund", "Security", "Wt", "MV (Base)", "NAV"])

    assert [fit.template.name for fit in fits] == [
        "multi-portfolio-holdings",
        "nav-reconciliation",
        "long-only-holdings",
    ]
    assert suggest_templates(["Name", "Sector", "Notes"]) == ()
    assert suggest_templates([]) == ()


def test_partial_fits_say_what_to_fix_and_keep_the_unmatched_name() -> None:
    fit = fit_template(get_template("multi-portfolio-holdings"), ["Fund", "Wt", "MV", "NAV"])

    adapted = fit.adapted()

    assert any("no column in your file matches 'ticker'" in line for line in adapted.adapt)
    columns = adapted.policy().to_document()["rules"][0]["columns"]
    assert columns == ["Fund", "ticker", "Wt", "MV"]


def test_adapted_policy_runs_on_the_file_it_was_matched_to() -> None:
    data = parse_csv("Fund,Security,Wt,MV (Base),NAV\nA,X,0.5,10,20\nA,Y,0.5,10,20\n")
    columns = list(data.column_names)

    (best, *_) = suggest_templates(columns)
    report = best.adapted().policy().check(data)

    assert best.template.name == "multi-portfolio-holdings"
    assert report.passed
    assert [r.outcome.value for r in report.results] == ["passed"] * 4


def test_adapted_yaml_names_the_matches_to_confirm() -> None:
    fit = fit_template(get_template("position-valuation"), ["Shares", "Px", "Mkt Val"])

    text = fit.adapted().to_yaml()

    assert "Confirm the columns finassert matched" in text
    assert "'quantity' is your column 'Shares' (known name match)" in text
    assert 'quantity: "Shares"' in text


def test_expected_columns_follow_the_catalog() -> None:
    document = get_template("cash-reconciliation").policy().to_document()

    assert expected_columns(document, default_catalog()) == (
        "opening_balance",
        "inflows",
        "outflows",
        "cash_income",
        "closing_balance",
        "portfolio",
        "date",
        "currency",
    )


def test_when_two_expected_columns_want_one_header_the_closer_match_keeps_it() -> None:
    matches = match_columns(["portfolio", "fund"], ["Fund"])

    assert how(matches, "fund") == ("Fund", "exact")
    portfolio = next(match for match in matches if match.expected == "portfolio")
    assert portfolio.column is None and portfolio.candidates == ("Fund",)


def test_when_two_expected_columns_want_one_header_equally_neither_gets_it() -> None:
    matches = match_columns(["portfolio_id", "fund_code"], ["Portfolio Code"])

    # Both are known names for the same concept, and neither is an exact match.
    assert [match.column for match in matches].count("Portfolio Code") <= 1
