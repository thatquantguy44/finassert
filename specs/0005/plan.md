# 0005 — Reporting and diagnostics: plan

[Spec](spec.md) · [Plan](plan.md) · [Tasks](tasks.md) · [Roadmap](roadmap.md) ·
[Contracts](contracts.md) · [Handoff](handoff.md) · [Agent instructions](AGENTS.md)

1. Specify common bounded diagnostics and resolve non-finite serialization behavior.
2. Apply the contract to existing built-ins and verify deterministic strict JSON and
   useful text output.
3. Define the artifact envelope with 0007, then support Excel Diagnostics output in 0011
   and later redaction hooks.

Implementation areas:
[src/finassert/core/models.py](../../src/finassert/core/models.py),
[src/finassert/reporting](../../src/finassert/reporting),
[src/finassert/rules/portfolio.py](../../src/finassert/rules/portfolio.py),
[src/finassert/rules/arithmetic.py](../../src/finassert/rules/arithmetic.py).

Dependencies and acceptance requirements remain in
[spec.md](spec.md#dependencies-on-other-specifications).

Verification from the repository root:

```bash
PYTHONPATH=src .venv/bin/python -m pytest -q tests/unit/test_engine.py tests/unit/test_portfolio.py tests/unit/test_arithmetic.py tests/unit/test_accounting.py
```

This command covers the existing baseline. Add focused coverage for new behavior as
tasks are implemented.
