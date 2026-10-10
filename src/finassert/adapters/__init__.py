"""Optional dataset adapters."""

from finassert.adapters.contracts import ColumnMapping, FieldAggregation, GroupKey
from finassert.adapters.pandas import PandasDataFrameAdapter

__all__ = ["ColumnMapping", "FieldAggregation", "GroupKey", "PandasDataFrameAdapter"]
