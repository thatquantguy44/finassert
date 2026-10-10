"""Explicit, inclusive numerical tolerance semantics."""

from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal
from typing import TypeAlias

Numeric: TypeAlias = int | float | Decimal


@dataclass(frozen=True, slots=True)
class Tolerance:
    """Absolute and relative bounds for numeric comparisons.

    Values are close when ``abs(actual - expected)`` is less than or equal to
    ``absolute + relative * max(abs(actual), abs(expected))``. Decimal operands
    remain Decimal; configured tolerances are converted from their string form.
    NaN and infinity never compare as close.
    """

    absolute: Numeric = 0
    relative: Numeric = 0

    def __post_init__(self) -> None:
        if not _is_finite(self.absolute) or not _is_finite(self.relative):
            raise ValueError("tolerances must be finite")
        if self.absolute < 0 or self.relative < 0:
            raise ValueError("tolerances must be non-negative")

    def is_close(self, actual: Numeric, expected: Numeric) -> bool:
        """Return whether two finite values are within the inclusive bound."""
        if not _is_finite(actual) or not _is_finite(expected):
            return False
        if any(
            isinstance(value, Decimal) for value in (actual, expected, self.absolute, self.relative)
        ):
            actual_decimal = _to_decimal(actual)
            expected_decimal = _to_decimal(expected)
            absolute = _to_decimal(self.absolute)
            relative = _to_decimal(self.relative)
            decimal_difference = abs(actual_decimal - expected_decimal)
            decimal_bound = absolute + relative * max(abs(actual_decimal), abs(expected_decimal))
            return decimal_difference <= decimal_bound
        actual_float = float(actual)
        expected_float = float(expected)
        absolute_float = float(self.absolute)
        relative_float = float(self.relative)
        float_difference = abs(actual_float - expected_float)
        float_bound = absolute_float + relative_float * max(abs(actual_float), abs(expected_float))
        return float_difference <= float_bound

    def to_dict(self) -> dict[str, Numeric]:
        """Return a serialization-friendly representation."""
        return {"absolute": self.absolute, "relative": self.relative}


def coerce_tolerance(value: Numeric | Tolerance) -> Tolerance:
    """Convert a numeric shorthand to an absolute-only tolerance."""
    return value if isinstance(value, Tolerance) else Tolerance(absolute=value)


def is_finite(value: object) -> bool:
    """Return whether ``value`` is a supported finite real number."""
    return (
        isinstance(value, (int, float, Decimal))
        and not isinstance(value, bool)
        and _is_finite(value)
    )


def _is_finite(value: Numeric) -> bool:
    if isinstance(value, Decimal):
        return value.is_finite()
    if isinstance(value, int):
        return True
    return math.isfinite(value)


def _to_decimal(value: Numeric) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))
