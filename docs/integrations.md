# Integrations

Column mappings and row records require no extra dependency. pandas support is
available through the `pandas` extra and accepts a DataFrame directly or through
`PandasDataFrameAdapter`, which preserves index labels in row diagnostics.

Polars is deferred until expression, null, and row-identity behavior is stable.
YAML, orchestrator, database, and distributed integrations are designs only and
are documented in the repository's `specs/` directory. No optional integration
is imported by the core package.
