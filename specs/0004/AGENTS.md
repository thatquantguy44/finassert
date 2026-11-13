# Spec 0004 agent instructions

Follow [the shared spec instructions](../AGENTS.md). Read this folder's [spec](spec.md),
[contracts](contracts.md), [tasks](tasks.md), and newest [handoff](handoff.md) before
related implementation work.

Scope: DataFrame adapters. Relevant implementation areas:
[src/finassert/adapters](../../src/finassert/adapters),
[src/finassert/rules/grouped.py](../../src/finassert/rules/grouped.py),
[docs/design/grouped-validation.md](../../docs/design/grouped-validation.md).

Preserve these review constraints:

- Column values and labels have equal length, and multi-column native labels align.
- Adapters preserve dtypes, input order, duplicate labels, and caller data.
- Grouped reductions are explicitly configured. Public FIRST/LAST rules require
  an explicit ordering column; retain main's implemented ordering contract.

Use [plan.md](plan.md) for the approach and its verification command. Update task
evidence and the local handoff when work finishes; reflect cross-spec effects in the
master handoff.
