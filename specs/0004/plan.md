# 0004 — DataFrame adapters: plan

[Spec](spec.md) · [Plan](plan.md) · [Tasks](tasks.md) · [Roadmap](roadmap.md) ·
[Contracts](contracts.md) · [Handoff](handoff.md) · [Agent instructions](AGENTS.md)

1. Enforce extraction invariants before rule evaluation, including per-column
   value/label lengths.
2. Parameterize common contract cases across supported inputs and add bounded
   adapter-equivalence properties with 0009.
3. Resolve ordered aggregation and currency preconditions before promoting the private
   cash rule; keep Polars deferred.

Implementation areas: [src/finassert/adapters](../../src/finassert/adapters),
[src/finassert/rules/grouped.py](../../src/finassert/rules/grouped.py),
[docs/design/grouped-validation.md](../../docs/design/grouped-validation.md).

Dependencies and acceptance requirements remain in
[spec.md](spec.md#dependencies-on-other-specifications).

Verification from the repository root:

```bash
PYTHONPATH=src .venv/bin/python -m pytest -q tests/unit/test_adapter_contracts.py tests/unit/test_grouped_rules.py tests/unit/test_grouped_cash_prototype.py tests/integration
```

This command covers the existing baseline. Add focused coverage for new behavior as
tasks are implemented.
