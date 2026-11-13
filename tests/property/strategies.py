"""Finite cents, at most four groups and twenty records; no external state."""

from hypothesis import strategies as st

amounts = st.decimals(min_value=-10_000, max_value=10_000, places=2)


@st.composite
def cash_ledgers(draw: st.DrawFn) -> dict[str, list[object]]:
    """Transaction rows for several portfolios whose balances roll forward."""
    rows: dict[str, list[object]] = {
        key: [] for key in ("portfolio", "seq", "open", "in", "out", "close")
    }
    for portfolio in range(draw(st.integers(min_value=1, max_value=4))):
        balance = draw(amounts)
        for seq in range(draw(st.integers(min_value=1, max_value=5))):
            inflow, outflow = draw(amounts.map(abs)), draw(amounts.map(abs))
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


fund_values = st.dictionaries(
    st.sampled_from(["F1", "F2", "F3"]),
    st.lists(amounts, min_size=1, max_size=6),
    min_size=1,
)
nullable_amounts = st.lists(st.one_of(st.none(), amounts), min_size=1, max_size=20)


@st.composite
def duplicated_labels(draw: st.DrawFn) -> list[str]:
    """At most twenty labels, with a guaranteed duplicate and stable order."""
    labels = draw(st.lists(st.sampled_from(["row-A", "row-B", "row-C"]), min_size=1, max_size=19))
    return [*labels, labels[0]]
