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
