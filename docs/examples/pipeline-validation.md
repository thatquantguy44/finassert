# Pipeline validation

```python
report = finassert.check(dataset, configured_rules)
artifact = finassert.reporting.to_json(report)
write_artifact(artifact)
if not report.passed:
    raise RuntimeError(report.summary())
```

This is the recommended pattern until the proposed CLI exists. Keep the artifact
even on failure so operators can distinguish invariant failures from evaluation
errors.
