"""Optional pandas adapter.

Importing this module does not import pandas. The adapter uses DataFrame's
public column and index interfaces and validates its input at runtime.
"""

from __future__ import annotations

from typing import Any

from finassert.adapters._column import extract_column
from finassert.core.exceptions import InvalidDataError


class PandasDataFrameAdapter:
    """Expose a pandas DataFrame through the core ``ColumnSource`` protocol."""

    def __init__(self, dataframe: Any) -> None:
        data_type = type(dataframe)
        pandas_module = data_type.__module__ == "pandas" or data_type.__module__.startswith(
            "pandas."
        )
        if not (pandas_module and data_type.__name__ == "DataFrame"):
            raise InvalidDataError("PandasDataFrameAdapter requires a pandas DataFrame")
        self._dataframe = dataframe

    def column(self, name: str) -> tuple[list[Any], list[Any]]:
        """Return a column's values and index labels."""
        return extract_column(self._dataframe, name)
