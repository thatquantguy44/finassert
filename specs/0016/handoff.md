# 0016 — Excel add-in validation workflow: handoff

## Current state

- **Status:** Scoped proposal; runtime implementation and real-host acceptance pending.
- **Branch:** docs/spec-0016-excel-validation-workflow, based on main at 8d96fdc.
- **PR:** No separate implementation PR created for this scope.
- **Delivered:** Required seven-file workspace and manual acceptance checklist;
  six ordered implementation tasks with requirement/acceptance coverage. All
  documentation checks passed; the scope is ready for implementation review.
- **Open evidence:** Real Mac version/capabilities, install baseline and timings;
  see E-01. No real-Excel result is claimed.
- **Next step:** E-01: proposal issue, stale-result regression and Mac host baseline.

## Entries

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
