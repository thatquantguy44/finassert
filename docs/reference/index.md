# API reference

## Top-level API

- `check(data, rules, *, raise_on_error=False) -> ValidationReport`
- `weights_sum_to_one(*, column="weight", tolerance=1e-8, null_policy="fail")`
- `non_negative(*, column, tolerance=0, null_policy="fail", max_violations=20)`
- `custom_rule(rule_id, name, evaluator, ...)`
- `Tolerance(absolute=0, relative=0)`

## Adapter contracts

- `ColumnMapping(columns, group_keys=(), row_key=None)` creates an immutable
  semantic-to-physical field map.
- `GroupKey(name, column)` declares one ordered grouping dimension.
- `PandasDataFrameAdapter(frame)` exposes pandas values and index labels through
  the dependency-free column-source protocol.

The grouped cash-reconciliation module is private exploratory code and is not part
of the supported API.

## Results

`ValidationResult` contains `rule_id`, `rule_name`, `outcome`, `severity`,
`message`, `observed`, `expected`, `tolerance`, and `metadata`; `passed` is a
derived property. `ValidationReport` exposes ordered `results`, `failures`,
counts, `passed`, `to_dict()`, and `summary()`.

Outcomes are `passed`, `failed`, `error`, and `skipped`. JSON serialization uses
strings for Decimal values so precision is not lost.
