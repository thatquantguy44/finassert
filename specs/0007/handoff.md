# 0007 — CLI and pipeline integration: handoff

[Spec](spec.md) · [Plan](plan.md) · [Tasks](tasks.md) · [Roadmap](roadmap.md) ·
[Contracts](contracts.md) · [Handoff](handoff.md) · [Agent instructions](AGENTS.md)

## Current state

- Status: Proposed.
- Implementation/reference areas: [pyproject.toml](../../pyproject.toml),
  [src/finassert/registry](../../src/finassert/registry),
  [src/finassert/reporting](../../src/finassert/reporting),
  [docs/examples/pipeline-validation.md](../../docs/examples/pipeline-validation.md).
- Remaining work and known gaps: [tasks.md](tasks.md).
- Next step: Freeze the versioned artifact envelope with 0005 and factory/configuration
  contracts with 0006.

## Entries

### 2026-11-13 — Numbered spec workspace created

- **Branch:** `docs/spec-0011-excel`.
- **Done:** Moved the original spec verbatim from
  `specs/0007-cli-and-pipeline-integration.md` to `spec.md`; added plan, task, roadmap,
  contract, agent, and handoff files.
- **Not done / partial:** Runtime implementation and existing spec status are unchanged.
  Open tasks are not claimed complete.
- **Decisions:** Requirements remain canonical in `spec.md`; companion files track
  execution and evidence. Earlier project history remains in the [master
  handoff](../../docs/handoff.md).
- **Verify with:** Use [plan.md](plan.md) for baseline checks; documentation migration
  checks are recorded in the master handoff.
- **Next step:** Start with the first unchecked item in [tasks.md](tasks.md).
