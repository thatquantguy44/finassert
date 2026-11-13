# 0001 — Core validation engine: plan

[Spec](spec.md) · [Plan](plan.md) · [Tasks](tasks.md) · [Roadmap](roadmap.md) ·
[Contracts](contracts.md) · [Handoff](handoff.md) · [Agent instructions](AGENTS.md)

1. Retain the existing sequential engine and initial models as the baseline.
2. Close acceptance-test gaps and resolve any result-immutability ambiguity in the spec
   before changing the public model.
3. Coordinate reporting changes with 0005; keep context and policy hooks outside the
   current implementation scope.

Implementation areas: [src/finassert/core](../../src/finassert/core).

Dependencies and acceptance requirements remain in
[spec.md](spec.md#dependencies-on-other-specifications).

Verification from the repository root:

```bash
PYTHONPATH=src .venv/bin/python -m pytest -q tests/unit/test_engine.py
```

This command covers the existing baseline. Add focused coverage for new behavior as
tasks are implemented.
