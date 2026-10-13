# finassert

**Financial invariants, tested like code.**

[![Python](https://img.shields.io/badge/python-3.11%2B-3776AB.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Release](https://img.shields.io/badge/release-pre--alpha-lightgrey.svg)](CHANGELOG.md)

Financial datasets can be structurally valid while remaining economically
inconsistent. `finassert` provides small, deterministic rules for detecting
those inconsistencies and producing diagnostics that both people and automation
can inspect.

- Finance-native invariants with explicit assumptions.
- Immutable, JSON-compatible results with stable rule identifiers.
- Decimal-aware, inclusive absolute and relative tolerances.
- No pandas, NumPy, database, or configuration dependency in the core package.
- Rules are composable Python objects; datasets are never normalized or mutated.
- Checks can also be written as YAML policies and run from a command line or a
  browser app, so people who do not write Python can use them.

> **Project status:** usable foundation under active development. The API may
> change before 1.0; no PyPI release or hosted documentation is claimed.

## Installation

From a checkout, install the complete development environment with
[uv](https://docs.astral.sh/uv/):

```bash
uv sync --all-extras --dev
```

For an application that only needs mapping and row-record inputs:

```bash
uv add finassert
```

Install `finassert[pandas]` when pandas DataFrames are required, and
`finassert[cli]` for the command line with YAML policies. Until a release
is published, install from a checkout or a pinned source revision.

## Quick start

```python
import finassert as fa

portfolio = {
    "weight": [0.40, 0.35, 0.25],
    "market_value": [4_000_000, 3_500_000, 2_500_000],
}

report = fa.check(
    portfolio,
    rules=[
        fa.weights_sum_to_one(column="weight", tolerance=1e-8),
        fa.non_negative(column="market_value"),
    ],
)

print(report.summary())
if not report.passed:
    raise RuntimeError("Financial validation failed")
```

Output:

```text
finassert PASS: 2 passed, 0 failed, 0 errors, 0 skipped
```

A failed allocation explains the observed value and remains machine-readable:

```python
report = fa.check({"weight": [0.40, 0.50]}, [fa.weights_sum_to_one()])
print(report.summary())
print(report.results[0].observed)  # 0.9
```

```text
finassert FAIL: 0 passed, 1 failed, 0 errors, 0 skipped
- [error] portfolio.weights_sum_to_one: Weight total 0.9 is not within tolerance of 1.
```

## Without writing Python

Describe the checks in a policy file:

```yaml
version: 1
name: Daily positions
rules:
  - rule: weights_sum_to_one
    column: weight
    tolerance: "0.0001"
  - rule: non_negative
    column: market_value
```

Then run them against a CSV export and get a report anyone can read (try it with
`examples/policy.yml` and `examples/positions.csv`):

```bash
finassert check --config policy.yml --input positions.csv --html report.html
```

Exit codes separate passes (`0`), failed checks (`1`), checks that could not
run (`2`), invalid policies (`3`), and unreadable files (`4`), so the same
command gates CI jobs and ETL steps. `finassert rules` describes every check in
plain language, and `finassert init --template long-only-holdings` writes a
starter policy, with its assumptions, for you to adapt.

For people who prefer not to use a terminal, `python scripts/build_web.py`
produces a single HTML file that runs the same checks entirely inside the
browser: choose a file, pick checks from a list, and download the report and the
policy. The data never leaves the computer. See
[policies and the command line](docs/command-line.md) and the
[browser app](docs/browser-app.md).

## Errors and failures

Evaluation errors (for example, a missing configured column) are a separate
outcome and never count as passes. Set `raise_on_error=True` to fail immediately
with `RuleEvaluationError`; otherwise the engine records the error and continues.

## Capabilities

| Available now | Designed and deferred |
|---|---|
| Weight-sum and nonnegative-value rules | NAV, cash, returns, collateral, exposure rules |
| Mappings, row records, and pandas DataFrames | Polars, SQL, streaming, distributed execution |
| Decimal-aware tolerance handling | Typed currencies, FX providers, financial units |
| Typed column, grouping, and aggregation contracts | Public grouped accounting rules |
| Text, JSON, and self-contained HTML reports | Assistant tool server |
| Starter policy templates with stated assumptions | |
| YAML/JSON policies, CLI, and in-browser app | Polars and SQL inputs |
| CSV, JSON, Excel (.xlsx), and Parquet input files | |
| Callable custom rules and an explicit registry | Plugin discovery and rule version negotiation |

Negative weights are not rejected: short positions may be legitimate. Apply
`non_negative` only to a field whose financial meaning requires it. Null handling
is explicit (`"fail"`, `"ignore"`, or `"skip"`) and defaults to failure.

## Architecture

The dependency-free engine executes `Rule` objects in caller-provided order.
Each returns a `ValidationResult`; the engine aggregates them into a
`ValidationReport`. Built-in rules consume a minimal column-source contract, so
optional dataframe integrations remain outside the core import path.

See [architecture](docs/architecture.md), [rule development](docs/rule-development.md),
and the [implementation specifications](specs/README.md).

## Development

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy src/finassert
uv run mkdocs build --strict
uv build
uv run python scripts/build_web.py
```

Read [CONTRIBUTING.md](CONTRIBUTING.md) before proposing a change. Security
issues follow the private process in [SECURITY.md](SECURITY.md).

## Roadmap

The next milestones are the adapter and diagnostic contract described in
[specification 0004](specs/0004-dataframe-adapters.md), catalog rules whose
financial semantics can be stated without institutional assumptions, and the
remaining [non-technical interface](specs/0011-non-technical-interfaces.md)
work: an assistant tool server and more templates as rules are added. The
full sequence appears in the [roadmap](docs/roadmap.md).

## License

Licensed under the [MIT License](LICENSE).
