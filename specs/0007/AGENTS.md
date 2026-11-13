# Spec 0007 agent instructions

Follow [the shared spec instructions](../AGENTS.md). Read this folder's [spec](spec.md),
[contracts](contracts.md), [tasks](tasks.md), and newest [handoff](handoff.md) before
related implementation work.

Scope: CLI and pipeline integration. Relevant implementation areas:
[pyproject.toml](../../pyproject.toml),
[src/finassert/registry](../../src/finassert/registry),
[src/finassert/reporting](../../src/finassert/reporting),
[docs/examples/pipeline-validation.md](../../docs/examples/pipeline-validation.md).

Preserve these review constraints:

- Exit codes distinguish pass/skip, invariant failure, evaluation error,
  usage/configuration error, and I/O failure.
- Configuration is versioned, unknown keys fail, and rule factories are allowlisted.
- Evaluation artifacts use 0005 and are written atomically; no interactive prompts are
  required.

Use [plan.md](plan.md) for the approach and its verification command. Update task
evidence and the local handoff when work finishes; reflect cross-spec effects in the
master handoff.
