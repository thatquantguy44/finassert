# API reference

## Top-level API

- `check(data, rules, *, raise_on_error=False) -> ValidationReport`
- `weights_sum_to_one(*, column="weight", tolerance=1e-8, null_policy="fail",
  group_by=(), max_violations=20)`; with `group_by`, each group must add up to 1.
- `non_negative(*, column, tolerance=0, null_policy="fail", max_violations=20)`
- `cash_reconciles(*, outflow_sign, opening_cash, inflows, outflows,
  closing_cash, cash_pnl=None, group_by=(), currency=None, grain="summary",
  order_by=None, row_key=None, mapping=None, tolerance=0, null_policy="fail",
  max_violations=20)` checks that cash rolls forward within each group.
- `nav_reconciles(*, market_value, nav, group_by=(), currency=None,
  row_key=None, tolerance=0, null_policy="fail", max_violations=20)` checks
  that signed market values add up to the reported NAV within each group.
- `no_duplicates(*, columns, null_policy="fail", max_violations=20)` checks
  that no value, or combination of values, appears on two rows.
- `required_fields(*, columns, max_violations=20)` checks that the named
  columns are never blank.
- `custom_rule(rule_id, name, evaluator, ...)`
- `Tolerance(absolute=0, relative=0)`

## Adapter contracts

- `ColumnMapping(columns, group_keys=(), row_key=None, aggregations={},
  order_key=None)` creates an immutable semantic-to-physical field and
  aggregation map. `order_key` names the column that orders rows for `FIRST`
  and `LAST`, which public rules require.
- `FieldAggregation` provides `SUM`, `FIRST`, `LAST`, and `REQUIRE_UNIQUE`.
- `GroupKey(name, column)` declares one ordered grouping dimension.
- `PandasDataFrameAdapter(frame)` exposes pandas values and index labels through
  the dependency-free column-source protocol.
- `GroupedRule` is the structural protocol for ordinary rules that declare a
  mapping and required semantic fields.
- `finassert.rules.aggregate_values(values, aggregation)` applies one configured
  numeric reduction without dataframe coercion, taking `FIRST`/`LAST` by
  physical order; `finassert.rules.grouped.aggregate_ordered(values, order,
  aggregation)` takes them by ordering keys from `order_value`.

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

- `policy_templates()` and `get_template(name)` return `PolicyTemplate` starter
  policies with `policy()`, `to_yaml()`, `assumptions` in the document, and
  `adapt` notes.

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

## Assistant tool server

`finassert-assistant --root FOLDER` serves the tools `rules`, `templates`,
`check_policy`, `inspect`, and `run_checks` over MCP; see
[Assistant tool server](../assistant.md). The same functions are available as
`finassert.assistant.list_rules`, `list_templates`, `validate_policy`,
`inspect_data`, and `check_data`, with `Workspace` restricting file access.

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
