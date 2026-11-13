# Master handoff log

Single running record of work handed between sessions, agents, and people.
Newest entry first. Add an entry at the end of every working session; do not
rewrite old entries (append a correction instead).

## How to use

1. Read **Current state** and the newest entry before starting.
2. Pick the top item under **Next up**, or the item the previous entry names.
3. On finishing, copy the **Entry template**, fill it in, and put it directly
   under the `Entries` heading. Update **Current state** and **Next up**.
4. Keep entries factual: link specs, PRs, and commits instead of restating them.
5. Spec-specific plans, tasks, contracts, and session details live in the numbered
   `specs/NNNN/` workspaces. This log retains project-wide state and cross-spec
   decisions; see the [spec catalog](https://github.com/thatquantguy44/finassert/blob/main/specs/README.md).

## Current state

- **Branch / PR:** `feature/bounded-diagnostic-memory`, [draft PR #18](https://github.com/thatquantguy44/finassert/pull/18).
- **Last recorded main merge:** PR #17, seven-priority delivery (`5ec9959`).
- **Delivery:** Spec 0010 now bounds diagnostic retention during scalar evaluation;
  all failures are counted and complete reference reports are preserved. Dense
  100,000-row failures use 4.58 MiB of Python validation peak, down from 22.88 MiB.
- **Evidence:** 2,144 tests, 1,322 reference comparisons, and all 48 benchmark
  fingerprints match. See the [local handoff](https://github.com/thatquantguy44/finassert/blob/main/specs/0010/handoff.md) and
  [retained measurements](https://github.com/thatquantguy44/finassert/blob/main/specs/0010/artifacts/README.md).
- **Open blockers:** None for bounded diagnostic evaluation. Broader proposed
  work remains unchecked in its owning spec tasks.

## Next up

1. Review the bounded-diagnostic branch and retained correctness/memory evidence.
2. Use updated spec 0010 profiles before selecting shared reads or vectorization;
   input materialization and aggregation memory remain. Batch APIs stay proposed.
3. Select further catalog, redaction, or workbook-visibility work from the
   [project roadmap](roadmap.md) and local task files.

## Entry template

```markdown
### YYYY-MM-DD — short title
- **Author:** name or agent
- **Branch / PR:** 
- **Done:** 
- **Not done / partial:** 
- **Decisions made:** 
- **Open questions / blockers:** 
- **Verify with:** commands or tests to confirm the state
- **Next step:** the single most useful thing to do next
```

## Entries

### 2026-11-13 — Bound diagnostic memory during evaluation (spec 0010)

- **Branch / PR:** `feature/bounded-diagnostic-memory`, [draft PR #18](https://github.com/thatquantguy44/finassert/pull/18), from merged PR #17 (`5ec9959`).
- **Done:** Built-in arithmetic, weights, shared row/group, integrity, exposure,
  and alignment evaluators now count every failure with bounded example samples.
  Existing outcomes, messages, row identity/order, totals, truncation, numerical
  reductions, and error precedence are preserved; no public API/schema change.
- **Evidence:** 2,144 tests pass, including 1,322 full-reference comparisons from
  the merged baseline. All 48 benchmark report fingerprints match. Dense
  100,000-row failure peak fell 80.0% (22.88 → 4.58 MiB). Paired grouped runs
  resolve a timing outlier without showing sustained regression. See
  [spec 0010 evidence](https://github.com/thatquantguy44/finassert/blob/main/specs/0010/artifacts/README.md).
- **Verification:** Ruff lint/format, mypy (58 modules), strict docs, author policy,
  wheel/sdist build, and isolated installed CLI/unit/FX/workbook flows pass. The local
  editable-install path was hidden by this
  environment; installing the built wheel allowed the MCP subprocess check and
  full suite to pass. No repository workaround was introduced.
- **Limits:** Input materialization and necessary aggregation/group/key state
  still scale with the data. No merge, release, or public batch API is included.
- **Next step:** Review this branch and the local spec handoff.

### 2026-11-13 — Pin the browser CI runner to Playwright's supported OS

- **Branch / PR:** `feature/seven-priority-roadmap`, draft PR #17.
- **Evidence:** CI at `5abd62e` passed Python 3.11-3.13, quality/package checks,
  authorship, and documentation. The web job built all artifacts but failed
  installing Chromium: pinned Playwright 1.55 rejects Ubuntu 26.04, now selected
  by `ubuntu-latest`.
- **Fix:** Pin only the web job to Ubuntu 24.04, supported by Playwright 1.55's
  [platform contract](https://github.com/microsoft/playwright/blob/v1.55.0/packages/playwright-core/src/server/utils/hostPlatform.ts).
  Browser smoke tests remain required, with no dependency upgrade or skipped gate.
- **Next step:** Verify all browser/Excel smoke tests on the corrected runner.

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

### 2026-11-13 — Reconcile current main before implementation

- **Branch / PR:** `feature/seven-priority-roadmap`, draft PR #17; tracking issue #16.
- **Finding:** The initial local checkout was stale. Main at `a3f0a3e` already
  includes public cash/NAV rules, policies/CLI, workbook loading, Excel add-in,
  and treasury work. Preserve these implementations and verify remaining gaps.
- **Layout correction:** Main already allocated 0011 to non-technical interfaces
  and 0012 to treasury. The unpublished workbook-file proposal moves to 0013;
  the unpublished seven-priority tracker moves to 0014. Previous entries retain
  the paths and numbering used at the time.
- **Decision:** Retain main's severity-based blocking semantics. Extend the Excel
  module with the optional workbook-reader API without replacing the add-in API.
- **Next step:** Verify the integrated baseline, then complete gate 1 in order.

### 2026-11-13 — Seven-priority implementation branch

- **Author:** Codex (Joshua Lutkemuller's session)
- **Branch:** `feature/seven-priority-roadmap`.
- **Done:** Created an ordered delivery workspace at `specs/0012/`, preserving
  the existing Excel reader and numbered-spec migration as branch foundations.
- **Not done:** The seven implementation gates remain open; work starts at gate 1.
- **Decisions:** Draft PR tracks all seven priorities. Each gate receives
  verification and a reviewable commit before moving to the next.
- **Next step:** Fix trailing uncached formulas and Excel error-cell outcomes.

### 2026-11-13 — Numbered specification workspaces

- **Author:** Codex (Joshua Lutkemuller's session)
- **Branch / PR:** `docs/spec-0011-excel`; no PR created in this session.
- **Done:** Moved specs 0001-0011 verbatim into `specs/NNNN/spec.md`. Added
  `plan.md`, `tasks.md`, `roadmap.md`, `AGENTS.md`, `contracts.md`, and `handoff.md`
  to every spec folder. Added a reusable template, repository/shared instructions,
  contribution guidance, and updated active links and current-state tracking.
- **Not done / partial:** Runtime code and spec requirements are unchanged.
  Formula/error-cell, adapter length-validation, and diagnostic gaps reproduced
  during the preceding review are tracked as open tasks, not fixes.
- **Decisions made:** Use permanent four-digit folder names. `spec.md` remains
  canonical; companion files track implementation and evidence. Master handoff
  history is preserved, including historical paths. New specs start from
  `specs/_template/`.
- **Open questions / blockers:** No blocker for the documentation migration.
- **Verify with:** Compare migrated spec contents against HEAD; verify all
  numbered folders, local links, and anchors; `git diff --check`;
  `.venv/bin/python -m mkdocs build --strict --site-dir /tmp/finassert-review-site`.
- **Evidence:** All 11 specs match their original contents byte-for-byte; every
  numbered folder and the template has the seven required files. Historical
  master handoff entries are unchanged. Local links/anchors, the strict docs
  build, and the whitespace check pass. Runtime checks were not repeated for
  this documentation-only migration.
- **Next step:** Fix the first unchecked task in `specs/0011/tasks.md`: detect
  uncached formulas before trimming trailing rows.

### 2026-10-15 — Excel reader implemented (spec 0011 milestones 1-2)
- **Author:** Claude Code (Joshua Lutkemuller's session)
- **Branch / PR:** `docs/spec-0011-excel` (not pushed, no PR yet)
- **Done:** `src/finassert/excel.py` with `read_workbook`, `WorkbookSource`,
  `ExcelError`; `excel` extra and openpyxl in dev group; 10 tests in
  `tests/integration/test_excel_reader.py`. ruff, mypy, and pytest (75 passed)
  clean.
- **Not done / partial:** `write_report_xlsx`, CLI flags, hidden-row reporting,
  shared 0004 adapter contract suite not yet run over this adapter. `uv.lock`
  also lost some platform markers when re-locked; review before merging.
- **Decisions made:** Hidden rows are read; `sheet` is required; numeric cells
  become `Decimal(repr(x))`; midnight datetimes become `date`.
- **Open questions / blockers:** Package rename from `docs/` branch name; PR.
- **Verify with:** `uv run pytest -q && uv run mypy && uv run ruff check`
- **Next step:** Milestone 4, `write_report_xlsx`, or the 0004 contract suite.

### 2026-10-15 — Spec 0011 reviewed against code
- **Author:** Claude Code (Joshua Lutkemuller's session)
- **Branch / PR:** `docs/spec-0011-excel` (initial commit `93ca479`)
- **Done:** Fixed two spec/code mismatches: `ColumnMapping` belongs to rules,
  not the reader (`read_workbook` now takes no mapping); rule metadata is
  free-form, so the report `Diagnostics` sheet is deferred until 0005 defines
  structured observations. Added formula-injection guard and open questions.
- **Not done / partial:** No code. openpyxl not yet added to `pyproject.toml`.
- **Decisions made:** Reader returns a plain `ColumnSource`; worksheet row
  numbers are labels; Decimals written to reports as text.
- **Open questions / blockers:** See the spec's Open questions section.
- **Verify with:** `mkdocs build --strict`
- **Next step:** Implement milestone 1-2 behind an `excel` extra, test-first.

### 2026-10-15 — Draft spec 0011 Excel workbook integration
- **Author:** Claude Code (Joshua Lutkemuller's session)
- **Branch / PR:** `fix/github-merge-author` (uncommitted)
- **Done:** Added `specs/0011-excel-workbook-integration.md` and indexed it in
  `specs/README.md`. No repo spec previously covered Excel.
- **Not done / partial:** No code. Spec scope is an assumption: workbook file
  input (openpyxl, optional extra) and `.xlsx` report output. Add-ins, xlwings,
  and hosted Graph APIs are listed as deferred.
- **Decisions made:** Row labels are worksheet row numbers; formula cells with
  no cached value are evaluation errors; core never imports openpyxl.
- **Open questions / blockers:** Confirm scope with Joshua; is a live-Excel or
  hosted API wanted instead? Not on the roadmap yet.
- **Verify with:** `mkdocs build --strict`
- **Next step:** Confirm scope, then add to the roadmap after item 3.

### 2026-10-15 — Handoff log created
- **Author:** Claude Code (Joshua Lutkemuller's session)
- **Branch / PR:** `fix/github-merge-author`
- **Done:** Created this log, seeded from the roadmap and recent git history
  (PRs #1–#3 grouped validation and typed aggregation; `7a5a69c` merge-author
  identity fix).
- **Not done / partial:** Earlier sessions have no recorded entries.
- **Decisions made:** Log lives in `docs/handoff.md`, append-only, newest first.
- **Open questions / blockers:** none
- **Verify with:** `mkdocs build --strict`
- **Next step:** Roadmap item 1, starting with a gap review of spec 0004
  against the current adapter code.
