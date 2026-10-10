"""Dependency-free column extraction shared by built-in rules."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Any

from finassert.core.exceptions import ColumnNotFoundError, InvalidDataError
from finassert.core.protocols import ColumnSource


def extract_column(data: Any, name: str) -> tuple[list[Any], list[Any]]:
    """Extract a named column and stable row labels from supported inputs."""
    if isinstance(data, ColumnSource):
        return data.column(name)
    if isinstance(data, Mapping):
        if name not in data:
            raise ColumnNotFoundError(name)
        raw_values = data[name]
        if isinstance(raw_values, (str, bytes)):
            raise InvalidDataError(f"column {name!r} must be an iterable of values")
        try:
            column_values = list(raw_values)
        except TypeError as exc:
            raise InvalidDataError(f"column {name!r} must be iterable") from exc
        return column_values, list(range(len(column_values)))
    if _looks_like_pandas(data):
        return _extract_pandas(data, name)
    if isinstance(data, Sequence) and not isinstance(data, (str, bytes)):
        row_values: list[Any] = []
        for index, row in enumerate(data):
            if not isinstance(row, Mapping):
                raise InvalidDataError(f"row {index} is not a mapping")
            if name not in row:
                raise ColumnNotFoundError(name)
            row_values.append(row[name])
        return row_values, list(range(len(row_values)))
    raise InvalidDataError(
        "data must be a column mapping, a sequence of row mappings, "
        "a ColumnSource, or a pandas DataFrame"
    )


def extract_columns(
    data: Any,
    names: Sequence[str],
    *,
    row_key: str | None = None,
) -> tuple[dict[str, list[Any]], list[Any]]:
    """Extract aligned columns and diagnostic row labels.

    Repeated physical column names are read once. All extracted columns must
    expose the same native labels. When ``row_key`` is supplied, its values
    replace native labels after alignment has been validated.
    """
    requested = tuple(dict.fromkeys([*names, *([row_key] if row_key else [])]))
    if not requested:
        raise InvalidDataError("at least one column must be requested")

    extracted: dict[str, list[Any]] = {}
    native_labels: list[Any] | None = None
    for name in requested:
        values, labels = extract_column(data, name)
        if native_labels is None:
            native_labels = labels
        elif not _labels_equal(native_labels, labels):
            raise InvalidDataError("extracted columns do not share aligned row labels")
        extracted[name] = values

    assert native_labels is not None
    diagnostic_labels = list(extracted[row_key]) if row_key else native_labels
    return extracted, diagnostic_labels


def is_missing(value: object) -> bool:
    """Return whether a scalar represents a missing value."""
    if value is None:
        return True
    value_type = type(value)
    if value_type.__name__ in {"NAType", "NaTType"} and value_type.__module__.startswith("pandas"):
        return True
    if isinstance(value, Decimal):
        return value.is_nan()
    try:
        comparison = value != value
        return bool(comparison)
    except Exception:
        return False


def _looks_like_pandas(data: Any) -> bool:
    data_type = type(data)
    return (
        data_type.__module__ == "pandas" or data_type.__module__.startswith("pandas.")
    ) and data_type.__name__ == "DataFrame"


def _extract_pandas(data: Any, name: str) -> tuple[list[Any], list[Any]]:
    if name not in data.columns:
        raise ColumnNotFoundError(name)
    return data[name].tolist(), data.index.tolist()


def _labels_equal(left: list[Any], right: list[Any]) -> bool:
    if len(left) != len(right):
        return False
    for left_item, right_item in zip(left, right, strict=True):
        if left_item is right_item:
            continue
        try:
            if not bool(left_item == right_item):
                return False
        except Exception:
            return False
    return True
