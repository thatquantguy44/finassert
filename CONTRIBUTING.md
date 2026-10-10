# Contributing

Thank you for improving `finassert`. Open an issue before substantial API or
financial-semantics changes. A rule proposal should state the invariant, units,
sign convention, null policy, tolerance basis, failure diagnostics, and cases in
which the rule is inappropriate.

## Development

Install [uv](https://docs.astral.sh/uv/), then run:

```bash
uv sync --all-extras --dev
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy src/finassert
uv run mkdocs build --strict
uv build
```

Public APIs require type annotations and Google-style docstrings. Tests should
cover boundaries, nulls, empty data, non-finite values, and Decimal behavior as
applicable. Use synthetic data and do not commit credentials or proprietary data.

By participating, you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).
