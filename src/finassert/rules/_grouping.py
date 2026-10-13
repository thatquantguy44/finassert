"""Partition rows into groups for reconciliation rules."""

from __future__ import annotations

from collections.abc import Collection, Sequence
from dataclasses import dataclass, field
from typing import Any

from finassert.adapters._column import extract_columns, is_missing
from finassert.adapters.contracts import ColumnMapping
from finassert.core.exceptions import GroupAggregationError, InvalidDataError
from finassert.numerical import Numeric, is_finite
from finassert.rules.grouped import aggregate_ordered, order_value

_ORDER_FIELD = "order"


@dataclass(slots=True)
class Group:
    """Observations of one group, in physical row order.

    Attributes:
        identity: Group-key name to value, in declared key order.
        values: Semantic field to its present values.
        orders: Semantic field to ordering keys aligned with ``values``.
        rows: Diagnostic labels of the group's rows.
    """

    identity: dict[str, Any]
    values: dict[str, list[Numeric]]
    orders: dict[str, list[tuple[int, Any]]]
    rows: list[Any] = field(default_factory=list)

    def aggregate(self, semantic: str, mapping: ColumnMapping) -> Numeric:
        """Reduce one field with its configured aggregation."""
        return aggregate_ordered(
            self.values[semantic],
            self.orders[semantic],
            mapping.aggregation_for(semantic),
        )


@dataclass(slots=True)
class Collected:
    """Groups plus the rows that could not join one.

    Attributes:
        groups: Groups in order of first appearance.
        unusable_rows: Rows, in file order, with blank required values
            (``blank``) or non-numeric values or ordering values (``invalid``).
        row_count: Number of rows read.
    """

    groups: list[Group]
    unusable_rows: list[dict[str, Any]]
    row_count: int

    @property
    def has_blanks(self) -> bool:
        """Return whether any unusable row has a blank value."""
        return any(item.get("blank") for item in self.unusable_rows)


def collect_groups(
    data: Any,
    mapping: ColumnMapping,
    semantics: Sequence[str],
    *,
    blank_allowed: Collection[str] = (),
) -> Collected:
    """Read the mapped columns and partition rows by the mapping's group keys.

    A row with a blank group key cannot be placed, so it is an evaluation error.
    A blank value makes the row unusable unless the field is in
    ``blank_allowed``, in which case the blank is left out of that field only.
    A non-finite or non-numeric value, or an ordering value that is not a number
    or ISO date, also makes the row unusable. Unusable rows do not join a group.

    Raises:
        InvalidDataError: If a group key is blank or columns are misaligned.
        ColumnNotFoundError: If a mapped column is absent.
    """
    physical = {semantic: mapping.resolve(semantic) for semantic in semantics}
    names = [*physical.values(), *mapping.grouping_columns]
    if mapping.order_key is not None:
        names.append(mapping.order_key)
    columns, labels = extract_columns(data, names, row_key=mapping.row_key)

    groups: dict[tuple[Any, ...], Group] = {}
    unusable_rows: list[dict[str, Any]] = []
    for position, label in enumerate(labels):
        key = tuple(columns[group_key.column][position] for group_key in mapping.group_keys)
        if any(is_missing(value) for value in key):
            raise InvalidDataError(f"row {label!r} has a blank value in a grouping column")

        missing: list[str] = []
        invalid: list[str] = []
        present: dict[str, Numeric] = {}
        for semantic, column in physical.items():
            value = columns[column][position]
            if is_missing(value):
                if semantic not in blank_allowed:
                    missing.append(semantic)
            elif not is_finite(value):
                invalid.append(semantic)
            else:
                present[semantic] = value
        order: tuple[int, Any] = (0, 0)
        if mapping.order_key is not None:
            raw = columns[mapping.order_key][position]
            if is_missing(raw):
                missing.append(_ORDER_FIELD)
            else:
                try:
                    order = order_value(raw)
                except GroupAggregationError:
                    invalid.append(_ORDER_FIELD)
        if missing or invalid:
            entry: dict[str, Any] = {"row": label}
            if missing:
                entry["blank"] = missing
            if invalid:
                entry["invalid"] = invalid
            unusable_rows.append(entry)
            continue

        group = groups.get(key)
        if group is None:
            group = Group(
                identity={
                    group_key.name: value
                    for group_key, value in zip(mapping.group_keys, key, strict=True)
                },
                values={semantic: [] for semantic in semantics},
                orders={semantic: [] for semantic in semantics},
            )
            groups[key] = group
        group.rows.append(label)
        for semantic, value in present.items():
            group.values[semantic].append(value)
            group.orders[semantic].append(order)
    return Collected(
        groups=list(groups.values()),
        unusable_rows=unusable_rows,
        row_count=len(labels),
    )
