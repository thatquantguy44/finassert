"""Shared execution semantics for grouped financial rules."""

from __future__ import annotations

from collections.abc import Sequence

from finassert.adapters.contracts import FieldAggregation
from finassert.core.exceptions import GroupAggregationError
from finassert.numerical import Numeric, is_finite
from finassert.rules._helpers import precise_sum


def aggregate_values(values: Sequence[Numeric], aggregation: FieldAggregation) -> Numeric:
    """Reduce ordered finite numeric values using an explicit group policy.

    ``FIRST`` and ``LAST`` use physical input order; adapters never sort rows.
    ``REQUIRE_UNIQUE`` uses exact numeric equality because it validates data
    shape, while financial comparison tolerance belongs to the consuming rule.

    Args:
        values: Non-empty, finite numeric values in adapter-provided row order.
        aggregation: Explicit reduction policy.

    Raises:
        GroupAggregationError: If values are empty, non-finite, or fail
            ``REQUIRE_UNIQUE``.
    """
    if not values:
        raise GroupAggregationError("cannot aggregate an empty group field")
    if any(not is_finite(value) for value in values):
        raise GroupAggregationError("group field values must be finite numbers")
    if aggregation is FieldAggregation.SUM:
        return precise_sum(list(values))
    if aggregation is FieldAggregation.FIRST:
        return values[0]
    if aggregation is FieldAggregation.LAST:
        return values[-1]
    if aggregation is FieldAggregation.REQUIRE_UNIQUE:
        first = values[0]
        if any(value != first for value in values[1:]):
            raise GroupAggregationError("group field contains more than one distinct value")
        return first
    raise AssertionError(f"unsupported field aggregation: {aggregation!r}")
