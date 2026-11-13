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

- **Branch:** `feature/seven-priority-roadmap`
- **Last recorded merge:** PR #3 grouped DataFrame contracts
- **Active work:** [Seven-priority delivery](https://github.com/thatquantguy44/finassert/blob/main/specs/0014/spec.md), starting with Excel reader correctness
  under [0013](https://github.com/thatquantguy44/finassert/blob/main/specs/0013/spec.md),
  adapter contracts under [0004](https://github.com/thatquantguy44/finassert/blob/main/specs/0004/spec.md),
  and diagnostics under [0005](https://github.com/thatquantguy44/finassert/blob/main/specs/0005/spec.md).
- **Open blockers / gaps:** Known formula/error-cell, adapter length-validation,
  and diagnostic gaps are recorded in the corresponding spec task files.

## Next up

Immediate corrective work precedes the feature sequence in the
[roadmap](roadmap.md). Move items to an entry when done.

1. Fix uncached trailing formulas and Excel error-cell outcomes (spec 0011).
2. Enforce adapter value/label lengths and shared adapter tests (spec 0004), then
   stabilize bounded diagnostics, row identity, and strict JSON (spec 0005).
3. Cash and NAV reconciliation rules with documented sign and materiality
   conventions.
4. Excel report output, stable CLI/JSON artifacts, and optional YAML policy
   configuration.
5. Typed financial units and explicit FX provenance.
6. Benchmark batch execution before choosing vectorization or concurrency.

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
