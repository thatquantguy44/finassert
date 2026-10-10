# Architecture

The architecture has four small layers:

1. `core` owns outcomes, immutable result models, the `Rule` protocol, and
   deterministic sequential execution.
2. `numerical` owns finite-value and tolerance semantics without coercing Decimal
   values to float.
3. `rules` contains finance-aware policies. A rule reads data and returns one
   complete result; it does not mutate the dataset.
4. `adapters` translate optional tabular libraries into a two-method conceptual
   boundary: named values and stable row labels.

Imports of `finassert` do not import pandas or NumPy. Diagnostics are bounded to
avoid accidentally creating unbounded artifacts. Rule order, result order, and
JSON key ordering are deterministic for identical inputs and configuration.

An empty rule set passes vacuously. Skipped rules do not fail a report. Failed
and errored rules do, regardless of severity; severity classifies impact rather
than changing truth.

## Column and grouping contracts

`finassert.adapters.ColumnMapping` maps stable rule semantics to physical column
names. Ordered `GroupKey` values define partitions and diagnostic key order. An
optional physical `row_key` replaces native labels for row diagnostics. Mapping
configuration is immutable after construction, while input datasets remain
untouched.

Grouped mappings assign an explicit `FieldAggregation` to every semantic field:
`SUM`, `FIRST`, `LAST`, or `REQUIRE_UNIQUE`. First and last refer to unchanged
physical input order. `GroupedRule` is a structural extension of `Rule`; the core
engine still executes it through the ordinary `evaluate` method.

Grouped validation design and the private cash-reconciliation exploration are
documented in [Grouped validation](design/grouped-validation.md).
