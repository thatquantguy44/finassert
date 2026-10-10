# API reference

## Top-level API

- `check(data, rules, *, raise_on_error=False) -> ValidationReport`
- `weights_sum_to_one(*, column="weight", tolerance=1e-8, null_policy="fail")`
- `non_negative(*, column, tolerance=0, null_policy="fail", max_violations=20)`
- `custom_rule(rule_id, name, evaluator, ...)`
- `Tolerance(absolute=0, relative=0)`

## Results

`ValidationResult` contains `rule_id`, `rule_name`, `outcome`, `severity`,
`message`, `observed`, `expected`, `tolerance`, and `metadata`; `passed` is a
derived property. `ValidationReport` exposes ordered `results`, `failures`,
counts, `passed`, `to_dict()`, and `summary()`.

Outcomes are `passed`, `failed`, `error`, and `skipped`. JSON serialization uses
strings for Decimal values so precision is not lost.
