from decimal import Decimal

import pandas as pd
import pandas.testing as pdt

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


def test_pandas_nullable_values_follow_explicit_null_policy() -> None:
    frame = pd.DataFrame({"value": pd.Series([1, pd.NA], dtype="Int64")})

    failed = fa.check(frame, [fa.non_negative(column="value")]).results[0]
    ignored = fa.check(
        frame,
        [fa.non_negative(column="value", null_policy="ignore")],
    ).results[0]
    skipped = fa.check(
        frame,
        [fa.non_negative(column="value", null_policy="skip")],
    ).results[0]

    assert failed.metadata["invalid_rows"] == [1]
    assert ignored.passed
    assert skipped.outcome is fa.Outcome.SKIPPED


def test_pandas_decimal_object_column_preserves_decimal_arithmetic() -> None:
    frame = pd.DataFrame(
        {"weight": [Decimal("0.10"), Decimal("0.20"), Decimal("0.70")]},
        dtype=object,
    )

    result = fa.check(
        frame,
        [fa.weights_sum_to_one(tolerance=Decimal("0"))],
    ).results[0]

    assert result.passed
    assert result.observed == Decimal("1.00")


def test_duplicate_pandas_indexes_are_retained_without_claiming_uniqueness() -> None:
    frame = pd.DataFrame({"value": [-1, -2]}, index=["duplicate", "duplicate"])

    result = fa.check(frame, [fa.non_negative(column="value")]).results[0]

    assert result.metadata["violations"] == [
        {"row": "duplicate", "value": -1},
        {"row": "duplicate", "value": -2},
    ]


def test_pandas_input_is_not_mutated() -> None:
    frame = pd.DataFrame(
        {"weight": [0.4, 0.6], "market_value": [400, 600]},
        index=pd.Index(["A", "B"], name="position"),
    )
    original = frame.copy(deep=True)

    fa.check(
        frame,
        [fa.weights_sum_to_one(), fa.non_negative(column="market_value")],
    )

    pdt.assert_frame_equal(frame, original)


def test_empty_pandas_frame_uses_each_rules_documented_semantics() -> None:
    frame = pd.DataFrame({"weight": pd.Series(dtype=float), "market_value": pd.Series(dtype=float)})

    report = fa.check(
        frame,
        [fa.weights_sum_to_one(), fa.non_negative(column="market_value")],
    )

    assert report.results[0].outcome is fa.Outcome.FAILED
    assert report.results[1].outcome is fa.Outcome.PASSED
