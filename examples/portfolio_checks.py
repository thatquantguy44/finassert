"""Show diagnostic row labels from a pandas DataFrame."""

import pandas as pd

import finassert as fa

positions = pd.DataFrame(
    {"weight": [0.55, 0.45], "market_value": [5_500, -4_500]},
    index=["LONG", "SHORT"],
)
report = fa.check(
    positions,
    [fa.weights_sum_to_one(), fa.non_negative(column="market_value")],
)
print(report.summary())
print(report.results[1].metadata["violations"])
