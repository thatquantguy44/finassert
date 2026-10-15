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

## Current state

- **Branch:** `fix/github-merge-author` (clean, based on `main`)
- **Last merged:** PR #3 grouped DataFrame contracts
- **Active spec:** [0004 DataFrame adapters](https://github.com/thatquantguy44/finassert/blob/main/specs/0004-dataframe-adapters.md)
- **Open blockers:** none recorded

## Next up

Ordered; mirrors the [roadmap](roadmap.md). Move items to an entry when done.

1. Harden dataframe adapters, column mappings, grouped rules, and diagnostic
   row identity (spec 0004).
2. Cash and NAV reconciliation rules with documented sign and materiality
   conventions.
3. Stable CLI/JSON artifacts and optional YAML policy configuration.
4. Typed financial units and explicit FX provenance.
5. Benchmark batch execution before choosing vectorization or concurrency.

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
