# Spec 0002 agent instructions

Follow [the shared spec instructions](../AGENTS.md). Read this folder's [spec](spec.md),
[contracts](contracts.md), [tasks](tasks.md), and newest [handoff](handoff.md) before
related implementation work.

Scope: Financial invariants. Relevant implementation areas:
[src/finassert/rules](../../src/finassert/rules),
[docs/design/grouped-validation.md](../../docs/design/grouped-validation.md).

Preserve these review constraints:

- Every public rule defines equation, applicability, signs, units, null/empty behavior,
  and tolerance basis.
- Missing columns or incompatible units error; financial invariant violations fail.
- Mixed currencies require explicit grouping or conversion provenance.

Use [plan.md](plan.md) for the approach and its verification command. Update task
evidence and the local handoff when work finishes; reflect cross-spec effects in the
master handoff.
