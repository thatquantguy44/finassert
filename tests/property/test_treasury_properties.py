from datetime import date, timedelta
from decimal import Decimal

from hypothesis import given
from hypothesis import strategies as st

import finassert as fa


@given(
    weeks=st.integers(2, 30), opening=st.integers(-(10**15), 10**15), break_week=st.integers(1, 29)
)
def test_complete_series_and_single_localized_break(weeks, opening, break_week):
    anchor = date(2024, 2, 29)
    data = [
        {
            "id": str(n),
            "currency": "USD",
            "start": (anchor + timedelta(days=7 * n)).isoformat(),
            "end": (anchor + timedelta(days=7 * (n + 1))).isoformat(),
            "open": Decimal(opening) + n,
            "close": Decimal(opening) + n + 1,
        }
        for n in range(weeks)
    ]
    schedule = dict(
        period_start="start",
        period_end="end",
        group_by=[],
        currency="currency",
        expected_scope=[{"currency": "USD"}],
        first_period=anchor.isoformat(),
        periods=weeks,
        row_key="id",
    )
    rules = [
        fa.forecast_coverage(**schedule),
        fa.cash_continuity(opening_cash="open", closing_cash="close", **schedule),
    ]
    assert fa.check(data, rules, raise_on_error=True).passed
    index = 1 + break_week % (weeks - 1)
    data[index]["open"] += Decimal("0.01")
    report = fa.check(data, rules, raise_on_error=True)
    assert report.results[0].passed
    assert report.results[1].metadata["violation_count"] == 1
    assert report.results[1].metadata["violations"][0]["row"] == str(index)
    assert fa.check(list(reversed(data)), rules) == report
