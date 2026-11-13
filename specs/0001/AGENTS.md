# Spec 0001 agent instructions

Follow [the shared spec instructions](../AGENTS.md). Read this folder's [spec](spec.md),
[contracts](contracts.md), [tasks](tasks.md), and newest [handoff](handoff.md) before
related implementation work.

Scope: Core validation engine. Relevant implementation areas:
[src/finassert/core](../../src/finassert/core).

Preserve these review constraints:

- Rule execution order and result order match; each rule executes once.
- Failures, errors, and skips remain distinct. Preserve main's severity-based
  report blocking: evaluation errors always block; warning/info failures are
  findings that do not block at the default threshold.
- The engine does not coerce, normalize, or mutate caller data.

Use [plan.md](plan.md) for the approach and its verification command. Update task
evidence and the local handoff when work finishes; reflect cross-spec effects in the
master handoff.
