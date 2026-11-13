# 0014 — Seven-priority delivery: handoff

## Current state

- **Branch:** `feature/seven-priority-roadmap`.
- **Gate:** 1 of 7; no implementation gate complete yet.
- **Next step:** Fix trailing uncached formula detection before blank-row trimming.

## Entries

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
