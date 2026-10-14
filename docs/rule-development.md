# Rule development

A rule exposes `rule_id`, `name`, `severity`, and `evaluate(data)`. Return the
rule's own `severity` in every result: a failed result of `warning` or `info`
severity is reported but does not fail the report. The method
returns a `ValidationResult` and should be deterministic, side-effect free, and
non-mutating. Stable identifiers should use a reverse-domain or project namespace
for third-party rules.

For small policies, use `custom_rule`:

```python
import finassert as fa

rule = fa.custom_rule(
    "acme.positions.present",
    "Positions are present",
    lambda data: len(data["position_id"]) > 0,
)
```

Return a full `ValidationResult` when observed, expected, tolerance, or metadata
must be reported. Exceptions represent evaluation errors, not failed financial
assertions. Limit row diagnostics and record whether they were truncated.

## Grouped rules

A grouped rule remains a normal `Rule`, but also satisfies `GroupedRule` by
exposing a `ColumnMapping` and `required_semantics`. Require an explicit
`FieldAggregation` for every required semantic at construction time. Do not infer
summation from numeric dtype: balances, prices, rates, and flows have different
aggregation behavior.

Use `aggregate_values` for the four supported numeric policies. Treat a
`REQUIRE_UNIQUE` conflict as a validation failure for the affected group. Reserve
evaluation errors for missing columns, invalid grouping keys, or inability to
construct the groups.
