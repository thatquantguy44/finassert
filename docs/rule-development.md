# Rule development

A rule exposes `rule_id`, `name`, `severity`, and `evaluate(data)`. The method
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
