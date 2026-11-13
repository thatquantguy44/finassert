# 0010 — Performance and batch validation: handoff

[Spec](spec.md) · [Plan](plan.md) · [Tasks](tasks.md) · [Roadmap](roadmap.md) ·
[Contracts](contracts.md) · [Handoff](handoff.md) · [Agent instructions](AGENTS.md)

## Current state

- Status: Proposed.
- Implementation/reference areas:
  [src/finassert/core/engine.py](../../src/finassert/core/engine.py),
  [src/finassert/adapters](../../src/finassert/adapters),
  [src/finassert/rules](../../src/finassert/rules).
- Remaining work and known gaps: [tasks.md](tasks.md).
- Next step: Create a reproducible synthetic corpus and scalar baselines recording
  hardware, software, shape, dtypes, and group skew.

## Entries

### 2026-11-13 — Numbered spec workspace created

- **Branch:** `docs/spec-0011-excel`.
- **Done:** Moved the original spec verbatim from
  `specs/0010-performance-and-batch-validation.md` to `spec.md`; added plan, task,
  roadmap, contract, agent, and handoff files.
- **Not done / partial:** Runtime implementation and existing spec status are unchanged.
  Open tasks are not claimed complete.
- **Decisions:** Requirements remain canonical in `spec.md`; companion files track
  execution and evidence. Earlier project history remains in the [master
  handoff](../../docs/handoff.md).
- **Verify with:** Use [plan.md](plan.md) for baseline checks; documentation migration
  checks are recorded in the master handoff.
- **Next step:** Start with the first unchecked item in [tasks.md](tasks.md).
