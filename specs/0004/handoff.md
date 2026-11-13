# 0004 — DataFrame adapters: handoff

[Spec](spec.md) · [Plan](plan.md) · [Tasks](tasks.md) · [Roadmap](roadmap.md) ·
[Contracts](contracts.md) · [Handoff](handoff.md) · [Agent instructions](AGENTS.md)

## Current state

- **Branch:** `feature/shared-column-reads`.
- **Latest delivered work:** Adapter length enforcement and shared contracts.
- **Evidence:** 86 adapter tests passed across six input forms, including generated workbook/pandas equivalence; Ruff and mypy passed.
- **Next step:** Review the shared-read parity evidence under spec 0010; further
  extensions remain proposed.

## Entries

### 2026-11-13 — Shared-read parity under spec 0010

- **Branch:** `feature/shared-column-reads`.
- **Done:** Private shared reads retain at most one column for eligible built-in
  checks on plain dictionaries/native pandas frames. Custom sources and rules,
  lazy iterables and one-shot columns retain scalar reads. Native labels and
  explicit row keys remain unchanged; reset-hook mutations clear retained values.
- **Evidence:** Full 3,484-test suite passed, including 2,644 captured-reference
  tests and focused label/mutation/nested/concurrent regressions.
- **Details:** [Spec 0010 handoff](../0010/handoff.md) and
  [measurements](../0010/artifacts/README.md#shared-column-reads).

### 2026-11-13 — Gate 2: Adapter length enforcement and shared contracts

- **Branch / PR:** `feature/seven-priority-roadmap`, [draft PR #17](https://github.com/thatquantguy44/finassert/pull/17).
- **Done:** Adapter length enforcement and shared contracts.
- **Evidence:** 86 adapter tests passed across six input forms, including generated workbook/pandas equivalence; Ruff and mypy passed.
- **Next step:** Gate 3: bounded diagnostics and strict artifacts.

### 2026-11-13 — Numbered spec workspace created

- **Branch:** `docs/spec-0011-excel`.
- **Done:** Moved the original spec verbatim from `specs/0004-dataframe-adapters.md` to
  `spec.md`; added plan, task, roadmap, contract, agent, and handoff files.
- **Not done / partial:** Runtime implementation and existing spec status are unchanged.
  Open tasks are not claimed complete.
- **Decisions:** Requirements remain canonical in `spec.md`; companion files track
  execution and evidence. Earlier project history remains in the [master
  handoff](../../docs/handoff.md).
- **Verify with:** Use [plan.md](plan.md) for baseline checks; documentation migration
  checks are recorded in the master handoff.
- **Next step:** Start with the first unchecked item in [tasks.md](tasks.md).
