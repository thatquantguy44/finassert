# 0007 — CLI and pipeline integration: plan

[Spec](spec.md) · [Plan](plan.md) · [Tasks](tasks.md) · [Roadmap](roadmap.md) ·
[Contracts](contracts.md) · [Handoff](handoff.md) · [Agent instructions](AGENTS.md)

1. Settle artifact, policy, and factory schemas before publishing a CLI contract.
2. Implement the minimal JSON/CSV path and explicit exit-code precedence using the
   existing engine.
3. Verify subprocess behavior and atomic artifacts, then extend input/output formats and
   integration recipes.

Implementation areas: [pyproject.toml](../../pyproject.toml),
[src/finassert/registry](../../src/finassert/registry),
[src/finassert/reporting](../../src/finassert/reporting),
[docs/examples/pipeline-validation.md](../../docs/examples/pipeline-validation.md).

Dependencies and acceptance requirements remain in
[spec.md](spec.md#dependencies-on-other-specifications).

Verification from the repository root:

```bash
PYTHONPATH=src .venv/bin/python -m pytest -q
```

This command covers the existing baseline. Add focused coverage for new behavior as
tasks are implemented.
