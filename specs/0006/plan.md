# 0006 — Rule registry and custom rules: plan

[Spec](spec.md) · [Plan](plan.md) · [Tasks](tasks.md) · [Roadmap](roadmap.md) ·
[Contracts](contracts.md) · [Handoff](handoff.md) · [Agent instructions](AGENTS.md)

1. Preserve explicit local instance registration and callable execution semantics.
2. Define factory descriptors and validation schemas alongside the CLI policy format in
   0007.
3. Validate namespacing and collisions without introducing import-time global
   registration or automatic discovery.

Implementation areas: [src/finassert/registry](../../src/finassert/registry),
[src/finassert/rules/custom.py](../../src/finassert/rules/custom.py).

Dependencies and acceptance requirements remain in
[spec.md](spec.md#dependencies-on-other-specifications).

Verification from the repository root:

```bash
PYTHONPATH=src .venv/bin/python -m pytest -q tests/unit/test_engine.py
```

This command covers the existing baseline. Add focused coverage for new behavior as
tasks are implemented.
