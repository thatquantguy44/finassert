# 0016 — Excel add-in validation workflow: handoff

## Current state

- **Status:** E-01–E-05 implemented and verified for their slices; full E-06 pending.
  AC-01–06 and AC-08 have slice evidence; full acceptance remains pending.
- **Branch:** `feature/excel-e06-mac-acceptance` from merged main `67c3c1c`.
  E-04/E-05 and QuantSmith PR #28 are merged. E-06 tooling/evidence is
  included in the enclosing delivery checkpoint; production runtime is unchanged.
- **Earlier PRs:** [#22](https://github.com/thatquantguy44/finassert/pull/22) and
  [#24](https://github.com/thatquantguy44/finassert/pull/24) are merged.
- **Issue:** [#23](https://github.com/thatquantguy44/finassert/issues/23) has no
  remaining expected-failure browser cases; review/closure is separate.
- **Delivered:** Native corrected-manifest baseline, explicit table/fixed-range
  binding, exact IDs/geometry, totals/visibility/input guards, bounded requests
  and required user date interpretation. E-03 adds session-configurable freshness,
  stable captures, generations and existing-action preflight.
  See [evidence](artifacts/README.md).
- **Native:** Excel 16.115 / Mac; 50,000-row baseline all PASS. Both epochs,
  hidden row, actual table totals and selection-preserving Run verified.
- **E-04:** Canonical findings, bounded physical cell/row targets, key ambiguity,
  missing series, keyboard/live feedback and configured preflight implemented.
  13 identity tests, 19 E-04 browser cases and focused native F8 selection pass.
- **E-05:** Validated input.excel provenance, canonical output parity, unique
  names, saved ownership/explicit replacement, policy picker/independence and
  incomplete-write recovery. 22 unit and 15 E-05 browser cases; full runtime
  3,697 and full browser 106 pass. Native export/reopen/integrity evidence retained.
- **E-06 preflight:** On Linux at source `4862ce7`, 3,697 runtime and 106 bundled
  browser tests passed. Excel bundled and CDN-page/local-runtime smoke, shared
  browser/file smoke, 50,000-row Office stand-in diagnostic, quality/docs and
  distribution checks passed after correcting hidden-DOM harness assertions.
  See [acceptance](acceptance.md#2026-11-15-automated-preflight-linux).
- **Optional reference:** Spec [0018](../0018/spec.md) adds a local on-demand
  QuantSmith document reader. It does not change source capture, result
  currentness or the pending E-06 real-host gate.
- **E-06 Mac preflight:** 3,700 existing runtime tests plus ten new harness
  controls pass. Browser run: 104 pass and three startup timeouts, all three pass
  on retry. Quality/docs, CDN-page/local-runtime and bundled/shared smokes,
  50,000-row stand-in and installed distribution checks pass. See the
  [structured record](artifacts/e06-mac-preflight.json).
- **E-06 native scale:** All diagnostic steps pass on the current bundled build:
  startup 1,351 ms; 50,000-row write/read/check-render 322/732/750 ms. Verified
  capture reached Current; actual JSON/HTML/all 41 results-sheet rows and CLI
  match exactly. Source values/types/formats and four unrelated sheets are
  unchanged. See [diagnostic](artifacts/e06-native-diagnostics.json) and
  [parity/integrity](artifacts/e06-native-scale-parity.json).
- **AC-07 progress:** Initial E-06 checkpoint was committed/pushed as `6328253`.
  Native H8:H9 Short Date, explicit 1900/Jan 1, C7:H9 bounds, one row-8 negative
  failure/two passes and F8 click navigation now pass. Actual failed JSON report
  and policy equal the CLI; source values/types/formats match across navigation.
  See [progress](artifacts/ac07-native-progress.json).
- **Native stopping point:** Original workbook was saved. Last confirmed F8 is
  -400, with Current failing evidence; correction/Stale/reread/pass/exports have
  not run. Native capture returned cgWindowNotFound; foreground assistance was
  requested. The unrelated Book1 prompt was canceled without saving/discarding it.
- **Next:** Foreground the original disposable workbook on the current desktop,
  inspect dialogs and recheck F8, then complete the correction loop in the
  [immediate pickup](acceptance.md#ac-07-immediate-pickup). Finish remaining
  1904/table/hidden/failure/race/keyboard rows and review under master ordering.

## Entries

### 2026-11-17 — AC-07 dates, failing run and native F8 navigation

- **Work:** Pushed initial E-06 checkpoint `6328253`, then continued AC-07 on
  the existing original disposable workbook. Applied native date formatting,
  bound C7:H9, used long-only policy, retained one row-8 violation/two passes,
  navigated to F8/-400 and downloaded the actual failed JSON.
- **Verification:** Saved 1900 dates/preview show 2026-01-01; Current failure and
  navigation preflights passed. Failed report/policy equal actual CLI; before/
  after-navigation source cells/types/formats match. Native details and hashes
  are in [progress](artifacts/ac07-native-progress.json).
- **Stopping point:** Native capture failed before correction. Original workbook
  saved; unrelated Book1 prompt canceled. Isolated native-seed/temporary-manifest
  launch did not establish a visible window and is not host acceptance proof.
- **Pickup:** Foreground the original workbook, verify F8 -400, correct to 400,
  observe Stale/export guards, reread/pass and retain passing exports/CLI parity.
  AC-07 and full E-06 remain open; record human review separately.


### 2026-11-16 — E-06 delivery checkpoint; AC-07 next

User requested commit/push of all current changes before AC-07. The enclosing
checkpoint retains native scale/capture/export/CLI/integrity evidence, acceptance
tools, ten passing harness controls and current documentation. The next native
step remains the unsaved Sheet1!C7:H9 source and its date-format/correction loop;
no new AC-07 completion is claimed by delivery. Follow the master ordering.


### 2026-11-16 — Native scale, verified exports and CLI tie-out

- **Work:** Opened the current build using Microsoft's empty sideload template;
  replaced only the identified old localhost:3000 test server with the current
  bundled build after Excel retained that cached source address. No security or
  certificate trust changed. The CLI's supplied-document route does not inject
  web-extension parts into a freshly generated workbook.
- **Verification:** Native API support through 1.13, Automatic/Done and all
  diagnostic steps pass. Scale read 732 ms/check-render 750 ms; exact three
  failing weight and three NAV groups, two passing data checks. Verified capture
  reached Current; actual JSON/HTML/canonical worksheet/CLI and input integrity
  pass. [Retained evidence](artifacts/e06-native-scale-parity.json) includes hashes
  and unchanged source/unrelated cells. This supersedes the previous preflight's
  no-native-execution status for the executed scale/export cases only.
- **Remaining findings:** Generated table still triggers repair (table part);
  speculative filter/metadata fixes were not retained as a verified repair.
  A single-cell binding attempt was safely rejected. Native Go To plus OK was
  needed to select bounds; Name Box text alone did not do so.
- **Stopping point:** Live Sheet1!C7:H9 small source pasted, unsaved; date-format
  setup then timed out. Scale native snapshots/exports and policy are safely
  retained under `/tmp/finassert-e06-*`; current server/build is localhost:3000
  and `/tmp/finassert-e06-current`. The optional 3002 server remains separate.
- **Pickup:** Inspect current live state; finish small negative/correction/1904
  and remaining table/hidden/failure/race/keyboard cases, then record review.
  E-06 is not complete merely because AC-09/10 now have recorded evidence.


### 2026-11-16 — E-06 acceptance tooling and blocked Mac setup

- **Work:** Prepared synthetic offset/hidden/table/totals fixtures for both epochs,
  validated policies and byte identities; added native retained-export/CLI parity
  verifier and ten positive/negative controls. No production behavior changed.
- **Verification:** Current merged runtime 3,700 passes plus ten new controls;
  browser 104 passes with three engine-startup errors, all three pass on retry;
  quality/docs, both Excel runtime smokes, shared browser flow, 50,000-row stand-in
  and isolated distributions pass. Actual pinned QuantSmith localhost response
  matched its Git blob; native panel remains pending.
- **Failures:** First sideload hit an existing manifest (resolved via official
  stop/start); initial fixture triggered recovery. Corrected totals/filter and
  policy layout, but native dialogs then repeatedly failed automation targeting.
  Clean native opening and workflow were not established.
- **Stopping point:** E-06 remains open. Last native Open dialog selected the
  generated 1900 workbook. Prepared files/build remain under `/tmp/finassert-e06-*`.
- **Pickup:** Restore native control, cleanly open the fixture, execute the
  [host checklist](acceptance.md#resume-with-retained-files), retain actual exports,
  run the parity verifier and native scale; record external review separately.


### 2026-11-15 — Optional local reference beside the Excel workflow

Spec [0018](../0018/spec.md) adds a reader for pinned QuantSmith documents
to the pane. It fetches only on request and never sends workbook cells. The
workbook capture/output contract and E-06 Mac acceptance gate are unchanged;
the 0018 handoff owns reference evidence and later hosting decisions.

### 2026-11-15 — E-06 Linux preflight; Mac acceptance remains open

- **Work:** Ran automated E-06 regressions against `4862ce7` and repaired
  browser/smoke assertions that used `innerText` on hidden DOM elements. Added a
  configurable 50,000-row Office stand-in diagnostic. No production behavior
  changed.
- **Verification:** 3,697 runtime and 106 bundled browser tests; both Excel
  smoke modes, shared browser/file smoke, 50,000-row planted failures and source
  integrity, Ruff/format, mypy, strict docs and isolated distribution probes pass.
  Exact synthetic timings and bundle hashes are in [acceptance.md](acceptance.md#2026-11-15-automated-preflight-linux).
- **Stopping point:** No Mac Excel host was available. Full native E-06 workflow,
  both epochs, CLI/export tie-out, 50,000-row native timings and review remain.
- **Pickup:** Follow the master's E-06 priority: execute the pending real-host
  rows on the same build and record actual fixture, policy and output evidence.

### 2026-11-15 — E-05 verified source evidence and output lifecycle

- **Branch:** E-04 committed/pushed as 6bbf6b9; user authorized E-05 on the same
  feature branch. This checkpoint contains the complete E-05 implementation.
- **Work:** Private strict input.excel context after verification; shared canonical
  HTML/JSON/sheet results with captured/verified times and evaluated snapshot hash.
  Outputs use unique names, saved add-in-scoped worksheet ID ownership and explicit
  completed-results replacement. Source/role guards and preflight remain mandatory.
  Stage text/rows before writes, preserve literal quotes/formula guards, and report
  partial/protected/cancel failures without claiming atomicity/completion.
- **Verification:** 3,697 runtime and 106 browser passes, including 22 new context
  and 15 output cases. CDN/bundled/shared-browser smoke, Ruff/format and mypy pass.
  Strict docs, 179 local Markdown links/anchors, whitespace and installed
  distribution probes also pass; the master records final verification/pickup.
- **Native:** [Evidence](artifacts/e05-native-exports.json) records actual build
  hashes and both phases: saved unique outputs/explicit replacement/policy/ownership
  reopening, then corrected literal apostrophe handling. Saved C7:H11 values,
  number formats, cell types and hidden row match the original synthetic fixture.
- **Pickup:** Review the stack and execute full E-06 acceptance.md, including
  both epochs, CLI/export parity and 50,000-row workflow timings. No full E-06 or
  broad platform support claim; no PR/merge/release requested in this continuation.

### 2026-11-15 — E-04 commit checkpoint and E-05 continuation

User requested commit/push and E-05 implementation on the same branch. E-04's
verified implementation/evidence is recorded in this checkpoint; the following
E-05 entry will record its actual commit. No runtime changes since verification.
Continue with R-05 provenance, safe destinations, parity and write-failure recovery.
The master's priorities remain authoritative; E-06 full native acceptance follows.

### 2026-11-15 — E-04 implementation and focused native verification

- **Work:** Native diagnostic labels are resolved in Python before serialization.
  Only retained canonical samples yield targets; row keys never become addresses.
  The pane shows counts/caps/truncation and group/missing/ambiguous context, with
  native buttons/live status. Configured current-result preflight, captured host
  IDs/geometry and numeric bounds guard selection. No artifact/public API changes.
- **Verification:** 13 identity tests and 19 browser cases pass; 72 existing
  browser regressions also passed. Full runtime: 3,675 passed, 91 browser cases
  skipped in that ordinary job. Ruff/mypy and CDN/bundled/shared-browser smoke pass.
  Strict docs, Markdown links/anchors, whitespace and installed-distribution
  probes pass. The master records the final project verification and pickup.
- **Native:** [Recorded build/fixture/policy evidence](artifacts/e04-native-navigation.json)
  verifies F8 selection on an offset/apostrophe source, unchanged selected value,
  correction → Stale/disabled target → fresh Current three-pass result. Automation
  transcription/capture issues were recovered and recorded; no full E-06 claim.
- **Stopping point:** Uncommitted reviewable E-04 work on the feature branch.
  Review diff/evidence and prepare a refreshed master checkpoint before commit.
  Follow the master's E-05 priority next. E-06 output/scale/CLI acceptance remains.

### 2026-11-15 — Implementation merged; E-04 resumes from main

PR #25 merged at 32cf4ab, bringing E-01 native evidence, E-02 binding/dates and
configurable E-03 freshness/capture to main. E-04 is still unstarted and should
use a new feature branch from main. The current user-requested prompt/documentation
commit changes no Excel implementation; existing acceptance evidence remains
valid and the full E-06 workflow remains pending. Project ordering stays in the
master handoff.

### 2026-11-15 — Implementation PR opened

[PR #25](https://github.com/thatquantguy44/finassert/pull/25) targets main with
E-01 native completion, E-02 source/date binding and configurable E-03 capture/
freshness, plus the spec 0017 handoff guards. Commits 4822db8/e8d3526 were already
pushed; this update records the PR. Existing native, 72-browser and full-suite
evidence is retained. No runtime change, merge or release. Follow the master's
E-04 pickup; navigation, provenance/output ownership and full E-06 remain pending.

### 2026-11-14 — Master checkpoint guard added under 0017

The master handoff is canonical for project order and pickup. Spec 0017 now
requires a complete master checkpoint with matching current/newest-entry fields
and generated Git context for each nonempty commit; push/CI check outgoing history.
Follow [the contributor workflow](../../CONTRIBUTING.md#master-handoff-checkpoints).
This local handoff defers to the master's priorities. E-01–E-03 remain complete;
E-04 remains the next product task. No Excel implementation changed in this work.

### 2026-11-14 — Commit checkpoint; resume at E-04

- **Branch:** feature/excel-source-binding-dates. E-01–E-03 are the stopping point;
  E-04 implementation has not started. This checkpoint includes all recorded
  native evidence, source/date binding and session-configurable captures.
- **First work on resume:** Read R-03 and the E-04 task. Build a diagnostic view
  from canonical retained samples with complete counts/caps, then map observed
  findings to physical source rows/cells. Reuse withCurrentResult for navigation
  preflight; do not derive worksheet rows from business keys. Explain ambiguous
  and missing targets and add keyboard actions. Start tests with C7 offsets,
  quoted sheet names, duplicate keys and source edits/sort/delete before use.
- **Verification carried forward:** Latest 72 browser cases pass; earlier full
  runtime pass is 3,624 tests. Duplicate runtime reruns stalled during dependency
  imports, as recorded below; no Python runtime implementation changed afterward.
  The commit/handoff update uses links/anchors, strict docs and whitespace checks.
- **Native session:** Latest build opened Ready/Unbound with no epoch selected.
  Rebind and explicitly choose dates; settings do not persist. Retain the earlier
  Reload failure for E-06 and use the measured CLI close/reopen recovery route.
- **Later:** E-05 provenance/output ownership and E-06 complete Mac acceptance.

### 2026-11-14 — Configurable freshness and stable capture

- **Request:** Add configurable freshness/stable captures; user selected pane
  controls for this session only. Branch feature/excel-source-binding-dates.
- **Implemented:** Unbound/Ready/Reading/Checking/Current/Stale/Blocked states;
  live events or on-demand monitoring; verified or unverified snapshot mode;
  2–4 captures, bounded rows/cells and 1–300s timeout, cancel and Restore defaults.
  Strict defaults are events, verified/two captures, 5,000 rows, 50,000 cells, 120s.
- **Integrity:** Typed canonical evaluated snapshot SHA-256 with independent
  vectors, separate private formula hash, settled/manual calculation guards,
  generation/source/policy/date/config checks around async work and candidate
  publication. Event handlers are removed on rebind; pane shutdown makes no new
  Office calls. Export always rereads/compares in verified mode, even on demand;
  snapshot-only never becomes Current. Shared file/policy paths are regression-tested.
- **Output prerequisite:** Refuse bound-source replacement and existing sheets
  not created in this pane session. Durable ownership, unique-name UI, provenance,
  navigation and protected/partial output recovery remain E-04/E-05.
- **Evidence:** Native Excel 16.115 / 1904 C7:H9: verified passing Current result;
  edit F8 to -400 → Stale/exports disabled; rerun → Current with one financial
  failure at physical row 8; configuration edits invalidate; snapshot-only stays
  unverified/no export; defaults restored. See [E-03 evidence](artifacts/README.md#e-03-configurable-freshness-and-stable-capture).
- **Verification:** 3,624 runtime tests and 72 browser cases; CDN/bundled Excel
  and shared browser/file smoke, Ruff/format, mypy, distributions and strict docs.
  Initial sandbox loopback failures were rerun with loopback access; mypy's old
  cache caused an internal error and a fresh cache passed. Build during document
  edits hit an archive-size race; the final distribution was built after edits.
- **Final verification note:** Latest 72 browser cases pass. A duplicate full
  runtime rerun was stopped during blocked dependency file reads before collection;
  the earlier 3,624-test pass remains evidence and Python runtime code was unchanged.
  The final served build reopened Ready/Unbound in native Excel.
- **Remaining:** Complete E-06 acceptance, including native navigation/output
  parity and broader platform support. Earlier Reload blank-pane finding is
  retained; CLI close/reopen is the measured recovery route.
- **Next:** E-04. No commit, push, release or deployment performed in this turn.

### 2026-11-13 — Complete native E-01 and implement E-02

- **Branch:** feature/excel-source-binding-dates. No release or rollout.
- **E-01:** Built and sideloaded corrected 1.0.0.0 / 1.7 manifest. Menu entry
  remained disabled; Microsoft's CLI-generated sideload workbook opened Ready.
  Native diagnostics all PASS: 50,000 rows, startup 1,062 ms, read/preview 561 ms,
  check/render 631 ms. Actual 1.9/calculation/event answers and build hashes saved.
- **E-02:** Explicit workbook-table or fixed-rectangle binding, IDs, exact quoted
  bounds, actual header/body/totals, all hidden/filtered rows, prefetch ceiling,
  5,000-row / 50,000-cell requests, malformed/empty/merged/header guards, mapping
  review, structural reselection and required 1900/1904 choice. Each Run resolves
  and reads the bound source; source/date changes clear old snapshots/results.
- **API amendment:** Stable merged-header detection needs ExcelApi 1.13 for range
  mode. Earlier hosts get a table/update alternative; table manifest floor stays
  1.7 and planned freshness stays 1.9. No automatic epoch getter was established.
- **Native E-02:** C7:H9, quoted/apostrophe sheet name, hidden row, both epochs
  yielding 2026-01-01; P18 selection then 3 passing checks; actual totals row 11
  excluded from table body C7:H10, including a -99999 sentinel. Saved native
  fixture reopened intact after an initial generated table repair.
- **Verification:** Full runtime suite 3,624 passed; browser source/date and
  freshness cases pass except the explicit E-03 policy-edit xfail. CDN/bundled
  Excel and shared browser/file smoke flows, Ruff/format, mypy, distribution,
  strict docs, local links/anchors and whitespace checked; details in artifacts.
- **Boundaries:** No stable capture/calculation gate, comprehensive freshness,
  navigation or export/collision preflight is claimed. E-06 acceptance remains
  pending; retain the original historical baseline and handoff entries.
- **Recovery finding:** Native Add-in options Reload left a blank pane. Closing
  the disposable workbook and CLI reopening recovered the final build; 1904
  source read and three passing checks repeated. Cause unknown; investigate in E-06.
- **Next:** E-03; estimated E-03–E-06 work is 6–9 engineering days after these slices.

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
