# Integrations

Column mappings and row records require no extra dependency. pandas support is
available through the `pandas` extra and accepts a DataFrame directly or through
`PandasDataFrameAdapter`, which preserves index labels in row diagnostics.

Rules that consume multiple fields can use `ColumnMapping` to separate semantic
names from physical schemas. `GroupKey` declarations retain order in diagnostics,
an optional `row_key` column provides portable row identity, and
`FieldAggregation` makes every grouped reduction explicit. See
[Grouped validation](design/grouped-validation.md) for the contract and example.

YAML and JSON policies, CSV and JSON file loaders, the `finassert` command, and
HTML reports are described in [Policies and the command line](command-line.md).
PyYAML (`finassert[cli]`) is needed only to read YAML policies.

Any orchestrator that can run a shell command can gate a step on
`finassert check`; the exit code distinguishes failed checks from checks that
could not run, and `--output` retains the JSON artifact for operators.

Polars is deferred until expression, null, and row-identity behavior is stable.
Orchestrator packages, database, and distributed integrations are designs only
and are documented in the repository's `specs/` directory. No optional
integration is imported by the core package.
