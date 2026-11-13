"""Internal numeric helpers for rules."""

from __future__ import annotations

import math
from decimal import Decimal, localcontext
from typing import Any, cast

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


def precise_product(values: list[Numeric]) -> Numeric:
    """Multiply values without converting Decimal operands to binary floats.

    Decimal products are computed with enough precision that they are not
    rounded, so a quantity times a price keeps every digit.
    """
    if any(isinstance(value, Decimal) for value in values):
        with localcontext() as context:
            context.prec = 100
            result = Decimal(1)
            for value in values:
                result *= _decimal(value)
            return result
    result_number: Any = 1
    for value in values:
        result_number *= value
    return cast(Numeric, result_number)


def precise_quotient(numerator: Numeric, denominator: Numeric) -> Numeric:
    """Divide, keeping Decimal operands exact to many digits; the divisor is nonzero."""
    if isinstance(numerator, Decimal) or isinstance(denominator, Decimal):
        with localcontext() as context:
            context.prec = 50
            return _decimal(numerator) / _decimal(denominator)
    return numerator / denominator


def _decimal(value: Numeric) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


def is_blank(value: object) -> bool:
    """Return whether a cell holds nothing: missing, or text with no characters.

    Text of only spaces counts as blank, as a person looking at a spreadsheet
    would see it. Zero and ``False`` are values, not blanks.
    """
    return is_missing(value) or (isinstance(value, str) and not value.strip())


def absolute(value: Numeric) -> Numeric:
    """Return the absolute value of a number, keeping its type."""
    return -value if value < 0 else value
