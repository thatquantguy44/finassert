# 0005 — Reporting and diagnostics: handoff

[Spec](spec.md) · [Plan](plan.md) · [Tasks](tasks.md) · [Roadmap](roadmap.md) ·
[Contracts](contracts.md) · [Handoff](handoff.md) · [Agent instructions](AGENTS.md)

## Current state

- **Branch:** `feature/excel-diagnostic-navigation` for the 0016 compatibility work.
- **Latest work:** E-04 consumes canonical native samples for session-only targets;
  no diagnostic or artifact schema changes. Earlier gates are historical below.
- **Evidence:** 13 identity tests and 19 E-04 browser cases pass; see
  [0016 evidence](../0016/artifacts/README.md#e-04-diagnostic-navigation).
- **Next step:** Follow the [master handoff](../../docs/handoff.md#next-up),
  beginning with E-05 source provenance/safe output and its reporting contract.

## Entries

### 2026-11-15 — E-04 diagnostic compatibility

Recorded the private navigation response boundary. E-04 uses only canonical
retained samples, resolves labels before serialization, preserves complete counts
and caps, and leaves artifact schema 1 unchanged. Identity tests compare samples
to exported canonical diagnostics and cover collisions/zero caps. No financial
semantics or formatter rewrite. Current project ordering is the master handoff.

### 2026-11-13 — Gate 3: Bounded structured diagnostics and strict versioned artifacts

- **Branch / PR:** `feature/seven-priority-roadmap`, [draft PR #17](https://github.com/thatquantguy44/finassert/pull/17).
- **Done:** Bounded structured diagnostics and strict versioned artifacts.
- **Evidence:** 754 full-suite tests passed; the remaining MCP subprocess passed after repairing the macOS hidden flag on the editable-install path; Ruff and mypy passed.
- **Next step:** Gate 4: verify existing public cash and NAV contracts across adapters.

### 2026-11-13 — Numbered spec workspace created

- **Branch:** `docs/spec-0011-excel`.
- **Done:** Moved the original spec verbatim from
  `specs/0005-reporting-and-diagnostics.md` to `spec.md`; added plan, task, roadmap,
  contract, agent, and handoff files.
- **Not done / partial:** Runtime implementation and existing spec status are unchanged.
  Open tasks are not claimed complete.
- **Decisions:** Requirements remain canonical in `spec.md`; companion files track
  execution and evidence. Earlier project history remains in the [master
  handoff](../../docs/handoff.md).
- **Verify with:** Use [plan.md](plan.md) for baseline checks; documentation migration
  checks are recorded in the master handoff.
- **Next step:** Start with the first unchecked item in [tasks.md](tasks.md).
