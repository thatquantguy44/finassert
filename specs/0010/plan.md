# 0010 — Performance and batch validation: plan

[Spec](spec.md) · [Plan](plan.md) · [Tasks](tasks.md) · [Roadmap](roadmap.md) ·
[Contracts](contracts.md) · [Handoff](handoff.md) · [Agent instructions](AGENTS.md)

1. Establish reproducible timing and peak-memory baselines for ordinary check.
2. Profile the measured bottlenecks and choose the smallest justified private
   optimization.
3. Verify parity across numeric types and adapters before considering batch APIs or
   parallel execution.

Implementation areas:
[src/finassert/core/engine.py](../../src/finassert/core/engine.py),
[src/finassert/adapters](../../src/finassert/adapters),
[src/finassert/rules](../../src/finassert/rules).

Dependencies and acceptance requirements remain in
[spec.md](spec.md#dependencies-on-other-specifications).

Verification from the repository root:

```bash
PYTHONPATH=src .venv/bin/python -m pytest -q
```

This command covers the existing baseline. Add focused coverage for new behavior as
tasks are implemented.
