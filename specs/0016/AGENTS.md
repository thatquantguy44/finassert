# Spec 0016 agent instructions

Follow [the shared spec instructions](../AGENTS.md). Read [spec.md](spec.md),
[contracts.md](contracts.md), [tasks.md](tasks.md), [plan.md](plan.md) and the newest
[handoff](handoff.md) before implementation.

Scope: the proposed live Excel validation workflow. Primary areas are web/excel.js,
web/app.js, the Python web/Excel bridge, artifact source context, build scripts and
Office stand-in/browser tests. Read owning 0011/0005/0007 instructions when changing
their shared contracts; 0013 continues to own file readers.

- This workspace currently records proposed behavior. Do not claim real Excel
  support, API availability, performance or completed work without actual evidence.
- Keep one explicit source, generation-safe operations, and freshness separate from
  financial outcomes. Missing events never authorize trusting stale stored data.
- Preserve source cells, row identity, exact numerics, diagnostic caps and core
  pass/fail/error/skip/severity behavior. Do not implement financial rules in JS.
- Use stable Office APIs and explicit date interpretation. Feature probes and the
  Mac test establish support; a permissive stub is not proof of host behavior.
- Never infer a cell from a business row key, fabricate a missing-group address,
  overwrite a bound source, or clear arbitrary sheets based on name alone.
- Follow the ordered tasks and record focused evidence before promotion. Manual
  host acceptance cannot be checked off by CI. Keep evidence synthetic and bounded.

No sub-agent delegation is requested by this workspace. Use [plan.md](plan.md) for
verification; update local/master handoffs and the project roadmap at completion.
