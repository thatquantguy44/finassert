# Contributing

Thank you for improving `finassert`. Open an issue before substantial API or
financial-semantics changes. A rule proposal should state the invariant, units,
sign convention, null policy, tolerance basis, failure diagnostics, and cases in
which the rule is inappropriate.

## Development

Install [uv](https://docs.astral.sh/uv/), then run:

```bash
uv sync --all-extras --dev
git config --local core.hooksPath .githooks
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

Commits must satisfy the configurable identity rules in `.author-policy.toml`.
The tracked `.githooks/pre-commit` hook checks the effective Git author, and CI
checks every author in repository history. Activate the tracked hooks with the
command above. Update the policy through review when maintainers or accepted
identities change; common AI-agent identities remain blocked.

By participating, you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).
