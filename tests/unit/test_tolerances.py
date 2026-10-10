from decimal import Decimal

import pytest

from finassert.numerical import Tolerance


def test_absolute_boundary_is_inclusive() -> None:
    tolerance = Tolerance(absolute=Decimal("0.01"))

    assert tolerance.is_close(Decimal("1.01"), Decimal("1.00"))


def test_relative_tolerance_scales_from_larger_magnitude() -> None:
    tolerance = Tolerance(relative=Decimal("0.01"))

    assert tolerance.is_close(Decimal("101"), Decimal("100"))
    assert not tolerance.is_close(Decimal("102"), Decimal("100"))


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_values_never_compare_close(value: float) -> None:
    assert not Tolerance(absolute=100).is_close(value, 1)


def test_invalid_tolerances_are_rejected() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        Tolerance(absolute=-1)
