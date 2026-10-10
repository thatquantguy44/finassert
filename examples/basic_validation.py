"""Run the two built-in rules against dependency-free column data."""

import finassert as fa

portfolio = {"weight": [0.4, 0.35, 0.25], "market_value": [4_000, 3_500, 2_500]}
report = fa.check(
    portfolio,
    [fa.weights_sum_to_one(), fa.non_negative(column="market_value")],
)
print(report.summary())
