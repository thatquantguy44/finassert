# Spec 0006 agent instructions

Follow [the shared spec instructions](../AGENTS.md). Read this folder's [spec](spec.md),
[contracts](contracts.md), [tasks](tasks.md), and newest [handoff](handoff.md) before
related implementation work.

Scope: Rule registry and custom rules. Relevant implementation areas:
[src/finassert/registry](../../src/finassert/registry),
[src/finassert/rules/custom.py](../../src/finassert/rules/custom.py).

Preserve these review constraints:

- Registries are caller-owned; duplicate registration requires explicit replacement.
- Callable results preserve rule identity and engine error semantics.
- Configuration lookup does not imply permission to load arbitrary external code.

Use [plan.md](plan.md) for the approach and its verification command. Update task
evidence and the local handoff when work finishes; reflect cross-spec effects in the
master handoff.
