# Spec 0008 agent instructions

Follow [the shared spec instructions](../AGENTS.md). Read this folder's [spec](spec.md),
[contracts](contracts.md), [tasks](tasks.md), and newest [handoff](handoff.md) before
related implementation work.

Scope: Financial units and currencies. Relevant implementation areas:
[src/finassert/numerical](../../src/finassert/numerical),
[src/finassert/adapters](../../src/finassert/adapters),
[src/finassert/core/models.py](../../src/finassert/core/models.py).

Preserve these review constraints:

- Unlike currencies and incompatible dimensions cannot be combined implicitly.
- FX conversion is explicit and retains direction, source, and an aware UTC timestamp.
- Financial materiality remains distinct from currency minor-unit rounding.

Use [plan.md](plan.md) for the approach and its verification command. Update task
evidence and the local handoff when work finishes; reflect cross-spec effects in the
master handoff.
