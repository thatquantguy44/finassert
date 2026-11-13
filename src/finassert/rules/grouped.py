"""Shared execution semantics for grouped financial rules."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime
from decimal import Decimal
from typing import Any

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


_TEMPORAL = 1
_NUMERIC = 0


def order_value(value: object) -> tuple[int, Any]:
    """Normalize one ordering-column value into a comparable sort key.

    Accepts finite numbers (sequence numbers), dates, datetimes, and ISO 8601
    date or datetime text. Other text is rejected, because sorting text such as
    ``"1/10/2026"`` and ``"1/9/2026"`` would silently misorder rows.

    Raises:
        GroupAggregationError: If ``value`` cannot order rows.
    """
    if isinstance(value, bool) or value is None:
        raise GroupAggregationError(f"{value!r} cannot order rows")
    if isinstance(value, int | float | Decimal):
        if not is_finite(value):
            raise GroupAggregationError(f"{value!r} cannot order rows")
        return (_NUMERIC, value)
    if isinstance(value, datetime):
        return (_TEMPORAL, value)
    if isinstance(value, date):
        return (_TEMPORAL, datetime(value.year, value.month, value.day))
    if isinstance(value, str):
        try:
            return (_TEMPORAL, datetime.fromisoformat(value.strip()))
        except ValueError:
            pass
    raise GroupAggregationError(
        f"{value!r} cannot order rows; use numbers or ISO dates such as 2026-01-31"
    )


def aggregate_ordered(
    values: Sequence[Numeric],
    order: Sequence[tuple[int, Any]],
    aggregation: FieldAggregation,
) -> Numeric:
    """Reduce group values, taking ``FIRST`` and ``LAST`` by an ordering column.

    ``order`` holds keys from :func:`order_value`, aligned with ``values``. The
    first value is the one with the smallest key and the last the one with the
    largest. When several rows share that key and their values differ, the
    choice would be arbitrary, so the group fails. Other aggregations behave as
    in :func:`aggregate_values`.

    Raises:
        GroupAggregationError: As :func:`aggregate_values`, or if the ordering
            keys mix numbers with dates, mix time-zone-aware and naive times,
            or tie on different values.
    """
    if aggregation not in {FieldAggregation.FIRST, FieldAggregation.LAST}:
        return aggregate_values(values, aggregation)
    if len(order) != len(values):
        raise GroupAggregationError("ordering keys are not aligned with values")
    if not values:
        raise GroupAggregationError("cannot aggregate an empty group field")
    if any(not is_finite(value) for value in values):
        raise GroupAggregationError("group field values must be finite numbers")
    if len({kind for kind, _ in order}) > 1:
        raise GroupAggregationError("the ordering column mixes numbers and dates")
    try:
        target = (min if aggregation is FieldAggregation.FIRST else max)(key for _, key in order)
    except TypeError as exc:
        raise GroupAggregationError(
            "the ordering column mixes times with and without a time zone"
        ) from exc
    chosen = [value for value, (_, key) in zip(values, order, strict=True) if key == target]
    if any(value != chosen[0] for value in chosen[1:]):
        raise GroupAggregationError(
            f"rows tie on the ordering column at {target} with different values; "
            "use a sequence number or timestamp that is unique within each group"
        )
    return chosen[0]
