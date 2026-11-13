# Pipeline validation

```python
report = finassert.check(dataset, configured_rules)
artifact = finassert.reporting.to_json(report)
write_artifact(artifact)
if not report.passed:
    raise RuntimeError(report.summary())
```

Keep the artifact even on failure so operators can distinguish invariant
failures from evaluation errors.

Without Python glue, run the same checks from a policy file:

```bash
finassert check --config policy.yml --input positions.csv --output report.json
```

Exit code `1` means a check failed and `2` that a check could not run.
