# 0009 — Property-based testing: plan

[Spec](spec.md) · [Plan](plan.md) · [Tasks](tasks.md) · [Roadmap](roadmap.md) ·
[Contracts](contracts.md) · [Handoff](handoff.md) · [Agent instructions](AGENTS.md)

1. Extract reusable bounded strategies from the initial allocation property.
2. Add tolerance and adapter properties before relying on expanded financial rules.
3. Grow identity and FX properties with the corresponding implementations, preserving
   reproducible counterexamples.

Implementation areas: [tests/property](../../tests/property),
[tests/integration](../../tests/integration),
[.github/workflows/ci.yml](../../.github/workflows/ci.yml).

Dependencies and acceptance requirements remain in
[spec.md](spec.md#dependencies-on-other-specifications).

Verification from the repository root:

```bash
PYTHONPATH=src .venv/bin/python -m pytest -q tests/property tests/integration
```

This command covers the existing baseline. Add focused coverage for new behavior as
tasks are implemented.
