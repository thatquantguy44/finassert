# 0002 — Financial invariants: plan

[Spec](spec.md) · [Plan](plan.md) · [Tasks](tasks.md) · [Roadmap](roadmap.md) ·
[Contracts](contracts.md) · [Handoff](handoff.md) · [Agent instructions](AGENTS.md)

1. Resolve cash promotion criteria with 0004 and bounded diagnostics with 0005.
2. Implement and validate public cash reconciliation, then NAV reconciliation, without
   silently combining currencies.
3. Expand the catalog only after each rule documents its applicability, equation, units,
   and counterexamples.

Implementation areas: [src/finassert/rules](../../src/finassert/rules),
[docs/design/grouped-validation.md](../../docs/design/grouped-validation.md).

Dependencies and acceptance requirements remain in
[spec.md](spec.md#dependencies-on-other-specifications).

Verification from the repository root:

```bash
PYTHONPATH=src .venv/bin/python -m pytest -q tests/unit/test_portfolio.py tests/unit/test_arithmetic.py tests/unit/test_accounting.py tests/property
```

This command covers the existing baseline. Add focused coverage for new behavior as
tasks are implemented.
