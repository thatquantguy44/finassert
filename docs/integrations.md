# Integrations

Column mappings and row records require no extra dependency. pandas support is
available through the `pandas` extra and accepts a DataFrame directly or through
`PandasDataFrameAdapter`, which preserves index labels in row diagnostics.

Rules that consume multiple fields can use `ColumnMapping` to separate semantic
names from physical schemas. `GroupKey` declarations retain order in diagnostics,
and an optional `row_key` column provides portable row identity. See
[Grouped validation](design/grouped-validation.md) for the contract and example.

Polars is deferred until expression, null, and row-identity behavior is stable.
YAML, orchestrator, database, and distributed integrations are designs only and
are documented in the repository's `specs/` directory. No optional integration
is imported by the core package.
