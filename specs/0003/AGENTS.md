# Spec 0003 agent instructions

Follow [the shared spec instructions](../AGENTS.md). Read this folder's [spec](spec.md),
[contracts](contracts.md), [tasks](tasks.md), and newest [handoff](handoff.md) before
related implementation work.

Scope: Numerical tolerances. Relevant implementation areas:
[src/finassert/numerical](../../src/finassert/numerical),
[tests/unit/test_tolerances.py](../../tests/unit/test_tolerances.py).

Preserve these review constraints:

- Closeness is abs(a-e) <= absolute + relative * max(abs(a), abs(e)).
- Tolerance components are finite and nonnegative; booleans are not supported numeric
  scalars.
- Decimal operands never convert to binary float; non-finite operands never compare
  close.

Use [plan.md](plan.md) for the approach and its verification command. Update task
evidence and the local handoff when work finishes; reflect cross-spec effects in the
master handoff.
