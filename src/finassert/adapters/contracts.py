"""Typed contracts shared by dataframe and columnar adapters."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType


class FieldAggregation(StrEnum):
    """How a semantic numeric field reduces within an ordered group."""

    SUM = "sum"
    FIRST = "first"
    LAST = "last"
    REQUIRE_UNIQUE = "require_unique"


@dataclass(frozen=True, slots=True)
class GroupKey:
    """A named physical column used to partition validation observations.

    Args:
        name: Stable semantic name emitted in diagnostics, such as ``portfolio``.
        column: Physical dataset column containing the grouping values.
    """

    name: str
    column: str

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not isinstance(self.column, str):
            raise TypeError("group key name and column must be strings")
        if not self.name.strip():
            raise ValueError("group key name must not be empty")
        if not self.column.strip():
            raise ValueError("group key column must not be empty")


@dataclass(frozen=True, slots=True)
class ColumnMapping:
    """Map rule semantics to physical columns and ordered grouping keys.

    A defensive immutable copy of ``columns`` is retained. Group-key order is
    significant because it defines deterministic grouping and serialization.

    Args:
        columns: Semantic field names mapped to physical dataset columns.
        group_keys: Ordered keys used to partition observations.
        row_key: Optional physical column used as diagnostic row identity. When
            omitted, adapters retain their native labels (for example a pandas
            index) or positional labels.
        aggregations: Reduction policy keyed by semantic field name. Ungrouped
            rules may omit it. Grouped rules must explicitly require policies
            for every semantic field they aggregate.
    """

    columns: Mapping[str, str]
    group_keys: tuple[GroupKey, ...] = ()
    row_key: str | None = None
    aggregations: Mapping[str, FieldAggregation] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.columns, Mapping):
            raise TypeError("columns must be a mapping")
        normalized: dict[str, str] = {}
        for semantic_name, physical_column in self.columns.items():
            if not isinstance(semantic_name, str) or not isinstance(physical_column, str):
                raise TypeError("semantic and physical column names must be strings")
            if not semantic_name.strip():
                raise ValueError("semantic column names must not be empty")
            if not physical_column.strip():
                raise ValueError(f"physical column for {semantic_name!r} must not be empty")
            normalized[semantic_name] = physical_column
        if not normalized:
            raise ValueError("at least one semantic column mapping is required")

        if any(not isinstance(key, GroupKey) for key in self.group_keys):
            raise TypeError("group_keys must contain GroupKey instances")
        group_names = [key.name for key in self.group_keys]
        if len(group_names) != len(set(group_names)):
            raise ValueError("group key names must be unique")
        group_columns = [key.column for key in self.group_keys]
        if len(group_columns) != len(set(group_columns)):
            raise ValueError("group key columns must be unique")
        if self.row_key is not None:
            if not isinstance(self.row_key, str):
                raise TypeError("row_key must be a string when provided")
            if not self.row_key.strip():
                raise ValueError("row_key must be a non-empty column name when provided")

        if not isinstance(self.aggregations, Mapping):
            raise TypeError("aggregations must be a mapping")
        normalized_aggregations: dict[str, FieldAggregation] = {}
        for semantic_name, aggregation in self.aggregations.items():
            if semantic_name not in normalized:
                raise ValueError(
                    f"aggregation configured for unknown semantic column {semantic_name!r}"
                )
            if not isinstance(aggregation, FieldAggregation):
                raise TypeError("aggregation values must be FieldAggregation members")
            normalized_aggregations[semantic_name] = aggregation

        object.__setattr__(self, "columns", MappingProxyType(normalized))
        object.__setattr__(self, "group_keys", tuple(self.group_keys))
        object.__setattr__(self, "aggregations", MappingProxyType(normalized_aggregations))

    def resolve(self, semantic_name: str) -> str:
        """Return the physical column for a required semantic field."""
        try:
            return self.columns[semantic_name]
        except KeyError as exc:
            raise KeyError(f"semantic column {semantic_name!r} is not configured") from exc

    def required_columns(self, *semantic_names: str) -> tuple[str, ...]:
        """Resolve required semantics in caller-provided order."""
        return tuple(self.resolve(name) for name in semantic_names)

    def aggregation_for(self, semantic_name: str) -> FieldAggregation:
        """Return the explicit aggregation for a semantic field."""
        self.resolve(semantic_name)
        try:
            return self.aggregations[semantic_name]
        except KeyError as exc:
            raise KeyError(
                f"aggregation for semantic column {semantic_name!r} is not configured"
            ) from exc

    def required_aggregations(self, *semantic_names: str) -> tuple[FieldAggregation, ...]:
        """Resolve required aggregations in caller-provided order."""
        return tuple(self.aggregation_for(name) for name in semantic_names)

    @property
    def grouping_columns(self) -> tuple[str, ...]:
        """Return physical grouping columns in declared order."""
        return tuple(key.column for key in self.group_keys)
