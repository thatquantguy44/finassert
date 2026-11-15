## Summary

## Financial assumptions

Describe units, signs, tolerances, null handling, and inappropriate use cases.

## Verification

- [ ] Master handoff checkpoint updated, priorities/pickup reviewed and Git context refreshed
- [ ] `python3 scripts/check_handoff.py --staged` (before committing)
- [ ] Tests added or updated
- [ ] `uv run pytest`
- [ ] `uv run ruff check .`
- [ ] `uv run ruff format --check .`
- [ ] `uv run mypy src/finassert`
- [ ] `uv run mkdocs build --strict`
- [ ] No credentials, proprietary data, or accidental generated artifacts
