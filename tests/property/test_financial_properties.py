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
