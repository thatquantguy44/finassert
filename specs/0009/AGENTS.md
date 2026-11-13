# Spec 0009 agent instructions

Follow [the shared spec instructions](../AGENTS.md). Read this folder's [spec](spec.md),
[contracts](contracts.md), [tasks](tasks.md), and newest [handoff](handoff.md) before
related implementation work.

Scope: Property-based testing. Relevant implementation areas:
[tests/property](../../tests/property), [tests/integration](../../tests/integration),
[.github/workflows/ci.yml](../../.github/workflows/ci.yml).

Preserve these review constraints:

- Every property states its mathematical and financial preconditions.
- Generated magnitudes, row counts, and precision are bounded.
- Property failures are reproducible; performance assertions belong to 0010 benchmarks.

Use [plan.md](plan.md) for the approach and its verification command. Update task
evidence and the local handoff when work finishes; reflect cross-spec effects in the
master handoff.
