# 0016 — Excel add-in validation workflow: tasks

**Status:** E-01/E-02 complete; E-03 implemented and verified with configurable
session controls. E-04 navigation and E-05 evidence/output implemented/verified;
full E-06 acceptance pending.

## Scoping delivery

- [x] Audit current snapshot reading, stored results, date payload and diagnostic output.
- [x] Define one-source Mac-first scope, compatibility boundaries and acceptance criteria.
- [x] Sequence implementation and identify meaningful automated/manual evidence.
- [x] Verify documentation links/anchors, workspace completeness, whitespace and strict build.

Scope evidence: 16 Markdown files and 80 local links/anchors checked; all seven
required files, six requirements/tasks and ten acceptance rows present. Strict
MkDocs and git diff --check passed. Runtime tests were not rerun for this
documentation-only proposal; no new runtime capability is claimed.

## Ordered implementation

Each E task is one intended reviewable commit; split a commit further when needed
without skipping its dependencies. Check completion only with recorded evidence.

- [x] **E-01 — Host baseline and contracts** (R-06, AC-08/09): open proposal issue;
  add a regression reproducing stale data/policy results; record real Mac version,
  install route, capability/requirement matrix, calculation behavior and date
  fallback. Attach baseline diagnostics; refine the estimate and host support floor.
  - [x] Open [implementation issue #23](https://github.com/thatquantguy44/finassert/issues/23).
  - [x] Reproduce stale Run, changed-source export and edited-policy export with
    strict expected-failure browser tests, plus passing financial controls.
  - [x] Audit stable APIs; correct the prototype floor to 1.7 and add a read-only
    diagnostic for the proposed 1.9 workflow. See [API matrix](api-matrix.md).
  - [x] Record installed Mac version, existing HTTPS/sideload route, baseline build
    identity and the disabled Developer Add-ins finding in [evidence](artifacts/README.md).
  - [x] Open the native pane, capture actual capabilities/calculation/timings and
    complete a synthetic read/run; refine the estimate from those measurements.
    Evidence: [native diagnostic](artifacts/e01-native-diagnostics.txt) and
    [structured baseline](artifacts/e01-native-baseline.json); 50,000 rows read in
    561 ms, template check/render 631 ms, engine ready 1,062 ms; all steps passed.
- [x] **E-02 — Source binding and dates** (R-01/04, AC-01/05): one table/range picker,
  exact geometry/identity, table totals exclusion, hidden/filtered inclusion,
  pre-read size guard, malformed/empty regions and explicit 1900/1904 choice.
  Verify offsets, date equality and selection changes that preserve binding.
  Evidence: 29 browser passes / one strict E-03 xfail; native Mac range/table,
  hidden-row, totals-sentinel, both date systems and selection-move checks in
  [E-02 evidence](artifacts/e02-native-verification.json). Requests are capped at
  5,000 rows / 50,000 cells; range merge detection requires stable ExcelApi 1.13.
  CDN/bundled Excel and shared browser/file smoke flows passed; full runtime suite
  3,624 passed. See [evidence notes](artifacts/README.md#e-02-source-and-date-evidence).
- [x] **E-03 — Freshness and stable capture** (R-02, AC-02/03/08): define canonical
  snapshot encoding/digest vectors; single operation/generations; rereads and
  calculation guards; edit/recalc/structure/policy invalidation; event disposal;
  delayed events, concurrent edits, failed runs and obsolete callbacks. Verify
  shared browser/file paths after changes to the common application.
  Evidence: [typed digest vectors](artifacts/e03-capture-vectors.json),
  [native observations and verification](artifacts/README.md#e-03-configurable-freshness-and-stable-capture),
  and tests/browser/test_excel_capture.py. Session controls cover events/on-demand,
  verified/snapshot-only, 2–4 captures, request sizes and timeout; obsolete jobs
  cannot publish and every current-result export rechecks. Existing output-name
  collisions are rejected unless the pane created the sheet; durable ownership,
  unique names and full source-provenance output remain E-05.
- [x] **E-04 — Diagnostic navigation** (R-03, AC-04/06): canonical sampled findings,
  complete totals/caps; physical row/cell targets; business-key ambiguity, group
  context and missing targets; source verification and keyboard navigation.
  Test malicious text, quoted sheet names, sort/delete and changed row mappings.
  Evidence: 13 identity tests and 19 browser cases, plus
  [native F8 selection/correction/rerun](artifacts/e04-native-navigation.json).
  Canonical counts/caps/samples and exported artifacts stay unchanged; ambiguous
  keys require unique mapping/rerun and missing series have no fabricated target.
- [x] **E-05 — Evidence and export** (R-05, AC-03/06/08): optional input.excel source
  contract, current-result preflight, JSON/HTML/results-sheet parity, collision and
  source-overlap guards, text safety, protected destinations and partial-write
  reporting. Preserve valid policy-only export/save independently of freshness.
  Evidence: 22 provenance/parity tests and 15 E-05 browser cases, existing browser
  regressions, and focused native unique-sheet/replacement/policy/ownership
  persistence evidence. See [E-05 evidence](artifacts/README.md#e-05-evidence-and-safe-output).
- [ ] **E-06 — Mac acceptance and regressions** (R-06, AC-07/09/10): execute
  acceptance.md, retain synthetic fixture/policy identities and actual results;
  run 50,000 rows, all repository checks and both runtime smoke modes; update user
  docs/support claims and the local/master handoffs. Record review status separately.
  Linux automated preflight and 50,000-row Office stand-in evidence are recorded
  in [acceptance.md](acceptance.md#2026-11-15-automated-preflight-linux). The full
  small Mac correction/date workflow and external review remain pending. Native
  scale timings, exports and CLI tie-out are now verified below.
  - [x] Prepare synthetic 1900/1904 workbooks and policy identities; add a
    retained-export verifier using the actual CLI. Ten controls verify both
    epochs and reject changed source, report counts, worksheet output and epoch.
  - [x] Run current-main Mac automated regressions, smoke/scale and package checks.
    See [Mac preflight](acceptance.md#2026-11-15-mac-preflight-and-blocked-native-setup).
  - [x] Run actual native 50,000-row diagnostics and verified capture; retain
    JSON/HTML/results-sheet and strict CLI parity plus complete source/unrelated
    cell integrity. See [native verification](acceptance.md#2026-11-16-native-scale-and-export-verification).
  - [x] Start AC-07 on native 1900 source: dates, exact C7:H9 bounds, row-8
    negative failure, F8 click navigation, unchanged source and actual failed
    JSON/CLI equality. See [progress](acceptance.md#2026-11-17-ac-07-progress-correction-remains-open).
  - [ ] Complete the small negative-value correction/date workflow, clean table
    opening, hidden/filtered and failure/race/keyboard cases. Native window capture
    failed after AC-07's failing export/navigation. Correct F8 from the last
    confirmed -400 to 400 and verify Stale/reread/pass/exports before completion.
    Record review separately.

## Acceptance ledger

| Criterion | State | Evidence required |
| --- | --- | --- |
| AC-01 | verified for E-02 | Browser guards/geometry fixtures and native table/range capture; see E-02 evidence |
| AC-02 | verified for E-03 | Browser races/invalidation plus native edit → Stale → fresh Current run |
| AC-03 | verified for E-03–E-05 | Configured export/navigation preflight, immutable snapshot provenance, staged output and failed-write recovery |
| AC-04 | verified for E-04 | 13 identity tests, 19 browser cases and focused native F8 navigation/correction/rerun |
| AC-05 | verified for E-02 | Both explicit epochs produce 2026-01-01 in the browser and native Mac pane |
| AC-06 | verified for E-04/E-05 | Canonical JSON/HTML/sheet samples/counts/caps and unchanged source; full E-06 host/CLI acceptance remains |
| AC-07 | partially verified; correction loop pending | Native 1900 dates/bounds/failure/F8 navigation and failed-report CLI parity recorded; correction/Stale/reread/pass/exports await a visible native window |
| AC-08 | verified for E-01–E-05 | Input/capability/race guards plus owned/source/collision checks and protected/partial/cancel recovery |
| AC-09 | verified for recorded build; browser retries disclosed | Runtime/browser, CDN-page/local-runtime and bundled smokes, quality/docs/distribution checks plus native resource/CSP diagnostic and startup-only server trace; no new core dependency |
| AC-10 | verified on native Mac | 50,000 rows × 5 columns; exact 3+3 failed financial groups, two passing data checks, diagnostic caps, native timings, verified capture and complete source/unrelated-cell integrity; native records linked above |

No acceptance row is complete merely because the baseline tests passed previously.
