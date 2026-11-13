# 0003 — Numerical tolerances: plan

[Spec](spec.md) · [Plan](plan.md) · [Tasks](tasks.md) · [Roadmap](roadmap.md) ·
[Contracts](contracts.md) · [Handoff](handoff.md) · [Agent instructions](AGENTS.md)

1. Preserve the documented symmetric tolerance equation and Decimal conversion behavior.
2. Extend boundary and mixed-numeric coverage using bounded strategies from 0009.
3. Keep unit-aware materiality and optimized kernels behind their dependency milestones.

Implementation areas: [src/finassert/numerical](../../src/finassert/numerical),
[tests/unit/test_tolerances.py](../../tests/unit/test_tolerances.py).

Dependencies and acceptance requirements remain in
[spec.md](spec.md#dependencies-on-other-specifications).

Verification from the repository root:

```bash
PYTHONPATH=src .venv/bin/python -m pytest -q tests/unit/test_tolerances.py tests/unit/test_portfolio.py tests/property
```

This command covers the existing baseline. Add focused coverage for new behavior as
tasks are implemented.
