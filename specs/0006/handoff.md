# 0006 — Rule registry and custom rules: handoff

[Spec](spec.md) · [Plan](plan.md) · [Tasks](tasks.md) · [Roadmap](roadmap.md) ·
[Contracts](contracts.md) · [Handoff](handoff.md) · [Agent instructions](AGENTS.md)

## Current state

- Status: Implemented (initial).
- Implementation/reference areas:
  [src/finassert/registry](../../src/finassert/registry),
  [src/finassert/rules/custom.py](../../src/finassert/rules/custom.py).
- Remaining work and known gaps: [tasks.md](tasks.md).
- Next step: Audit coverage for rich/invalid callable results, duplicate/replacement
  registration, sorted IDs, and registry independence.

## Entries

### 2026-11-13 — Numbered spec workspace created

- **Branch:** `docs/spec-0011-excel`.
- **Done:** Moved the original spec verbatim from
  `specs/0006-rule-registry-and-custom-rules.md` to `spec.md`; added plan, task,
  roadmap, contract, agent, and handoff files.
- **Not done / partial:** Runtime implementation and existing spec status are unchanged.
  Open tasks are not claimed complete.
- **Decisions:** Requirements remain canonical in `spec.md`; companion files track
  execution and evidence. Earlier project history remains in the [master
  handoff](../../docs/handoff.md).
- **Verify with:** Use [plan.md](plan.md) for baseline checks; documentation migration
  checks are recorded in the master handoff.
- **Next step:** Start with the first unchecked item in [tasks.md](tasks.md).
