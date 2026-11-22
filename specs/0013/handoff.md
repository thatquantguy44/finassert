# 0013 — Excel workbook integration: handoff

[Spec](spec.md) · [Plan](plan.md) · [Tasks](tasks.md) · [Roadmap](roadmap.md) ·
[Contracts](contracts.md) · [Handoff](handoff.md) · [Agent instructions](AGENTS.md)

## Current state

- **Branch:** `spec/0020-quant-model-assurance` for the cross-spec report update.
- **Delivered:** The XLSX `Policy` sheet now exports policy identity plus configured
  and effective rule parameters, including defaults, exact Decimal text, and
  formula-like strings as literal values.
- **Evidence:** Full suite 3,785 passed; 111 Excel browser-job tests skipped.
  Workbook report and policy-parameter tests pass; see [0020 handoff](../0020/handoff.md).
- **Next:** Follow the [master handoff](../../docs/handoff.md#next-up); live Excel
  behavior remains separate under 0011.

## Entries

### 2026-11-21 — Add XLSX policy parameter sheet

The report workbook includes a `Policy` sheet with name, description, version,
digest, assumptions, and one row per configured rule. Configured and effective
parameter maps use canonical JSON text; exact Decimal values and formula-like
strings remain literal. The full test suite passes (3,785 passed, 111 Excel
browser-job tests skipped), including XLSX round-trip, formula-injection and
policy-sheet coverage. The 0013 file-reader requirements are complete.

### 2026-11-13 — Slice 3 workbook hardening

Both readers inspect selected-sheet visibility without writable workbook loading.
Default include retains every physical row identity; reject refuses hidden selected
inputs. Counts and 20-example samples are copied into CLI artifact input.workbook.
Merged headers and uncached header formulas error; explicit row bounds still exclude
totals. Cached OOXML formulas and 1900/1904 epoch fixtures pass without modifying
source bytes. 200 focused tests passed, including CLI subprocesses; Ruff/mypy passed.
Generated header/label properties remain covered by the shared adapter suite.

### 2026-11-13 — Gate 5: Atomic Excel reports and complete CLI file workflow

- **Branch / PR:** `feature/seven-priority-roadmap`, [draft PR #17](https://github.com/thatquantguy44/finassert/pull/17).
- **Done:** Atomic Excel reports and complete CLI file workflow.
- **Evidence:** 200 workbook, CLI, loader, and strict-policy tests passed; Ruff, mypy, and strict documentation build passed.
- **Next step:** Gate 6: typed money and ratios plus direct FX provenance.

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

### 2026-11-13 — Numbered spec workspace created

- **Branch:** `docs/spec-0011-excel`.
- **Done:** Moved the original spec verbatim from
  `specs/0011-excel-workbook-integration.md` to `spec.md`; added plan, task, roadmap,
  contract, agent, and handoff files.
- **Not done / partial:** Runtime implementation and existing spec status are unchanged.
  Open tasks are not claimed complete.
- **Decisions:** Requirements remain canonical in `spec.md`; companion files track
  execution and evidence. Earlier project history remains in the [master
  handoff](../../docs/handoff.md).
- **Verify with:** Use [plan.md](plan.md) for baseline checks; documentation migration
  checks are recorded in the master handoff.
- **Next step:** Start with the first unchecked item in [tasks.md](tasks.md).
