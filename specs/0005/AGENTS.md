# Spec 0005 agent instructions

Follow [the shared spec instructions](../AGENTS.md). Read this folder's [spec](spec.md),
[contracts](contracts.md), [tasks](tasks.md), and newest [handoff](handoff.md) before
related implementation work.

Scope: Reporting and diagnostics. Relevant implementation areas:
[src/finassert/core/models.py](../../src/finassert/core/models.py),
[src/finassert/reporting](../../src/finassert/reporting),
[src/finassert/rules/portfolio.py](../../src/finassert/rules/portfolio.py),
[src/finassert/rules/arithmetic.py](../../src/finassert/rules/arithmetic.py).

Preserve these review constraints:

- Formatters are views over canonical results and do not change validation truth.
- Decimal precision is retained as text, and output is strict-JSON compatible.
- Diagnostic counts remain complete even when row/group details are capped.

Use [plan.md](plan.md) for the approach and its verification command. Update task
evidence and the local handoff when work finishes; reflect cross-spec effects in the
master handoff.
