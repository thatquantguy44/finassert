from decimal import Decimal

from hypothesis import given
from hypothesis import strategies as st

import finassert as fa


@given(
    st.lists(
        st.decimals(min_value=0, max_value=1, places=6, allow_nan=False, allow_infinity=False),
        min_size=1,
        max_size=25,
    )
)
def test_normalized_decimal_allocations_sum_to_one(weights: list[Decimal]) -> None:
    total = sum(weights)
    if total == 0:
        return
    normalized = [weight / total for weight in weights]

    report = fa.check(
        {"weight": normalized},
        [fa.weights_sum_to_one(tolerance=Decimal("1e-24"))],
    )

    assert report.passed


_amounts = st.decimals(min_value=-10_000, max_value=10_000, places=2)


@st.composite
def cash_ledgers(draw: st.DrawFn) -> dict[str, list[object]]:
    """Transaction rows for several portfolios whose balances roll forward."""
    rows: dict[str, list[object]] = {
        key: [] for key in ("portfolio", "seq", "open", "in", "out", "close")
    }
    for portfolio in range(draw(st.integers(min_value=1, max_value=4))):
        balance = draw(_amounts)
        for seq in range(draw(st.integers(min_value=1, max_value=5))):
            inflow, outflow = draw(_amounts.map(abs)), draw(_amounts.map(abs))
            closing = balance + inflow - outflow
            for key, value in (
                ("portfolio", f"P{portfolio}"),
                ("seq", seq),
                ("open", balance),
                ("in", inflow),
                ("out", outflow),
                ("close", closing),
            ):
                rows[key].append(value)
            balance = closing
    return rows


def _cash_rule() -> fa.Rule:
    return fa.cash_reconciles(
        outflow_sign="positive",
        opening_cash="open",
        inflows="in",
        outflows="out",
        closing_cash="close",
        group_by=["portfolio"],
        grain="transactions",
        order_by="seq",
    )


@given(cash_ledgers(), st.randoms(use_true_random=False))
def test_consistent_ledgers_reconcile_in_any_row_order(
    ledger: dict[str, list[object]], random: object
) -> None:
    order = list(range(len(ledger["seq"])))
    random.shuffle(order)  # type: ignore[attr-defined]
    shuffled = {key: [values[index] for index in order] for key, values in ledger.items()}

    assert fa.check(ledger, [_cash_rule()]).passed
    assert fa.check(shuffled, [_cash_rule()]).passed


@given(cash_ledgers(), st.data())
def test_breaking_one_balance_fails_exactly_that_portfolio(
    ledger: dict[str, list[object]], data: st.DataObject
) -> None:
    portfolios = sorted(set(ledger["portfolio"]), key=str)
    broken = data.draw(st.sampled_from(portfolios))
    last = max(index for index, name in enumerate(ledger["portfolio"]) if name == broken)
    ledger["close"][last] = ledger["close"][last] + Decimal("0.01")  # type: ignore[operator]

    result = fa.check(ledger, [_cash_rule()]).results[0]
    assert [group["group"] for group in result.metadata["failed_groups"]] == [{"portfolio": broken}]


@given(
    st.dictionaries(
        st.sampled_from(["F1", "F2", "F3"]),
        st.lists(_amounts, min_size=1, max_size=6),
        min_size=1,
    )
)
def test_nav_equal_to_the_sum_of_market_values_reconciles(
    funds: dict[str, list[Decimal]],
) -> None:
    rows = [
        (fund, value, sum(values, Decimal(0))) for fund, values in funds.items() for value in values
    ]
    data = {
        "fund": [fund for fund, _, _ in rows],
        "mv": [value for _, value, _ in rows],
        "nav": [nav for _, _, nav in rows],
    }
    rule = fa.nav_reconciles(market_value="mv", nav="nav", group_by=["fund"])
    assert fa.check(data, [rule]).passed


_quantities = st.decimals(min_value=-1_000_000, max_value=1_000_000, places=4)
_prices = st.decimals(min_value=0, max_value=100_000, places=6)


@given(st.lists(st.tuples(_quantities, _prices, st.integers(1, 100)), min_size=1, max_size=20))
def test_exact_products_always_reconcile_with_no_tolerance(
    rows: list[tuple[Decimal, Decimal, int]],
) -> None:
    data = {
        "qty": [qty for qty, _, _ in rows],
        "price": [price for _, price, _ in rows],
        "mult": [mult for _, _, mult in rows],
        "mv": [qty * price * mult for qty, price, mult in rows],
    }

    report = fa.check(
        data,
        [
            fa.market_value_reconciles(
                quantity="qty", price="price", market_value="mv", multiplier="mult"
            )
        ],
    )

    assert report.passed


@given(st.lists(st.decimals(min_value=-5, max_value=5, places=4), min_size=1, max_size=20))
def test_gross_exposure_is_never_below_absolute_net_exposure(values: list[Decimal]) -> None:
    gross = sum(abs(v) for v in values)
    net = sum(values)
    data = {"w": values}

    gross_at_own_level = fa.check(data, [fa.gross_within_limit(value="w", maximum=gross)])
    just_below = fa.check(
        data, [fa.gross_within_limit(value="w", maximum=gross - Decimal("0.0001"))]
    )
    net_inside = fa.check(data, [fa.net_within_limit(value="w", minimum=net, maximum=net)])

    assert gross_at_own_level.passed  # limits are inclusive
    assert not just_below.passed
    assert net_inside.passed
    assert gross >= abs(net)


@given(st.lists(st.decimals(min_value=-5, max_value=5, places=4), min_size=1, max_size=20))
def test_position_limit_at_the_largest_position_passes_and_below_fails(
    values: list[Decimal],
) -> None:
    largest = max(abs(v) for v in values)
    data = {"w": values}

    assert fa.check(data, [fa.position_within_limit(value="w", maximum=largest)]).passed
    if largest > 0:
        below = fa.position_within_limit(value="w", maximum=largest - Decimal("0.0001"))
        assert not fa.check(data, [below]).passed
