# 0008 — Financial units and currencies: handoff

[Spec](spec.md) · [Plan](plan.md) · [Tasks](tasks.md) · [Roadmap](roadmap.md) ·
[Contracts](contracts.md) · [Handoff](handoff.md) · [Agent instructions](AGENTS.md)

## Current state

- **Branch:** `feature/shared-column-reads`.
- **Latest delivered work:** Typed quantities, explicit direct FX, and retained provenance.
- **Evidence:** 86 unit, diagnostics, accounting, and property tests passed; Ruff, mypy, strict docs, and whitespace checks passed.
- **Next step:** Review the shared-read parity evidence under spec 0010; further
  extensions remain proposed.

## Entries

### 2026-11-13 — Shared-read parity under spec 0010

- **Branch:** `feature/shared-column-reads`.
- **Done:** Verified that private shared reads preserve per-rule unit/FX metadata.
  MoneySource and arbitrary context-aware sources continue scalar reads; reset
  hooks clear retained values before running. No unit or conversion contract changed.
- **Evidence:** Full 3,484-test suite passed; focused repeated-source tests compare
  complete cached/scalar reports and distinct FX records for a/b/a column reads.
- **Details:** [Spec 0010 handoff](../0010/handoff.md) and
  [measurements](../0010/artifacts/README.md#shared-column-reads).

### 2026-11-13 — Gate 6: Typed quantities, explicit direct FX, and retained provenance

- **Branch / PR:** `feature/seven-priority-roadmap`, [draft PR #17](https://github.com/thatquantguy44/finassert/pull/17).
- **Done:** Typed quantities, explicit direct FX, and retained provenance.
- **Evidence:** 86 unit, diagnostics, accounting, and property tests passed; Ruff, mypy, strict docs, and whitespace checks passed.
- **Next step:** Gate 7: retain reproducible runtime and peak-memory baselines.

### 2026-11-13 — Numbered spec workspace created

- **Branch:** `docs/spec-0011-excel`.
- **Done:** Moved the original spec verbatim from
  `specs/0008-financial-units-and-currencies.md` to `spec.md`; added plan, task,
  roadmap, contract, agent, and handoff files.
- **Not done / partial:** Runtime implementation and existing spec status are unchanged.
  Open tasks are not claimed complete.
- **Decisions:** Requirements remain canonical in `spec.md`; companion files track
  execution and evidence. Earlier project history remains in the [master
  handoff](../../docs/handoff.md).
- **Verify with:** Use [plan.md](plan.md) for baseline checks; documentation migration
  checks are recorded in the master handoff.
- **Next step:** Start with the first unchecked item in [tasks.md](tasks.md).
