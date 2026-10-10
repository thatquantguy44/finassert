# 0004 — DataFrame adapters

**Status:** pandas initial; Polars proposed

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
mappings and row mappings. pandas is detected without importing it and preserves
the index. A future Polars adapter will assign or require explicit row keys; it
must decide eager versus lazy collection before release.

## Public API design

```python
fa.check(frame, rules)
PandasDataFrameAdapter(frame)
# Proposed: PolarsDataFrameAdapter(frame, row_key="position_id")
```

Future `ColumnMap` maps semantic inputs to physical columns and group keys.

## Data contracts

Columns yield equal-length values and labels. Duplicate labels are permitted but
metadata must not claim uniqueness. Group keys serialize as ordered tuples.
Adapters do not change dtypes or fill nulls.

## Financial and numerical edge cases

Handle `None`, float NaN, pandas nullable scalars, Decimal object columns, empty
frames, duplicate indexes, timezone-aware timestamps, and categorical group keys.

## Failure semantics

Missing columns and unsupported containers error. Null observations follow each
rule's policy. Group-level failures identify group keys; collection failures are
evaluation errors, never passes.

## Implementation milestones

1. Mapping/record extraction and pandas index preservation. 2. Formal column-map
and group contracts. 3. pandas nullable tests. 4. Polars eager prototype, then
lazy behavior only with explicit collection limits.

## Acceptance criteria

Core imports without pandas/Polars; adapters preserve row identity; inputs remain
unmodified; missing columns are errors; optional extras isolate dependencies.

## Testing requirements

Contract-test every adapter using the same synthetic cases: pass/fail, empty,
null, duplicate label, Decimal, missing column, group failure, and non-mutation.

## Dependencies on other specifications

Uses 0001 and 0003; emits 0005 diagnostics; batch behavior is governed by 0010.

## Explicit deferred work

Polars, Arrow, SQL, Spark, streaming, lazy pushdown, and distributed partitions
remain deferred.
