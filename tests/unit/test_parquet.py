import builtins
import math
from decimal import Decimal
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

import finassert as fa
from finassert.core.exceptions import InvalidDataError
from finassert.loaders import input_format_for, load_input, read_parquet


def write(path: Path, table: pa.Table) -> Path:
    pq.write_table(table, path)
    return path


def test_parquet_values_keep_their_stored_types(tmp_path: Path) -> None:
    table = pa.table(
        {
            "weight": pa.array([Decimal("0.40"), Decimal("0.60")], pa.decimal128(10, 2)),
            "price": pa.array([1.5, float("nan")], pa.float64()),
            "qty": pa.array([10, None], pa.int64()),
            "ticker": ["AAA", "BBB"],
        }
    )
    source = read_parquet(write(tmp_path / "positions.parquet", table))

    assert source.column_names == ("weight", "price", "qty", "ticker")
    assert source.column("weight") == ([Decimal("0.40"), Decimal("0.60")], [0, 1])
    price = source.column("price")[0]
    assert price[0] == 1.5 and math.isnan(price[1])
    assert source.column("qty")[0] == [10, None]
    report = fa.check(source, [fa.weights_sum_to_one(tolerance=0)])
    assert report.passed


def test_parquet_nulls_and_nans_are_missing_values(tmp_path: Path) -> None:
    path = write(tmp_path / "p.pq", pa.table({"mv": pa.array([1.0, None, float("nan")])}))
    result = fa.check(load_input(path), [fa.non_negative(column="mv")]).results[0]
    assert result.metadata["invalid_rows"] == [1, 2]
    assert input_format_for(path) == "parquet"


def test_invalid_parquet_is_reported(tmp_path: Path) -> None:
    path = tmp_path / "broken.parquet"
    path.write_bytes(b"not parquet")
    with pytest.raises(InvalidDataError, match="Parquet file could not be read"):
        read_parquet(path)


def test_missing_pyarrow_explains_the_extra(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    real_import = builtins.__import__

    def without_pyarrow(name: str, *args: Any, **kwargs: Any) -> Any:
        if name.startswith("pyarrow"):
            raise ImportError(name)
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", without_pyarrow)
    with pytest.raises(InvalidDataError, match=r"finassert\[parquet\]"):
        read_parquet(tmp_path / "x.parquet")
