"""Internal numeric helpers for rules."""

from __future__ import annotations

import math
from decimal import Decimal
from typing import Any

from finassert.adapters._column import is_missing
from finassert.numerical import Numeric, is_finite


def finite_numeric_values(values: list[Any]) -> tuple[list[Numeric], list[int]]:
    """Return supported finite numbers and positions containing invalid values."""
    numeric: list[Numeric] = []
    invalid: list[int] = []
    for position, value in enumerate(values):
        if is_finite(value):
            numeric.append(value)
        else:
            invalid.append(position)
    return numeric, invalid


def precise_sum(values: list[Numeric]) -> Numeric:
    """Sum values without converting Decimal operands to binary floats."""
    if any(isinstance(value, Decimal) for value in values):
        return sum((_decimal(value) for value in values), Decimal(0))
    if any(isinstance(value, float) for value in values):
        return math.fsum(values)
    return sum(values)


def _decimal(value: Numeric) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


def is_blank(value: object) -> bool:
    """Return whether a cell holds nothing: missing, or text with no characters.

    Text of only spaces counts as blank, as a person looking at a spreadsheet
    would see it. Zero and ``False`` are values, not blanks.
    """
    return is_missing(value) or (isinstance(value, str) and not value.strip())
