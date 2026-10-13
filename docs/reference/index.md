# API reference

## Top-level API

- `check(data, rules, *, raise_on_error=False) -> ValidationReport`
- `weights_sum_to_one(*, column="weight", tolerance=1e-8, null_policy="fail")`
- `non_negative(*, column, tolerance=0, null_policy="fail", max_violations=20)`
- `custom_rule(rule_id, name, evaluator, ...)`
- `Tolerance(absolute=0, relative=0)`

## Adapter contracts

- `ColumnMapping(columns, group_keys=(), row_key=None, aggregations={})` creates
  an immutable semantic-to-physical field and aggregation map.
- `FieldAggregation` provides `SUM`, `FIRST`, `LAST`, and `REQUIRE_UNIQUE`.
- `GroupKey(name, column)` declares one ordered grouping dimension.
- `PandasDataFrameAdapter(frame)` exposes pandas values and index labels through
  the dependency-free column-source protocol.
- `GroupedRule` is the structural protocol for ordinary rules that declare a
  mapping and required semantic fields.
- `finassert.rules.aggregate_values(values, aggregation)` applies one configured
  numeric reduction without dataframe coercion.

The grouped cash-reconciliation module is private exploratory code and is not part
of the supported API.

## Policies

- `finassert.policy.load_policy(path, *, catalog=None, format=None) -> Policy`
  reads a `.yml`, `.yaml`, or `.json` policy; YAML needs PyYAML.
- `parse_policy(document, *, catalog=None)` and
  `parse_policy_text(text, *, format, catalog=None)` validate an in-memory
  policy.
- `Policy` exposes `rules`, `entries`, `name`, `description`, `assumptions`,
  `digest`, `check(data)`, `to_document()`, and `describe()`.
- `dump_policy(policy) -> str` writes YAML that reloads to an identical policy.
- `PolicyError.issues` holds `PolicyIssue` values with `location`, `line`,
  `message`, and `suggestion`.
- `RuleCatalog`, `RuleFactorySpec`, `ParameterSpec`, and `default_catalog()`
  define which factories a policy may name and describe them in plain language.

## Loaders

- `finassert.loaders.load_input(path, *, format=None, sheet=None)` reads CSV,
  JSON, Excel `.xlsx`, or Parquet; `sheet` chooses an Excel worksheet.
- `parse_xlsx(data, *, sheet=None) -> TableSource` reads workbook bytes with no
  dependency; `read_parquet(path)` needs pyarrow.
- `parse_csv(text) -> TableSource` and `parse_json(text)` parse text directly.
- `TableSource` implements `ColumnSource` with spreadsheet row numbers as
  labels and exposes `column_names`, `row_count`, and `preview()`.

## Reporting

- `finassert.reporting.to_text(report)` and `to_json(report)` render a report.
- `build_artifact(report, *, policy=None, input_locator=None, input_format=None,
  generated_at=None)` wraps a report with schema version, tool version, policy
  digest, and input context; `artifact_to_json()` serializes it.
- `to_html(report, ...)` and `render_artifact_html(artifact)` produce a
  self-contained HTML page that embeds the artifact.

## Command line

`finassert check` and `finassert rules`; see
[Policies and the command line](../command-line.md) for options and exit codes.
`finassert.cli.exit_code(report)` maps a report to its exit code.

## Results

`ValidationResult` contains `rule_id`, `rule_name`, `outcome`, `severity`,
`message`, `observed`, `expected`, `tolerance`, and `metadata`; `passed` is a
derived property. `ValidationReport` exposes ordered `results`, `failures`,
counts, `passed`, `to_dict()`, and `summary()`.

Outcomes are `passed`, `failed`, `error`, and `skipped`. JSON serialization uses
strings for Decimal values so precision is not lost.
