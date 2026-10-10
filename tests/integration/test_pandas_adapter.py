import pandas as pd

import finassert as fa
from finassert.adapters import PandasDataFrameAdapter


def test_pandas_dataframe_works_directly() -> None:
    frame = pd.DataFrame({"weight": [0.25, 0.75], "market_value": [100, 200]}, index=["A", "B"])

    report = fa.check(
        frame,
        [fa.weights_sum_to_one(), fa.non_negative(column="market_value")],
    )

    assert report.passed


def test_adapter_preserves_index_in_diagnostics() -> None:
    frame = pd.DataFrame({"value": [1, -1]}, index=["good", "bad"])

    result = fa.check(PandasDataFrameAdapter(frame), [fa.non_negative(column="value")]).results[0]

    assert result.metadata["violations"] == [{"row": "bad", "value": -1}]
