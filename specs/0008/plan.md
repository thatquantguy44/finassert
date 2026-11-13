# 0008 — Financial units and currencies: plan

[Spec](spec.md) · [Plan](plan.md) · [Tasks](tasks.md) · [Roadmap](roadmap.md) ·
[Contracts](contracts.md) · [Handoff](handoff.md) · [Agent instructions](AGENTS.md)

1. Review the small dimensional model before adding runtime types.
2. Implement Money and ratio units, followed by direct FX conversion with explicit
   provenance.
3. Integrate reporting and rule preconditions; leave conversion paths and rate
   acquisition deferred.

Implementation areas: [src/finassert/numerical](../../src/finassert/numerical),
[src/finassert/adapters](../../src/finassert/adapters),
[src/finassert/core/models.py](../../src/finassert/core/models.py).

Dependencies and acceptance requirements remain in
[spec.md](spec.md#dependencies-on-other-specifications).

Verification from the repository root:

```bash
PYTHONPATH=src .venv/bin/python -m pytest -q tests/unit/test_tolerances.py tests/property
```

This command covers the existing baseline. Add focused coverage for new behavior as
tasks are implemented.
