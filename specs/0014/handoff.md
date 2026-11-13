# 0014 — Seven-priority delivery: handoff

## Current state

- **Branch:** `feature/seven-priority-roadmap`.
- **Delivery:** Seven gates complete; 807 tests and all local/package checks passed.
- **PR:** Draft #17; no merge or release.
- **Next step:** Review the pushed PR and CI results.

## Entries

### 2026-11-13 — Seven priorities delivered and locally verified

- **Branch / PR:** `feature/seven-priority-roadmap`, [draft PR #17](https://github.com/thatquantguy44/finassert/pull/17); issue #16.
- **Done:** All seven ordered gates have implementation and evidence. Retained
  48-case scalar timing/memory/CPU profiles, source digest, and repeat/adapter
  fingerprints. Preserved existing main features and numbered-spec history.
- **Compatibility review:** Explicit custom diagnostic collections survive
  normalization; arbitrary objects retain string fallback unless explicitly
  marked as supported financial values. Added regressions for both behaviors.
- **Verification:** 807 tests passed. Ruff lint/format, mypy (57 modules), strict
  documentation, 783 local links/anchors, author policy (57 history records),
  whitespace, source digest, wheel/sdist build, and fresh-environment installed
  CLI/unit/FX/workbook workflows passed.
- **Not done:** No merge or release. Broader proposed catalog, redaction,
  visibility, and optimization work remains in owning spec tasks. Remote CI is
  checked against the pushed final head on the draft PR.
- **Next step:** Review draft PR #17 and its CI results.

### 2026-11-13 — Gate 7: Retained reproducible scalar timing, memory, and CPU profiles

- **Branch / PR:** `feature/seven-priority-roadmap`, [draft PR #17](https://github.com/thatquantguy44/finassert/pull/17).
- **Done:** Retained reproducible scalar timing, memory, and CPU profiles.
- **Evidence:** 48 cases across three sizes, two numeric domains, two adapters, and four populations retained; repeated/cross-adapter fingerprints and the delivered-source digest match; benchmark smoke test passed.
- **Next step:** Finish final regression, package, and draft PR verification.

### 2026-11-13 — Gate 6: Typed quantities, explicit direct FX, and retained provenance

- **Branch / PR:** `feature/seven-priority-roadmap`, [draft PR #17](https://github.com/thatquantguy44/finassert/pull/17).
- **Done:** Typed quantities, explicit direct FX, and retained provenance.
- **Evidence:** 86 unit, diagnostics, accounting, and property tests passed; Ruff, mypy, strict docs, and whitespace checks passed.
- **Next step:** Gate 7: retain reproducible runtime and peak-memory baselines.

### 2026-11-13 — Gate 5: Atomic Excel reports and complete CLI file workflow

- **Branch / PR:** `feature/seven-priority-roadmap`, [draft PR #17](https://github.com/thatquantguy44/finassert/pull/17).
- **Done:** Atomic Excel reports and complete CLI file workflow.
- **Evidence:** 200 workbook, CLI, loader, and strict-policy tests passed; Ruff, mypy, and strict documentation build passed.
- **Next step:** Gate 6: typed money and ratios plus direct FX provenance.

### 2026-11-13 — Gate 4: Verified public cash and NAV reconciliation across adapters

- **Branch / PR:** `feature/seven-priority-roadmap`, [draft PR #17](https://github.com/thatquantguy44/finassert/pull/17).
- **Done:** Verified public cash and NAV reconciliation across adapters.
- **Evidence:** 117 accounting, financial property, and shared-adapter tests passed, including sign, currency, valuation-date, materiality, ordering, and signed-liability cases.
- **Next step:** Gate 5: Excel report writer and CLI workbook workflow.

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
