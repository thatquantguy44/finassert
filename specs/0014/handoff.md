# 0014 — Seven-priority delivery: handoff

## Current state

- **Branch:** `feature/seven-priority-roadmap`.
- **Latest delivered work:** Bounded structured diagnostics and strict versioned artifacts.
- **Evidence:** 754 full-suite tests passed; the remaining MCP subprocess passed after repairing the macOS hidden flag on the editable-install path; Ruff and mypy passed.
- **Next step:** Gate 4: verify existing public cash and NAV contracts across adapters.

## Entries

### 2026-11-13 — Gate 3: Bounded structured diagnostics and strict versioned artifacts

- **Branch / PR:** `feature/seven-priority-roadmap`, [draft PR #17](https://github.com/thatquantguy44/finassert/pull/17).
- **Done:** Bounded structured diagnostics and strict versioned artifacts.
- **Evidence:** 754 full-suite tests passed; the remaining MCP subprocess passed after repairing the macOS hidden flag on the editable-install path; Ruff and mypy passed.
- **Next step:** Gate 4: verify existing public cash and NAV contracts across adapters.

### 2026-11-13 — Gate 2: Adapter length enforcement and shared contracts

- **Branch / PR:** `feature/seven-priority-roadmap`, [draft PR #17](https://github.com/thatquantguy44/finassert/pull/17).
- **Done:** Adapter length enforcement and shared contracts.
- **Evidence:** 86 adapter tests passed across six input forms, including generated workbook/pandas equivalence; Ruff and mypy passed.
- **Next step:** Gate 3: bounded diagnostics and strict artifacts.

### 2026-11-13 — Gate 1: Excel formula and error-cell correctness

- **Branch / PR:** `feature/seven-priority-roadmap`, [draft PR #17](https://github.com/thatquantguy44/finassert/pull/17).
- **Done:** Excel formula and error-cell correctness.
- **Evidence:** 86 focused Excel tests, Ruff, and mypy passed; six regressions failed before the fix.
- **Next step:** Gate 2: enforce adapter lengths and shared contracts.

### 2026-11-13 — Current main preserved and baseline verified

- **Done:** Integrated main at `a3f0a3e`, retaining public reconciliation,
  policies/CLI, Parquet, browser, assistant, Excel add-in, and treasury features.
- **Numbering:** Main owns 0011 (interfaces) and 0012 (treasury). The unpublished
  workbook-file proposal is 0013 and this delivery tracker is 0014.
- **Compatibility:** The optional workbook reader remains available through
  `finassert.excel`; its implementation lives in `finassert.workbook` alongside
  main's selected-range API. Existing severity-based blocking is preserved.
- **Verification:** 673 tests passed, mypy passed, strict docs and local link
  targets passed. Full tests required localhost socket access for existing
  server tests. The initial sandbox-only failures were permission errors.
- **Next step:** Gate 1, formula/error-cell regressions and corrections.

### 2026-11-13 — Delivery branch initialized

- **Done:** Created the branch and ordered seven-gate workspace. Carried forward
  the existing reader and numbered-spec migration as the foundation.
- **Not done:** All seven implementation gates remain open.
- **Verification:** Documentation migration was checked in the preceding session;
  runtime acceptance is recorded gate by gate from this point onward.
- **Next step:** Gate 1 regression tests and Excel input fixes.
