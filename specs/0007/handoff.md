# 0007 — CLI and pipeline integration: handoff

[Spec](spec.md) · [Plan](plan.md) · [Tasks](tasks.md) · [Roadmap](roadmap.md) ·
[Contracts](contracts.md) · [Handoff](handoff.md) · [Agent instructions](AGENTS.md)

## Current state

- **Branch:** feature/excel-diagnostic-navigation for 0016 E-05 compatibility.
- **Latest work:** Optional live artifact context/views; no CLI/file behavior change.
- **Evidence:** Full runtime 3,697 and browser 106 pass; earlier delivery evidence is historical below.
- **Next step:** Follow the master E-06 acceptance/CLI parity pickup.

## Entries

### 2026-11-15 — E-05 live artifact compatibility

Recorded optional input.excel under artifact schema 1 and canonical live views.
No CLI flag, public evaluation signature, exit-code, file-rendering or atomic
file-write change. Legacy/file regressions pass in the 3,697-test runtime suite;
full native output/CLI tie-out is an E-06 acceptance task. Follow the master order.

### 2026-11-13 — Gate 5: Atomic Excel reports and complete CLI file workflow

- **Branch / PR:** `feature/seven-priority-roadmap`, [draft PR #17](https://github.com/thatquantguy44/finassert/pull/17).
- **Done:** Atomic Excel reports and complete CLI file workflow.
- **Evidence:** 200 workbook, CLI, loader, and strict-policy tests passed; Ruff, mypy, and strict documentation build passed.
- **Next step:** Gate 6: typed money and ratios plus direct FX provenance.

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
