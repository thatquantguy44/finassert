from decimal import Decimal
from typing import Any

import pytest

import finassert as fa
from finassert.core.models import Outcome, Severity
from finassert.loaders import parse_csv


def only(data: Any, rule: Any) -> fa.ValidationResult:
    return fa.check(data, [rule]).results[0]


# in_range --------------------------------------------------------------------


def test_in_range_lists_each_value_outside_with_the_side_and_distance() -> None:
    data = {"cash": [0.02, 0.5, -0.01, 1.2], "ticker": ["A", "B", "C", "D"]}
    rule = fa.in_range(column="cash", minimum=0, maximum=1, row_key="ticker")

    result = only(data, rule)

    assert result.outcome is Outcome.FAILED
    assert result.metadata["violations"] == [
        {"row": "C", "value": -0.01, "reason": "below_minimum", "limit": 0, "beyond": 0.01},
        {
            "row": "D",
            "value": 1.2,
            "reason": "above_maximum",
            "limit": 1,
            "beyond": pytest.approx(0.2),
        },
    ]
    assert result.message == (
        "Column 'cash' has 2 value(s) outside the allowed range and "
        "0 blank or non-numeric value(s)."
    )


def test_in_range_limits_are_inclusive_and_tolerance_widens_them() -> None:
    data = parse_csv("w\n0\n1\n1.01\n-0.01\n")

    exact = only(data, fa.in_range(column="w", minimum=0, maximum=Decimal("1")))
    loose = only(
        data, fa.in_range(column="w", minimum=0, maximum=Decimal("1"), tolerance=Decimal("0.01"))
    )

    assert [v["row"] for v in exact.metadata["violations"]] == [4, 5]
    assert loose.outcome is Outcome.PASSED  # 1.01 and -0.01 are exactly on the widened limits


def test_in_range_one_sided_limits() -> None:
    assert only({"w": [5, 50]}, fa.in_range(column="w", minimum=5)).outcome is Outcome.PASSED
    assert only({"w": [5, 50]}, fa.in_range(column="w", maximum=10)).outcome is Outcome.FAILED


def test_in_range_blanks_and_non_numeric_values() -> None:
    data = {"w": [0.5, None, "abc", "  "]}

    failed = only(data, fa.in_range(column="w", minimum=0, maximum=1))
    ignored = only(data, fa.in_range(column="w", minimum=0, maximum=1, null_policy="ignore"))
    skipped = only({"w": [0.5, None]}, fa.in_range(column="w", minimum=0, null_policy="skip"))

    assert failed.metadata["invalid_rows"] == [1, 2, 3]
    assert ignored.metadata["invalid_rows"] == [2]  # text still fails; blanks are left out
    assert skipped.outcome is Outcome.SKIPPED


def test_in_range_severity_is_recorded_and_a_warning_does_not_fail_the_report() -> None:
    report = fa.check({"w": [2]}, [fa.in_range(column="w", maximum=1, severity="warning")])

    assert report.results[0].severity is Severity.WARNING
    assert report.passed and len(report.warnings) == 1


@pytest.mark.parametrize(
    "arguments",
    [
        {},
        {"minimum": 2, "maximum": 1},
        {"maximum": float("nan")},
        {"maximum": 1, "tolerance": fa.Tolerance(relative=0.1)},
        {"maximum": 1, "max_violations": -1},
    ],
)
def test_in_range_rejects_invalid_configuration(arguments: dict[str, Any]) -> None:
    with pytest.raises(ValueError):
        fa.in_range(column="w", **arguments)


# weights_match_market_values ----------------------------------------------------


def book() -> dict[str, list[Any]]:
    return {
        "portfolio": ["A", "A", "B", "B"],
        "ticker": ["X", "Y", "X", "Y"],
        "weight": [0.6, 0.4, 0.5, 0.3],
        "mv": [600, 400, 625, 375],
        "nav": [1000, 1000, 1000, 1000],
    }


def test_weights_match_market_values_against_nav_names_the_stale_rows() -> None:
    rule = fa.weights_match_market_values(
        weight="weight", market_value="mv", nav="nav", group_by=["portfolio"],
        row_key="ticker", tolerance=0.0001,
    )  # fmt: skip

    result = only(book(), rule)

    assert result.outcome is Outcome.FAILED
    assert result.message == "1 of 2 group(s) have weights that do not match their market values."
    (failure,) = result.metadata["failed_groups"]
    assert failure["group"] == {"portfolio": "B"}
    assert failure["base"] == 1000
    assert [(m["row"], m["weight"], m["expected"]) for m in failure["mismatches"]] == [
        ("X", 0.5, 0.625),
        ("Y", 0.3, 0.375),
    ]
    assert result.metadata["equation"] == "weight = market_value / nav"


def test_without_a_nav_the_base_is_the_groups_total_market_value() -> None:
    data = book()
    data["weight"] = [0.6, 0.4, 0.625, 0.375]
    rule = fa.weights_match_market_values(
        weight="weight", market_value="mv", group_by=["portfolio"], tolerance=0.0001
    )

    result = only(data, rule)

    assert result.outcome is Outcome.PASSED
    assert result.metadata["equation"] == "weight = market_value / sum(market_value)"


def test_weights_tolerance_is_inclusive_and_exact_for_decimals() -> None:
    data = parse_csv("weight,mv,nav\n0.2501,250,1000\n")

    def run(tolerance: str) -> Outcome:
        rule = fa.weights_match_market_values(
            weight="weight", market_value="mv", nav="nav", tolerance=Decimal(tolerance)
        )
        return only(data, rule).outcome

    assert run("0.0001") is Outcome.PASSED
    assert run("0.00009") is Outcome.FAILED


@pytest.mark.parametrize(
    ("nav", "reason"),
    [([0, 0, 0, 0], "base_not_positive"), ([None, None, 1000, 1000], "no_base")],
)
def test_an_unusable_base_fails_the_group_instead_of_dividing(nav: list[Any], reason: str) -> None:
    data = book()
    data["nav"] = nav
    rule = fa.weights_match_market_values(
        weight="weight", market_value="mv", nav="nav", group_by=["portfolio"], tolerance=0.1
    )

    result = only(data, rule)

    assert result.metadata["failed_groups"][0]["reason"] == reason


def test_a_zero_or_negative_total_market_value_fails_without_a_nav() -> None:
    rule = fa.weights_match_market_values(weight="weight", market_value="mv")

    result = only({"weight": [0.5, 0.5], "mv": [100, -100]}, rule)

    assert result.metadata["failed_groups"][0]["reason"] == "base_not_positive"


def test_weights_match_blank_values_fail_or_skip_and_are_never_zero() -> None:
    data = book()
    data["weight"][0] = None
    rule = fa.weights_match_market_values(
        weight="weight", market_value="mv", nav="nav", group_by=["portfolio"]
    )
    skip = fa.weights_match_market_values(
        weight="weight", market_value="mv", nav="nav", group_by=["portfolio"], null_policy="skip"
    )

    assert only(data, rule).outcome is Outcome.FAILED
    assert only(data, skip).outcome is Outcome.SKIPPED


# drift_within_band -----------------------------------------------------------------


def holdings() -> dict[str, list[Any]]:
    return {
        "portfolio": ["A", "A", "A", "B", "B"],
        "ticker": ["X", "Y", "Z", "X", "Y"],
        "weight": [0.45, 0.35, 0.20, 0.5, 0.5],
        "target": [0.40, 0.40, 0.20, 0.5, 0.5],
    }


def test_drift_defaults_to_warning_severity() -> None:
    rule = fa.drift_within_band(weight="weight", target_weight="target", band=0.04)

    assert rule.severity is Severity.WARNING
    assert (
        fa.drift_within_band(
            weight="weight", target_weight="target", band=0.04, severity="error"
        ).severity
        is Severity.ERROR
    )


def test_drift_lists_positions_beyond_the_band_and_a_warning_does_not_fail_the_run() -> None:
    rule = fa.drift_within_band(
        weight="weight", target_weight="target", band=0.04,
        group_by=["portfolio"], row_key="ticker",
    )  # fmt: skip

    report = fa.check(holdings(), [rule])

    (result,) = report.results
    assert result.outcome is Outcome.FAILED and result.severity is Severity.WARNING
    assert report.passed and len(report.warnings) == 1
    (failure,) = result.metadata["failed_groups"]
    assert failure["group"] == {"portfolio": "A"}
    assert failure["reason"] == "drift_above_band"
    assert [(b["row"], b["target"]) for b in failure["breaches"]] == [("X", 0.4), ("Y", 0.4)]
    assert failure["breaches"][0]["drift"] == pytest.approx(0.05)


def test_drift_band_is_inclusive() -> None:
    data = parse_csv("weight,target\n0.45,0.40\n0.35,0.40\n")
    rule = fa.drift_within_band(weight="weight", target_weight="target", band=Decimal("0.05"))

    assert only(data, rule).outcome is Outcome.PASSED


def test_total_drift_limit_sums_absolute_drifts() -> None:
    rule = fa.drift_within_band(
        weight="weight", target_weight="target", total_limit=0.09, group_by=["portfolio"]
    )

    result = only(holdings(), rule)

    (failure,) = result.metadata["failed_groups"]
    assert failure["reason"] == "total_drift_above_limit"
    assert failure["total_drift"] == pytest.approx(0.10)
    assert failure["total_limit"] == 0.09


@pytest.mark.parametrize(
    "arguments",
    [{}, {"band": -0.1}, {"total_limit": float("inf")}, {"band": 0.1, "null_policy": "ignore"}],
)
def test_drift_rejects_invalid_configuration(arguments: dict[str, Any]) -> None:
    with pytest.raises(ValueError):
        fa.drift_within_band(weight="weight", target_weight="target", **arguments)


def test_drift_blank_target_fails_and_is_not_zero() -> None:
    data = holdings()
    data["target"][2] = None
    rule = fa.drift_within_band(
        weight="weight", target_weight="target", band=0.5, group_by=["portfolio"]
    )

    result = only(data, rule)

    assert result.outcome is Outcome.FAILED
    assert result.metadata["unusable_rows"] == [{"row": 2, "blank": ["target_weight"]}]


# turnover_within_limit -------------------------------------------------------------


def trades() -> dict[str, list[Any]]:
    return {
        "portfolio": ["A", "A", "A", "B", "B"],
        "ticker": ["X", "Y", "Z", "X", "Y"],
        "weight": [0.5, 0.3, 0.2, 0.5, 0.5],
        "previous": [0.4, 0.3, 0.3, 0.5, 0.5],
    }


def test_one_way_turnover_is_half_the_absolute_changes() -> None:
    rule = fa.turnover_within_limit(
        weight="weight", previous_weight="previous", maximum=0.1, sides="one_way",
        group_by=["portfolio"], row_key="ticker",
    )  # fmt: skip

    result = only(trades(), rule)

    assert result.outcome is Outcome.PASSED  # (0.1 + 0 + 0.1) / 2 = 0.1, inclusive
    assert result.metadata["equation"] == "sum(abs(weight - previous_weight)) / 2"


def test_two_way_turnover_is_the_full_sum_and_names_the_largest_changes() -> None:
    rule = fa.turnover_within_limit(
        weight="weight", previous_weight="previous", maximum=0.15, sides="two_way",
        group_by=["portfolio"], row_key="ticker",
    )  # fmt: skip

    result = only(trades(), rule)

    (failure,) = result.metadata["failed_groups"]
    assert failure["group"] == {"portfolio": "A"}
    assert failure["observed"] == pytest.approx(0.2)
    assert [c["row"] for c in failure["largest_changes"][:2]] == ["X", "Z"]
    assert result.metadata["equation"] == "sum(abs(weight - previous_weight))"


def test_turnover_sides_has_no_default() -> None:
    with pytest.raises(TypeError):
        fa.turnover_within_limit(weight="w", previous_weight="p", maximum=0.1)  # type: ignore[call-arg]
    with pytest.raises(ValueError):
        fa.turnover_within_limit(weight="w", previous_weight="p", maximum=0.1, sides="both")


def test_a_blank_previous_weight_is_not_a_new_position() -> None:
    data = trades()
    data["previous"][1] = None
    rule = fa.turnover_within_limit(
        weight="weight",
        previous_weight="previous",
        maximum=1,
        sides="one_way",
        group_by=["portfolio"],
    )

    result = only(data, rule)

    assert result.outcome is Outcome.FAILED
    assert result.metadata["unusable_rows"] == [{"row": 1, "blank": ["previous_weight"]}]


def test_turnover_is_exact_for_decimals() -> None:
    data = parse_csv("weight,previous\n0.3000,0.1\n0.7000,0.9\n")

    at_limit = fa.turnover_within_limit(
        weight="weight", previous_weight="previous", maximum=Decimal("0.2"), sides="one_way"
    )
    below = fa.turnover_within_limit(
        weight="weight", previous_weight="previous", maximum=Decimal("0.1999"), sides="one_way"
    )

    assert only(data, at_limit).outcome is Outcome.PASSED
    assert only(data, below).outcome is Outcome.FAILED


@pytest.mark.parametrize("maximum", [-0.1, float("nan")])
def test_turnover_rejects_invalid_limits(maximum: float) -> None:
    with pytest.raises(ValueError):
        fa.turnover_within_limit(weight="w", previous_weight="p", maximum=maximum, sides="one_way")


# position_rolls_forward ------------------------------------------------------------


def blotter(**overrides: Any) -> dict[str, list[Any]]:
    data: dict[str, list[Any]] = {
        "portfolio": ["A", "A", "B"],
        "ticker": ["X", "Y", "X"],
        "open": [100, 50, 10],
        "buys": [20, 0, 5],
        "sells": [30, 10, 0],
        "close": [90, 40, 15],
    }
    data.update(overrides)
    return data


def rolls(**overrides: Any) -> Any:
    arguments: dict[str, Any] = {
        "sell_sign": "positive",
        "opening_quantity": "open",
        "buys": "buys",
        "sells": "sells",
        "closing_quantity": "close",
        "group_by": ["portfolio", "ticker"],
    }
    arguments.update(overrides)
    return fa.position_rolls_forward(**arguments)


def test_positions_roll_forward_and_the_equation_states_the_sign_convention() -> None:
    result = only(blotter(), rolls())

    assert result.outcome is Outcome.PASSED
    assert result.metadata["equation"] == "closing_quantity = opening_quantity + buys - sells"
    assert result.metadata["sell_sign"] == "positive"


def test_a_break_names_the_position_and_the_difference() -> None:
    result = only(blotter(close=[90, 45, 15]), rolls())

    (failure,) = result.metadata["failed_groups"]
    assert failure["group"] == {"portfolio": "A", "ticker": "Y"}
    assert (failure["observed"], failure["expected"], failure["difference"]) == (45, 40, 5)
    assert failure["reason"] == "does_not_roll_forward"
    assert failure["rows"] == [1]


def test_negative_sells_are_added_and_the_wrong_convention_breaks_the_file() -> None:
    data = blotter(sells=[-30, -10, 0])

    assert only(data, rolls(sell_sign="negative")).outcome is Outcome.PASSED
    assert only(data, rolls(sell_sign="positive")).outcome is Outcome.FAILED


def test_adjustments_are_added_for_splits_and_transfers() -> None:
    data = blotter(close=[290, 40, 15], adj=[200, 0, 0])

    plain = only(data, rolls())
    adjusted = only(data, rolls(adjustments="adj"))

    assert plain.outcome is Outcome.FAILED
    assert adjusted.outcome is Outcome.PASSED
    assert adjusted.metadata["equation"].endswith("+ adjustments")


def test_the_sell_sign_is_a_hard_requirement_with_no_default() -> None:
    with pytest.raises(TypeError):
        fa.position_rolls_forward(  # type: ignore[call-arg]
            opening_quantity="open", buys="buys", sells="sells",
            closing_quantity="close", group_by=["ticker"],
        )  # fmt: skip
    with pytest.raises(ValueError):
        rolls(sell_sign="both")
    with pytest.raises(ValueError):
        rolls(sell_sign=None)


def test_positions_must_be_identified_by_group_columns() -> None:
    with pytest.raises(ValueError, match="identify each position"):
        rolls(group_by=[])
    with pytest.raises(TypeError):
        rolls(group_by="ticker")


def test_rows_of_one_position_must_agree() -> None:
    data = blotter(
        close=[90, 40, 15, 91], portfolio=["A", "A", "B", "A"], ticker=["X", "Y", "X", "X"]
    )
    for column in ("open", "buys", "sells"):
        data[column] = [*data[column], data[column][0]]

    result = only(data, rolls())

    (failure,) = result.metadata["failed_groups"]
    assert failure["reason"] == "inconsistent_rows"


def test_roll_forward_tolerance_blanks_and_ignore() -> None:
    data = parse_csv("p,open,buys,sells,close\nA,1.5,0.25,0.5,1.26\n")
    kwargs = {
        "opening_quantity": "open", "buys": "buys", "sells": "sells",
        "closing_quantity": "close", "group_by": ["p"], "sell_sign": "positive",
    }  # fmt: skip

    assert only(data, fa.position_rolls_forward(**kwargs)).outcome is Outcome.FAILED
    assert only(data, fa.position_rolls_forward(tolerance=Decimal("0.01"), **kwargs)).outcome is (
        Outcome.PASSED
    )
    blank = blotter(buys=[20, None, 5])
    assert only(blank, rolls()).outcome is Outcome.FAILED
    assert only(blank, rolls(null_policy="skip")).outcome is Outcome.SKIPPED
    with pytest.raises(ValueError, match="ignore"):
        rolls(null_policy="ignore")
