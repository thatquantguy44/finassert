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

Install `finassert[pandas]` when pandas DataFrames are required. Until a release
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
| Text and JSON-compatible results | CLI, YAML policies, HTML reports |
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
```

Read [CONTRIBUTING.md](CONTRIBUTING.md) before proposing a change. Security
issues follow the private process in [SECURITY.md](SECURITY.md).

## Roadmap

The next milestone is the adapter and diagnostic contract described in
[specification 0004](specs/0004-dataframe-adapters.md), followed by catalog rules
whose financial semantics can be stated without institutional assumptions. The
full sequence appears in the [roadmap](docs/roadmap.md).

## License

Licensed under the [MIT License](LICENSE).
