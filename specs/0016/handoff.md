# 0016 — Excel add-in validation workflow: handoff

## Current state

- **Status:** E-01 in progress; native baseline incomplete. E-02–E-06 pending.
- **Branch:** feature/excel-source-binding-dates from refreshed main at 00ce4d9;
  prepared for E-02, with no E-02 implementation yet.
- **Implementation PR:** [#24](https://github.com/thatquantguy44/finassert/pull/24)
  is merged; E-01's native baseline is still incomplete.
- **Scope PR:** [#22](https://github.com/thatquantguy44/finassert/pull/22) is merged.
- **Issue:** [#23](https://github.com/thatquantguy44/finassert/issues/23).
- **Delivered:** Three stale-result reproductions, passing controls, stable API
  audit, read-only metadata probe and manifest floor/version corrections.
- **Open evidence:** Native pane is disabled in Excel's Developer Add-ins list.
  Installed version and served build hashes are recorded; actual Office.js
  capabilities/calculation and startup/read timings remain unobserved.
- **Next step:** Resolve native loading; complete the synthetic E-01 read/run and
  diagnostic capture in [baseline evidence](artifacts/README.md), then E-02.

## Entries

### 2026-11-13 — Next branch prepared from merged main

- **Branch:** feature/excel-source-binding-dates, created directly from main and
  origin/main at 00ce4d9 after fetching merged PR #24.
- **Next build:** E-02 source picker, explicit binding/geometry, table totals
  exclusion, malformed/empty/oversized input rejection and required date choice.
- **Status:** No runtime implementation or new host test in this preparation.
  E-01 native evidence remains a prerequisite; all acceptance rows stay pending.
- **Verification:** Matching branch/base SHA, strict MkDocs and whitespace checks.
- **Next:** Resolve native loading and finish E-01, then build E-02 in order.

### 2026-11-13 — E-01 draft PR published

- **Commit / PR:** 950a03e, [draft PR #24](https://github.com/thatquantguy44/finassert/pull/24)
  from feature/excel-host-baseline to main. Implementation was already committed
  and pushed; publication adds the PR link to local/master handoffs.
- **Verification:** Strict MkDocs and whitespace checks passed for these handoff
  updates. Runtime evidence remains in the implementation entry below.
- **Remaining:** Native add-in loading and actual capability/read/run measurements;
  issue #23 stays open. The draft does not promote E-01 or later acceptance.

### 2026-11-13 — E-01 engineering baseline started

- **Baseline:** Refreshed origin/main to 3b5a014, merged scope PR #22; created
  feature/excel-host-baseline and opened issue #23.
- **Done:** Added real-pane/Pyodide browser regressions for stale Run, changed
  source export and tolerance-edit export, tracked as strict expected failures
  pending E-03. Added passing financial/invalid-policy controls, unsupported 1.9
  and calculation-state probe cases; wired the browser suite into CI.
- **API findings:** [Matrix](api-matrix.md) confirms proposed 1.9 and explicit
  date fallback. Corrected prototype manifest/diagnostic minimum to 1.7 for
  getRangeByIndexes. Read-only probe observes calculation and event members;
  it does not implement freshness. Manifest deployment version is independent
  from the package to satisfy the validator's minimum 1.0 requirement.
- **Native findings:** Installed Excel 16.115 (16.115.26110837), macOS 26.5.1.
  Existing HTTPS/sideload route serves the exact unmodified main baseline.
  finassert is listed but disabled under Developer Add-ins; pane loading failed.
  No real Office.js capability/timing or successful read/run is claimed. No
  settings/trust, existing server/manifest or user workbook data was changed.
- **Verification:** 3,624 tests passed, nine browser tests skipped in the ordinary
  suite and run separately (six pass, three strict expected failures). Existing
  CDN and bundled/offline Excel smoke flows passed. Ruff/format, mypy and isolated
  installed-distribution verification, strict MkDocs and Microsoft's corrected
  manifest validation passed. See artifacts for reproduction.
- **Remaining:** E-01 native baseline and measurement-based estimate; E-02–E-06
  and all acceptance criteria remain incomplete. Resolve the disabled add-in entry.

### 2026-11-13 — Scope committed, pushed and opened for review

- **Commit:** d035bba, docs: scope the Excel add-in validation workflow.
- **PR:** [#22](https://github.com/thatquantguy44/finassert/pull/22), targeting main,
  ready for review. All 16 changed files are documentation.
- **Evidence:** 80 local links/anchors, workspace/task/acceptance coverage,
  whitespace and strict MkDocs passed. Remote checks are visible on the PR.
- **Next:** Review scope; E-01–E-06 and real-host acceptance remain pending.

### 2026-11-13 — Scope prepared for publication to main

- **Request:** Commit/push all changes and create a PR targeting main.
- **Baseline:** PR #21 is merged; fast-forwarded this branch onto main at 8d96fdc.
  The new PR contains only scope documentation and related roadmap/handoff changes.
- **Verification:** 16 Markdown files / 80 local links and anchors,
  workspace/task/acceptance coverage, whitespace and strict MkDocs passed. Runtime
  acceptance remains pending; this task does not implement E-01–E-06.
- **Next:** Review scope, then begin E-01.

### 2026-11-13 — Excel workflow scope prepared

- **Request:** Scope the validate → fix → rerun add-in slice after the six-slice delivery.
- **Done:** Audited the existing live snapshot, stored-result export, date payload,
  app invalidation and report helpers. Defined R-01–06, AC-01–10, E-01–06 and
  compatibility/deferred boundaries. Updated project sequencing to prioritize this
  Excel workflow; treasury follow-on work stays proposed.
- **Not done:** No runtime, deployment, certificate, workbook or host configuration
  changes. No Mac/Windows/web pilot executed.
- **Decisions:** One bound source; explicit dates; event invalidation plus stable
  capture/pre-action checks; canonical bounded navigation; Mac acceptance gate.
- **Verification:** 16 Markdown files / 80 local links and anchors checked;
  required files, six requirements/tasks and ten criteria checked. Strict MkDocs
  and whitespace checks passed. No runtime checks were needed for documentation.
- **Next:** Implementation begins with E-01; all runtime acceptance remains pending.
