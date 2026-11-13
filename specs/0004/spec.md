# 0004 — DataFrame adapters

**Status:** pandas, mapping, and grouped aggregation contracts implemented;
Polars proposed

## Problem statement

Rules need columns and row identity without coupling the core package to a
dataframe library or pretending pandas and Polars share identical semantics.

## Motivation and use cases

Users validate mapping data, pandas research frames, future Polars lazy frames,
and grouped pipeline outputs while expecting diagnostics that locate bad records.

## Goals

Define optional adapters, explicit column mapping and null policy, stable row
labels, grouped evaluation, bounded diagnostics, and no core-time dependency.

## Non-goals

Query planning, dataframe mutation, universal expression translation, SQL
execution, and zero-copy guarantees are excluded.

## Proposed architecture

The core `ColumnSource` returns values and labels. Built-ins also accept column
mappings and row mappings. `ColumnMapping` maps semantic fields to physical
columns and explicit aggregation policies, while ordered `GroupKey` values define
partitions. `GroupedRule` extends the structural rule contract without changing
engine execution. pandas is detected without importing it and preserves the
index. A future Polars adapter will assign or require explicit row keys; it must
decide eager versus lazy collection before release.

## Public API design

```python
from finassert.adapters import (
    ColumnMapping,
    FieldAggregation,
    GroupKey,
    PandasDataFrameAdapter,
)

fa.check(frame, rules)
PandasDataFrameAdapter(frame)
mapping = ColumnMapping(
    columns={"opening_cash": "cash_open", "closing_cash": "cash_close"},
    group_keys=(GroupKey("portfolio", "portfolio_id"),),
    row_key="record_id",
    aggregations={
        "opening_cash": FieldAggregation.FIRST,
        "closing_cash": FieldAggregation.LAST,
    },
)
# Proposed: PolarsDataFrameAdapter(frame, row_key="position_id")
```

`ColumnMapping`, `GroupKey`, and `FieldAggregation` are public adapter contracts.
`GroupedRule` is the public structural grouped-rule contract. Grouped rule
factories remain rule-specific; the cash prototype is private until ordering and
currency preconditions are resolved.

## Data contracts

Columns yield equal-length values and labels. Multi-column reads validate label
alignment. Duplicate labels are permitted but metadata must not claim uniqueness.
Group keys serialize in declared order. `row_key`, when configured, supplies
diagnostic labels from a physical column. Adapters do not change dtypes, fill
nulls, reorder rows, or mutate data.

Grouped fields have no default aggregation. Rules require configured policies for
every semantic they aggregate. `SUM` preserves Decimal arithmetic; `FIRST` and
`LAST` use physical input order; `REQUIRE_UNIQUE` requires exact equality among
repeated values. Aggregation-policy failure is a group validation failure rather
than an evaluation error.

## Financial and numerical edge cases

Handle `None`, float NaN, pandas nullable scalars, Decimal object columns, empty
frames, duplicate indexes, timezone-aware timestamps, and categorical group keys.

## Failure semantics

Missing columns and unsupported containers error. Null observations follow each
rule's policy. Group-level failures identify group keys; collection failures are
evaluation errors, never passes.

## Implementation milestones

1. Mapping/record extraction and pandas index preservation (complete). 2. Formal
column-mapping and group contracts (complete). 3. pandas nullable, Decimal,
duplicate-index, empty, and non-mutation tests (complete). 4. Typed group
aggregation and grouped-rule contracts (complete). 5. Decide whether first/last
policies require an explicit ordering column. 6. Polars eager prototype, then lazy
behavior only with explicit collection limits.

## Acceptance criteria

Core imports without pandas/Polars; adapters preserve row identity; inputs remain
unmodified; missing columns are errors; semantic mappings are immutable; group
ordering is deterministic; grouped aggregation is explicit; optional extras
isolate dependencies.

## Testing requirements

Contract-test every adapter using the same synthetic cases: pass/fail, empty,
null, duplicate label, Decimal, missing column, explicit row key, group failure,
alignment, and non-mutation.

## Dependencies on other specifications

Uses 0001 and 0003; emits 0005 diagnostics; batch behavior is governed by 0010.

## Explicit deferred work

Polars, Arrow, SQL, Spark, streaming, lazy pushdown, and distributed partitions
remain deferred.
