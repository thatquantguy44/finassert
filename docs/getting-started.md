# Getting started

Install all development dependencies with `uv sync --all-extras --dev`.

```python
import finassert as fa

data = {"weight": [0.6, 0.4], "market_value": [600, 400]}
report = fa.check(
    data,
    [fa.weights_sum_to_one(), fa.non_negative(column="market_value")],
)
assert report.passed, report.summary()
```

Inputs may be column mappings, sequences of row mappings, pandas DataFrames, or
objects implementing `ColumnSource`. The core package has no runtime dependency.

The same checks can be written in a policy file and run with
`finassert check`, or from the browser app without installing anything; see
[Policies and the command line](command-line.md).

## Nulls and errors

Built-in rules default to `null_policy="fail"`. Use `"ignore"` only when the
financial policy explicitly permits incomplete observations, or `"skip"` when
the entire rule should be recorded as not evaluated. A missing column is an
evaluation error. Use `raise_on_error=True` when pipeline control flow should
stop at the first error.
