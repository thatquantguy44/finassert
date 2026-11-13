# Spec 0010 agent instructions

Follow [the shared spec instructions](../AGENTS.md). Read this folder's [spec](spec.md),
[contracts](contracts.md), [tasks](tasks.md), and newest [handoff](handoff.md) before
related implementation work.

Scope: Performance and batch validation. Relevant implementation areas:
[src/finassert/core/engine.py](../../src/finassert/core/engine.py),
[src/finassert/adapters](../../src/finassert/adapters),
[src/finassert/rules](../../src/finassert/rules).

Preserve these review constraints:

- The scalar result contract remains the reference for every optimization.
- Decimal behavior, rule order, total failure counts, and diagnostic bounds remain
  deterministic.
- Performance claims require retained benchmark evidence; proposed batch APIs remain
  private.

Use [plan.md](plan.md) for the approach and its verification command. Update task
evidence and the local handoff when work finishes; reflect cross-spec effects in the
master handoff.
