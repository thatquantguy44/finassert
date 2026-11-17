# Master handoff log

Single running record of work handed between sessions, agents, and people.
Newest entry first. Add an entry at the end of every working session; do not
rewrite old entries (append a correction instead).
This is the canonical project status, priority and pickup document. Local handoffs
and the roadmap defer to this ordering; numbered spec.md files own requirements.

## How to use

1. Read **Current state** and the newest entry before starting.
2. Pick the top item under **Next up**, or the item the previous entry names.
3. Before every nonempty commit, add a dated **Entry template** under `Entries`.
   Match its work/stopping/priority/pickup/verification fields to **Current state**
   and review **Next up**. Existing priorities may be reaffirmed explicitly.
4. Keep entries factual: link specs, PRs, and commits instead of restating them.
5. Spec-specific plans, tasks, contracts, and session details live in the numbered
   `specs/NNNN/` workspaces. This log retains project-wide state and cross-spec
   decisions; see the [spec catalog](https://github.com/thatquantguy44/finassert/blob/main/specs/README.md).
6. Stage intended work/prose, run `python3 scripts/check_handoff.py --refresh`,
   then explicitly stage this file again. Hooks/CI check the index/history and
   preserve older entries. See [the workflow](https://github.com/thatquantguy44/finassert/blob/main/CONTRIBUTING.md#master-handoff-checkpoints).

## Current state

- **Last worked on:** Worked through AC-07 native 1900 dates, exact offset binding, negative row-8 failure, F8 click navigation and failed-export/CLI parity after pushing the E-06 checkpoint.
- **Highest priority:** E-06 — Full Mac acceptance and regressions.
- **Next pickup:** Bring the original Excel add-in 9877a12e disposable workbook to the foreground on the current desktop and dismiss dialogs. Recheck F8 -400, correct to 400, observe Stale/current exports disabled, reread/run three passing checks, then retain passing exports and strict CLI/integrity evidence for AC-07.
- **Verification:** Native Short Date and saved 1900 workbook show 2026-01-01; C7:H9 binds two physical/parsed rows and six columns. Current failing run has one row-8 violation and two passes; clicking its action selects F8/-400. Actual failed JSON report/policy equal the CLI; saved before/after-navigation source values/types/formats match. Initial E-06 checkpoint checks remain passed; AC-07 is incomplete.
- **Stopping point:** Initial changes are committed/pushed as 6328253. AC-07 date/binding/failure/navigation and failing JSON/CLI checks pass; correction/Stale/reread/pass/exports remain unexecuted after native capture returned cgWindowNotFound. Last confirmed F8 is -400.
- **Branch:** `feature/excel-e06-mac-acceptance`, from main `67c3c1c`.
  Acceptance tooling, tests, evidence and documentation changed; runtime untouched.
- **Last commits:** [6328253](https://github.com/thatquantguy44/finassert/commit/632825368ab69cf39d214a3d6bc6b01279bf7b43)
  committed/pushed all E-06 scale/tooling/docs changes before AC-07.
  Main `67c3c1c` merged QuantSmith PR #28; `7af01ff` merged Excel PR #26.
- **Delivered:** E-01–E-05, canonical handoff enforcement and the pinned local
  reference reader are merged. Actual native E-06 scale/export/CLI and observed
  network/integrity evidence now verify AC-09/10 for this build. AC-07 and full
  host acceptance remain open; external human review stays separate.
- **Native evidence:** [Diagnostic](https://github.com/thatquantguy44/finassert/blob/main/specs/0016/artifacts/e06-native-diagnostics.json)
  and [parity/integrity](https://github.com/thatquantguy44/finassert/blob/main/specs/0016/artifacts/e06-native-scale-parity.json)
  retain actual host capabilities, timings, policy/snapshot/export/workbook hashes
  and exact findings. JSON/HTML exports are retained; workbooks remain temporary.
- **Native state:** Original disposable workbook has Sheet1!C7:H9 and formatted
  H8:H9. It was saved; retained failing before/after-navigation workbook copies
  are `/tmp/finassert-ac07-native-failed-before-nav.xlsx` and
  `/tmp/finassert-ac07-native-failed-after-nav.xlsx`. Last observed result was
  Current and failed; inspect live state again before editing. The unrelated
  Book1 save prompt was canceled and that workbook was left untouched.
- **Evidence/pickup:** [AC-07 progress](https://github.com/thatquantguy44/finassert/blob/main/specs/0016/acceptance.md#ac-07-immediate-pickup)
  and `specs/0016/artifacts/ac07-native-progress.json` retain actual observations,
  source/policy/export hashes and the correction pickup. The actual failed JSON
  is retained. Previous native scale evidence remains valid and separate.
- **Recovery attempt:** Isolated native-seed fixtures with retained web-extension
  parts are prepared under `/tmp/finassert-ac07-native`, using temporary test
  add-in `7710156b-0be4-5677-89fb-28358896cc33`. CLI/SDK reported launch; native
  window opening was not established. Production add-in identity is unchanged;
  no isolated result is counted as acceptance. Foreground assistance was requested.
- **Host setup:** Microsoft's empty sideload template reliably opened the pane.
  Supplied-document launch does not add web-extension parts. Excel retained the
  old 3000 source address despite a 3002 manifest; the identified old development
  server was replaced by current code at trusted localhost:3000. Build directory
  is `/tmp/finassert-e06-current`. No security or certificate trust changed.
- **Scope/review:** No broad Mac support or Windows/web acceptance claimed.
  No core dependency, financial semantics, remote protection, release/tag or
  downstream application changed. Native reference-panel acceptance remains open.
- **Reusable prompt:** [prompts/master_handoff.md](https://github.com/thatquantguy44/finassert/blob/main/prompts/master_handoff.md)
  covers Git/filesystem modes; this repository's implemented checker is Git-backed.



## Next up

1. E-06 — Full Mac acceptance and regressions.
   Foreground the original disposable workbook and complete AC-07 from the last
   confirmed F8 value -400: correct → Stale → reread/pass → exports/CLI parity.
   Dates/bounds/failure/click navigation and failed-report CLI checks now pass.
   Then finish 1904, clean table/hidden/failure/race/keyboard cases and review.
2. Paired forecast accuracy — 0012 U-08.
   Keep matching/vintage/cutoff, zero-actual and limit-combination contracts explicit.
3. Debt principal and issuance — 0012 U-09.
   Finalize conventions and extend 0002 before promoting new public rules.

## Commit context

This checkpoint is the enclosing Git commit. Recent commits below precede it;
use `git log -5 --oneline` for the live tip. Regenerate with --refresh.

<!-- finassert-handoff-checkpoint:v1 -->
```json
{
  "version": 1,
  "prior_head": "632825368ab69cf39d214a3d6bc6b01279bf7b43",
  "recent_commits": [
    {
      "commit": "632825368ab69cf39d214a3d6bc6b01279bf7b43",
      "subject": "test(excel): retain native E06 scale and export verification"
    },
    {
      "commit": "67c3c1c6ea17bf0c88f4ab62bc927a292db058b6",
      "subject": "Merge pull request #28 from thatquantguy44/feature/quantsmith-readonly-docs"
    },
    {
      "commit": "7af01ffcee0a5bccfe5c27d2740da0aea9ac593d",
      "subject": "Merge pull request #26 from thatquantguy44/feature/excel-diagnostic-navigation"
    },
    {
      "commit": "251542222cf52a34fb00e89b60279581a3728c03",
      "subject": "docs: save reusable handoff enforcement prompt"
    },
    {
      "commit": "32cf4aba736ec05eec4668df7b0d19261699c16c",
      "subject": "Merge pull request #25 from thatquantguy44/feature/excel-source-binding-dates"
    }
  ],
  "changed_paths": [
    "docs/handoff.md",
    "specs/0016/acceptance.md",
    "specs/0016/artifacts/README.md",
    "specs/0016/artifacts/ac07-native-failed-report.json",
    "specs/0016/artifacts/ac07-native-progress.json",
    "specs/0016/handoff.md",
    "specs/0016/roadmap.md",
    "specs/0016/tasks.md"
  ],
  "project_sha256": "2535c86aebb9638f66bea2c9471df24c93c143fbf5daa6a95313f6d20483d1ca",
  "reviewed_sections_sha256": "7be48b512333207e0858a090fa131f7f25bbf71365753d8312d5f80937d847a2"
}
```
<!-- /finassert-handoff-checkpoint -->

## Entry template

```markdown
### YYYY-MM-DD — short title
- **Worked on:** match Current state / Last worked on
- **Stopping point:** match Current state / Stopping point
- **Priorities:** match Current state / Highest priority and Next up item 1 title
- **Next pickup:** match Current state / Next pickup; explicitly explain if none
- **Verification:** match Current state / Verification; record actual evidence
- **Branch / PR:** 
- **Decisions / blockers:** optional additional context
```

## Entries

### 2026-11-17 — AC-07 failing case and navigation; correction blocked

- **Worked on:** Worked through AC-07 native 1900 dates, exact offset binding, negative row-8 failure, F8 click navigation and failed-export/CLI parity after pushing the E-06 checkpoint.
- **Stopping point:** Initial changes are committed/pushed as 6328253. AC-07 date/binding/failure/navigation and failing JSON/CLI checks pass; correction/Stale/reread/pass/exports remain unexecuted after native capture returned cgWindowNotFound. Last confirmed F8 is -400.
- **Priorities:** E-06 — Full Mac acceptance and regressions.
- **Next pickup:** Bring the original Excel add-in 9877a12e disposable workbook to the foreground on the current desktop and dismiss dialogs. Recheck F8 -400, correct to 400, observe Stale/current exports disabled, reread/run three passing checks, then retain passing exports and strict CLI/integrity evidence for AC-07.
- **Verification:** Native Short Date and saved 1900 workbook show 2026-01-01; C7:H9 binds two physical/parsed rows and six columns. Current failing run has one row-8 violation and two passes; clicking its action selects F8/-400. Actual failed JSON report/policy equal the CLI; saved before/after-navigation source values/types/formats match. Initial E-06 checkpoint checks remain passed; AC-07 is incomplete.
- **Delivery:** User-requested initial commit/push completed as `6328253` before
  AC-07 began. This checkpoint retains the subsequent partial native evidence.
- **Priority decision:** Reaffirm E-06 first, focusing on AC-07's remaining
  correction/Stale/reread/pass/export loop. No completion or external sign-off
  is inferred from the newly verified failing half of the workflow.
- **Host findings:** Resolved a pending save sequence by saving the known test
  workbook and canceling at unrelated Book1. Later native capture again failed;
  user assistance to foreground the original test window was requested.
  Isolated seed/manifest preparation and launch messages are setup evidence only.


### 2026-11-16 — Deliver native E-06 checkpoint before AC-07

- **Worked on:** Prepared the verified E-06 native scale checkpoint for commit/push delivery; AC-07 native correction acceptance is the next task.
- **Stopping point:** E-06 scale evidence, acceptance tooling and documentation are in the enclosing checkpoint on feature/excel-e06-mac-acceptance. AC-07 resumes from the unsaved Sheet1!C7:H9 small source; date-format setup last timed out.
- **Priorities:** E-06 — Full Mac acceptance and regressions.
- **Next pickup:** Inspect the live Excel dialog/selection, format H8:H9 as dates, bind C7:H9 and run the long-only negative-value → navigate → correct F8 to 400 → Stale → reread → pass → export/CLI workflow for AC-07.
- **Verification:** Ten acceptance-harness controls passed again before delivery; Ruff/format, strict docs, links/anchors, distribution and checkpoint checks pass. Prior native 50,000-row diagnostics, actual JSON/HTML/worksheet/CLI equality and source/unrelated-cell integrity pass. AC-07 and the remaining full E-06 host cases are still pending.
- **Priority decision:** Reaffirm E-06 first, with AC-07 as the immediate native
  task; 0012 U-08 and U-09 remain later. The user requested commit/push of all
  existing changes before continuing AC-07.
- **Delivery:** This enclosing commit includes the acceptance tools, ten controls,
  native scale evidence and current documentation. Its SHA is obtained from Git
  history; generated context records the actual prior HEAD and staged snapshot.


### 2026-11-16 — Native E-06 scale, exports and CLI/integrity verification

- **Worked on:** Completed E-06 native Mac 50,000-row diagnostics, verified capture, retained exports and strict CLI/source-integrity tie-out.
- **Stopping point:** Native scale/export parity is verified on feature/excel-e06-mac-acceptance; the small source is pasted into live Sheet1!C7:H9 but unsaved, and native control timed out during date-format setup. E-06 edits remain uncommitted.
- **Priorities:** E-06 — Full Mac acceptance and regressions.
- **Next pickup:** Inspect the live Excel dialog/selection, finish H8:H9 date formatting and the small negative-value correction/rerun, verify 1904 and table/hidden/failure/race/keyboard cases, then record external review. Follow the current pickup in 0016 acceptance.md.
- **Verification:** Native 50,000-row write/read/check-render measured 322/732/750 ms; all diagnostic steps passed. Verified capture reached Current, actual JSON/HTML/all 41 results-sheet rows and CLI match, and source plus four unrelated sheets preserve cells/types/formats. Prior 3,700 runtime plus ten harness controls and 107 browser cases across retries passed; quality/docs/smoke/distribution checks passed. Full E-06 remains open.
- **Priority decision:** Reaffirmed E-06 ahead of 0012 U-08 and U-09. Native scale
  evidence completes that gate; the small correction/date and remaining host cases
  still own the highest priority. External review is not inferred from automation.
- **Correction to prior checkpoint:** Current-build native pane loading, scale,
  verified capture, actual downloads/sheet output, CLI and integrity now pass.
  The previous no-native-execution state remains historical. Generated table
  repair was still reproduced; tentative metadata/filter fixes did not establish
  a clean open and were not retained as a solution.
- **Retained evidence:** Actual diagnostic and JSON/HTML export files plus strict
  parity/source/unrelated-cell hashes are in 0016 artifacts. Local native workbook
  snapshots are saved; the subsequent small C7:H9 paste is unsaved.
- **Host findings:** The CLI's empty template injects the add-in; --document only
  copies its input. Cached source-address behavior required serving the current
  build at the known 3000 URL. Native Go To plus OK confirmed bounds; Name Box
  text alone did not. A single-cell bind was correctly rejected.


### 2026-11-16 — E-06 acceptance tools and Mac setup checkpoint

- **Worked on:** Built E-06 synthetic epoch fixtures and a retained-export/CLI verifier, ran Mac automated regressions, and attempted native acceptance setup.
- **Stopping point:** E-06 tooling/evidence is uncommitted on feature/excel-e06-mac-acceptance; native file-dialog window-target errors block clean fixture opening and the new host workflow.
- **Priorities:** E-06 — Full Mac acceptance and regressions.
- **Next pickup:** Restore a controllable Mac Excel workbook window, cleanly open the prepared 1900 fixture, then follow 0016 acceptance.md for both epochs, actual export/CLI parity, failure/race cases, native 50,000-row timings and external review.
- **Verification:** 3,700 existing runtime tests and ten new acceptance-harness controls passed. Bundled browser: 104 passed, three startup timeouts, all three passed on retry. Ruff/format, mypy, strict docs, links/anchors, both Excel runtime smokes, shared browser smoke, 50,000-row stand-in and isolated package verification passed. No new native acceptance row completed; see specs/0016/artifacts/e06-mac-preflight.json.
- **Priority decision:** Reaffirmed E-06 first, then 0012 U-08 and U-09. A native
  setup blocker does not authorize promoting the support gate or skipping it.
- **Delivery correction:** PR #28 is merged at `67c3c1c`; the older entry's draft
  PR status is historical. Current branch starts from that merged main.
- **Changes:** Disposable fixture generator, strict retained-export verifier,
  ten harness controls and actual preflight/setup evidence. No production change.
  JSON/HTML canonical artifacts and every sheet row must agree, with only
  per-action verification timestamps varying; the actual CLI must agree too.
- **Limits:** First generated workbook hit recovery; corrected fixture has not
  been cleanly opened in native Excel. UI automation errors prevented further
  work. Prepared/generated test outputs are not host evidence. External review
  remains a separate human task; no sign-off invented.


### 2026-11-15 — Route QuantSmith directly to main

- **Worked on:** Opened a direct QuantSmith delivery PR after the stacked PR merged into the Excel branch following its merge to main.
- **Stopping point:** QuantSmith is pending review in direct-to-main draft PR #28; private-checkout/live Excel reference verification and full E-06 Mac acceptance remain.
- **Priorities:** E-06 — Full Mac acceptance and regressions.
- **Next pickup:** Execute the pending real-host rows of 0016 acceptance.md on Mac Excel, including both epochs, CLI/export parity and 50,000-row native timings; obtain external review.
- **Verification:** PR #28 shows the QuantSmith reader across 27 changed files against main and is mergeable. The prior combined branch passed 3,700 runtime and 107 bundled browser tests, smoke checks, Ruff/format, mypy, strict docs and distribution verification. This checkpoint changes only handoff documentation; private-checkout and Mac Excel checks remain pending.
- **Branch / PR:** [Draft PR #28](https://github.com/thatquantguy44/finassert/pull/28) targets main from `feature/quantsmith-readonly-docs`. PR #26 merged into main first; PR #27 then merged the QuantSmith commit into the Excel branch. No revert or repeated implementation is needed.

### 2026-11-15 — Optional pinned QuantSmith reference in Excel

- **Worked on:** Implemented an optional pinned QuantSmith reference reader for the Excel add-in; E-06 Mac acceptance remains open on the Excel branch.
- **Stopping point:** The optional QuantSmith reader is implemented in this checkpoint; private-checkout/live Excel reference verification and full E-06 Mac acceptance remain.
- **Priorities:** E-06 — Full Mac acceptance and regressions.
- **Next pickup:** Execute the pending real-host rows of 0016 acceptance.md on Mac Excel, including both epochs, CLI/export parity and 50,000-row native timings; obtain external review.
- **Verification:** 3,700 runtime and 107 bundled browser tests pass, including synthetic pinned Git/API and reference-panel coverage. Both Excel smoke modes, shared browser/file smoke, a 50,000-row Office stand-in diagnostic, Ruff/format, mypy, strict docs and isolated distribution probes pass. No private QuantSmith checkout or Mac Excel host was available for live reference/native acceptance.
- **Branch / evidence:** `feature/quantsmith-readonly-docs` based on Excel draft PR #26 at `c4b169a`; see spec `0018` and [the local reader guide](quantsmith-reference.md). The lock pins QuantSmith `86eed7f47d2735964705ecd6d43be842f594ba2f`. No private file is bundled or served in this workspace.

### 2026-11-15 — E-06 automated preflight; Mac acceptance pending

- **Worked on:** Ran E-06 Linux automated preflight and repaired hidden-DOM browser/smoke assertions; real Mac acceptance remains open.
- **Stopping point:** E-06 automated preflight is recorded locally; full Mac acceptance and external review remain.
- **Priorities:** E-06 — Full Mac acceptance and regressions.
- **Next pickup:** Execute the pending real-host rows of 0016 acceptance.md on Mac Excel, including both epochs, CLI/export parity and 50,000-row native timings; obtain external review.
- **Verification:** 3,697 runtime and 106 bundled browser tests, both Excel smoke modes, shared browser/file smoke, a 50,000-row Office stand-in diagnostic, Ruff/format, mypy, strict docs and isolated distribution probes pass. No E-06 real-host row ran.
- **Branch / evidence:** `feature/excel-diagnostic-navigation` at `4862ce7` plus
  E-06 test-harness and documentation edits in this checkpoint. See
  [the acceptance record](https://github.com/thatquantguy44/finassert/blob/feature/excel-diagnostic-navigation/specs/0016/acceptance.md#2026-11-15-automated-preflight-linux).
  No Mac host was available, so AC-07/09/10 and E-06 remain open.

### 2026-11-15 — E-05 verified evidence and safe output on the E-04 branch

- **Worked on:** Implemented E-05 verified snapshot provenance, canonical output parity, durable ownership and safe partial-write recovery.
- **Stopping point:** E-04 and E-05 are implemented and verified in this branch checkpoint; full E-06 acceptance remains.
- **Priorities:** E-06 — Full Mac acceptance and regressions.
- **Next pickup:** Execute 0016 acceptance.md on the completed E-01–E-05 build, including full Mac workflow, CLI/export parity and 50,000-row timings.
- **Verification:** 3,697 runtime and 106 browser tests pass; native exports/ownership/literal addresses/source integrity, Ruff/format, mypy, all smoke flows, strict docs/links and installed distribution probes pass.
- **Branch / commits:** feature/excel-diagnostic-navigation; E-04 6bbf6b9 is
  pushed, E-05 is this enclosing checkpoint. Commit/push authorized on the same
  branch; no PR, merge, release or branch-protection change requested.
- **Decisions:** Optional scalar input.excel source schema 1; immutable canonical
  financial results and captured snapshot identity. Unique outputs by default,
  explicit saved-ID completed-results replacement, source/role guards, policy-only
  independence and best-effort incomplete-write recovery. No source records or
  session/navigation maps are exported; file/CLI behavior stays compatible.
- **Native correction:** Saved-file inspection exposed Excel consuming a leading
  apostrophe. The final writer preserves literal quotes; native stored addresses
  now match exactly. Native/build/fixture evidence is in the E-05 artifact record.

### 2026-11-15 — E-04 commit checkpoint; E-05 authorized on this branch

- **Worked on:** Implemented E-04 bounded diagnostic navigation with source verification, identity guards and native Mac evidence.
- **Stopping point:** E-04 implementation and evidence are recorded in this checkpoint; E-05 is authorized next on feature/excel-diagnostic-navigation.
- **Priorities:** E-05 — Evidence and export.
- **Next pickup:** Implement 0016 R-05 source provenance, safe output ownership and export parity on this same branch, as authorized.
- **Verification:** 3,675 runtime tests, 72 existing browser cases and 19 E-04 cases pass; native F8/correction/rerun, Ruff/mypy, CDN/bundled/shared-browser smoke, strict docs/links and installed distribution probes pass.
- **Delivery:** User requested commit/push and adding E-05 to this branch.
  This checkpoint contains E-04; the next implementation checkpoint will record
  its actual commit and E-05 verification. No merge or release is authorized.

### 2026-11-15 — E-04 diagnostic navigation implementation

- **Worked on:** Implemented E-04 bounded diagnostic navigation with source verification, identity guards and native Mac evidence.
- **Stopping point:** E-04 is implemented and verified in the working tree on feature/excel-diagnostic-navigation; changes are uncommitted.
- **Priorities:** E-05 — Evidence and export.
- **Next pickup:** Review E-04 changes/evidence, then implement 0016 R-05 source provenance, safe output ownership and export parity.
- **Verification:** 3,675 runtime tests, 72 existing browser cases and 19 E-04 cases pass; native F8/correction/rerun, Ruff/mypy, CDN/bundled/shared-browser smoke, strict docs/links and installed distribution probes pass.
- **Branch / PR:** feature/excel-diagnostic-navigation, based on main 2515422;
  no new commit/push/PR. Existing E-01–E-03 implementation PR #25 remains merged.
- **Decisions:** Private live-only metadata resolves retained native labels before
  JSON, never business keys as row numbers. Duplicate/serialized/unsafe keys
  require unique mapping and rerun. No source row means no target. Navigation
  selects only a bound cell/row rectangle after configured capture preflight.
  Canonical artifacts, financial outcomes and file/browser responses are unchanged.
- **Evidence:** specs/0016/artifacts/e04-native-navigation.json records actual
  build/fixture hashes, policy fingerprint, quoted offset source, native F8
  selection and the corrected Current run. Full E-06 remains unexecuted.

### 2026-11-15 — Save reusable prompt on main after PR merge

- **Worked on:** Saved the reusable Git/filesystem handoff prompt on main and recorded PR #25's merge.
- **Stopping point:** PR #25 is merged into main; the reusable prompt is saved and E-04 has not started.
- **Priorities:** E-04 — Diagnostic navigation.
- **Next pickup:** Read 0016 R-03; build bounded findings and physical row/cell targets using E-03 source verification.
- **Verification:** Markdown links/anchors, strict MkDocs, whitespace and staged handoff/author checks pass; runtime code is unchanged.
- **Delivery:** User requested committing the untracked prompts/master_handoff.md
  directly to main. Main was fast-forwarded to origin/main's merge commit
  32cf4ab; the prompt text is preserved. This checkpoint also corrects the current
  PR/branch state after [PR #25](https://github.com/thatquantguy44/finassert/pull/25)
  merged. Older open-PR entries remain historical and unchanged.
- **Scope:** Documentation only. The prompt describes a portable Git/filesystem
  workflow; it does not implement filesystem mode in finassert. Existing runtime
  and native/browser evidence is carried forward, not claimed as rerun here.
- **Pickup:** E-04 remains highest; start its own feature branch from main.
  E-05 provenance/output ownership and E-06 full Mac acceptance remain pending.

### 2026-11-15 — Open implementation PR and record pickup

- **Worked on:** Opened PR #25 for Excel E-01–E-03 and canonical handoff guards; recorded delivery and pickup.
- **Stopping point:** PR #25 is open for review; implementation is committed/pushed and E-04 has not started.
- **Priorities:** E-04 — Diagnostic navigation.
- **Next pickup:** Read 0016 R-03; build bounded findings and physical row/cell targets using E-03 source verification.
- **Verification:** Documentation links/anchors, strict MkDocs, whitespace and guarded checkpoint checks pass; implementation verification is retained in PR #25.
- **PR:** [#25](https://github.com/thatquantguy44/finassert/pull/25), targeting main.
  It includes 4822db8 (Excel/native evidence) and e8d3526 (handoff enforcement),
  after the branch-preparation commit. Existing implementation was already clean,
  committed and pushed; this entry records the PR without changing runtime code.
- **Evidence carried forward:** 3,662 runtime tests, 38 Git/hook cases, 72 separate
  browser cases and native Mac evidence. The previous handoff push workflow
  [passed](https://github.com/thatquantguy44/finassert/actions/runs/43675401872).
  PR checks run against the final head; review/merge remains separate.
- **Remaining:** E-04 navigation, E-05 provenance/output ownership, E-06 full Mac
  acceptance and remote required-status administration. No merge or release.

### 2026-11-14 — Canonical handoff enforcement

- **Worked on:** Spec 0017 canonical master handoff guards for commits, pushes and CI.
- **Stopping point:** Handoff enforcement is implemented; Excel E-01–E-03 are complete and E-04 has not started.
- **Priorities:** E-04 — Diagnostic navigation.
- **Next pickup:** Read 0016 R-03; build bounded findings and physical row/cell targets using E-03 source verification.
- **Verification:** 3,662 runtime tests (including 38 Git/hook cases), Ruff/format, mypy, strict docs, links/anchors and staged checkpoint checks pass.
- **Guard behavior:** Nonempty commits require a complete staged checkpoint and
  immutable old Entries. Generated context records actual prior commits, changed
  paths and snapshot digests; refresh never stages files or invents priorities.
  Pre-push/CI inspect every new commit, including locally bypassed commits.
- **Compatibility:** Unchanged complete snapshots can pass merge/squash transport;
  integration changing project content needs refreshed context. Earlier unguarded
  history remains historical. Existing author enforcement remains active.
- **Limits:** Semantic accuracy needs contributor review. Local hooks must be
  enabled in each clone; remote branch protection must require the CI check for
  repository-wide merge enforcement. No remote administrative setting changed.
- **Prior checkpoint:** 4822db8 committed/pushed the Excel implementation. Its
  native/72-browser/earlier 3,624-runtime evidence and duplicate-import-read caveat
  remain recorded below. No financial/runtime behavior changes in this guard work.
- **Resume:** The same E-04 pickup remains highest; 0017 does not move product
  priorities. Read the owning spec instructions/contracts/tasks before coding.

### 2026-11-14 — Excel checkpoint and next-session pickup

- **Branch:** [feature/excel-source-binding-dates](https://github.com/thatquantguy44/finassert/tree/feature/excel-source-binding-dates).
  This checkpoint packages the completed E-01 native verification, E-02 explicit
  source/date binding and configurable E-03 freshness/stable capture.
- **Stopping point:** E-04 has not started. Continue with the first unchecked
  task in [0016 tasks](https://github.com/thatquantguy44/finassert/blob/feature/excel-source-binding-dates/specs/0016/tasks.md)
  after reading that workspace's AGENTS.md, R-03, contracts and newest handoff.
  Start with canonical bounded findings and exact physical row/cell targets;
  reuse source verification before navigation. Financial outcomes stay unchanged.
- **Verification:** Latest 72 browser cases, native freshness/configuration checks,
  CDN/bundled Excel and shared browser/file smoke passed. The earlier complete
  runtime run passed 3,624 tests; duplicate runs were stopped during blocked
  dependency imports. Quality, distributions, links/anchors and strict docs pass.
  This commit/push changes no runtime behavior beyond the already verified work.
- **Host recovery:** Latest pane opened Ready/Unbound; rebind and choose the epoch
  for another session. Keep the historical blank Reload finding open for E-06;
  closing/reopening through Microsoft's sideload CLI is the verified recovery.
- **Remaining:** E-04 navigation, E-05 source provenance/durable output ownership,
  then full E-06 Mac correction/navigation/export acceptance. No broad platform
  support, release or main-branch promotion is implied by this checkpoint.

### 2026-11-14 — Session-configurable Excel freshness and capture

- **Branch:** feature/excel-source-binding-dates; user chose session-only pane controls.
- **Done:** E-03 freshness states, event/on-demand monitoring, verified/snapshot-only
  capture, 2–4 comparisons, request-size/time limits, cancel/defaults, calculation
  guards and generation-safe publication. Existing JSON/HTML/sheet actions always
  reverify Current results; unverified or historical results cannot export.
- **Cross-spec:** 0011's shared app invalidates policy/input results; financial
  outcomes, Python/file APIs and artifact schemas stay compatible. Canonical typed
  capture vectors and private formula identity live under 0016. Pre-existing
  output-name collisions are refused; full E-05 ownership/provenance remains pending.
- **Evidence:** Native Excel edit → Stale → reread/Current financial failure,
  snapshot-only export blocking and configuration/default controls verified.
  3,624 runtime tests, 72 browser cases, CDN/bundled Excel and shared browser/file
  smoke, quality/distribution/docs checks. See
  [local evidence](https://github.com/thatquantguy44/finassert/blob/feature/excel-source-binding-dates/specs/0016/artifacts/README.md#e-03-configurable-freshness-and-stable-capture).
- **Next:** E-04 navigation, E-05 evidence/output and E-06 complete Mac acceptance.
  Changes remain local; no commit/push/publication performed in this turn.

### 2026-11-13 — Native Excel baseline and explicit source/date binding complete

- **Branch:** feature/excel-source-binding-dates; local implementation, no rollout.
- **Done:** E-01 corrected manifest built/sideloaded; native pane Ready and all
  diagnostic steps PASS in Excel 16.115 / macOS 26.5.1. Fifty-thousand-row timings:
  startup 1,062 ms, read/preview 561 ms, check/render 631 ms. Actual capability and
  calculation metadata, original failures and build identities retained.
- **E-02:** Explicit table/fixed-range binding, exact IDs/bounds, totals exclusion,
  visibility/input guards, bounded reads and required 1900/1904 selection. Native
  offsets/hidden rows/totals/date equality and selection-preserving Run verified.
- **Cross-spec:** 0011 compatibility notes updated. Range merged-header detection
  requires stable ExcelApi 1.13; earlier hosts can choose a table. Python/file,
  financial outcomes, policy and artifact schemas remain compatible.
- **Verify:** 3,624 runtime tests; browser source/date regressions plus one expected
  E-03 policy-freshness failure; CDN/bundled Excel and shared browser/file smoke,
  Ruff/format, mypy, distributions, strict docs, local links/anchors and whitespace.
  See [spec evidence](https://github.com/thatquantguy44/finassert/blob/feature/excel-source-binding-dates/specs/0016/artifacts/README.md).
- **Host recovery:** Reload left a blank pane; CLI reopening recovered the final
  build and repeated a passing 1904 check. Cause remains an E-06 investigation.
- **Next:** E-03 stable capture/freshness; E-04–E-06 remain proposed. Full Mac
  correction/navigation/export acceptance and broader platform support are pending.

### 2026-11-13 — Prepare the source-binding and dates branch

- **Request:** Create the next branch off main and identify the next build slice.
- **Done:** Fetched origin, fast-forwarded local main to 00ce4d9 (merged PR #24),
  and created feature/excel-source-binding-dates directly from that commit.
- **Next code slice:** Spec 0016 E-02: explicit table/range binding, exact source
  identity/bounds, totals exclusion, input guards and required 1900/1904 choice.
- **Gate:** E-01's native loading/capability/read/run evidence is still pending.
  Branch preparation does not complete E-01 or start/promote E-02 acceptance.
- **Verification:** Branch base equals origin/main; strict MkDocs and whitespace
  checks passed for the handoff/roadmap update. No runtime behavior changed.
- **Next:** Complete the native E-01 baseline, then implement E-02 in task order.

### 2026-11-13 — Publish Excel E-01 draft PR

- **Commit / PR:** 950a03e and [draft PR #24](https://github.com/thatquantguy44/finassert/pull/24),
  from feature/excel-host-baseline to main. Verified the implementation commit was
  already pushed; linked the draft in both handoffs.
- **Scope:** E-01 regressions, API/diagnostic work, manifest corrections and native
  baseline findings. The draft records the disabled add-in entry; it does not
  close issue #23 or claim real-host acceptance.
- **Verification:** Prior implementation evidence remains recorded below;
  publication changes only handoff links. Strict MkDocs and whitespace passed.
- **Next:** Resolve native loading and finish E-01's read/run measurements.

### 2026-11-13 — Start Excel E-01 baseline and regression slice

- **Branch / issue:** feature/excel-host-baseline from refreshed main 3b5a014;
  [#23](https://github.com/thatquantguy44/finassert/issues/23). Scope PR #22 is merged.
- **Done:** Three strict expected-failure browser reproductions with passing
  controls; stable Office API audit; read-only calculation/event diagnostic;
  prototype requirement corrected to 1.7, proposed workflow floor retained at 1.9.
  Separated manifest deployment version from the package after validator rejection.
- **Host evidence:** Installed Excel 16.115 on macOS 26.5.1; served baseline matches
  fresh main byte for byte. The Developer Add-ins entry is disabled; native pane
  loading and actual Office.js measurements remain pending. Existing server,
  certificate trust, sideload manifest and user workbook data were not changed.
- **Verification:** 3,624 tests passed (nine browser tests run separately: six pass,
  three expected failures); CDN and bundled/offline Excel smoke flows passed.
  Ruff/format, mypy, strict MkDocs, isolated installed-distribution verification
  and Microsoft's corrected manifest validation passed.
- **Next:** Resolve native loading and record capabilities/timings before completing
  E-01. Stale-result fixes remain E-03; distribution remains deferred.

### 2026-11-13 — Publish the Excel workflow scope PR

- **Commit / PR:** d035bba and [PR #22](https://github.com/thatquantguy44/finassert/pull/22),
  from docs/spec-0016-excel-validation-workflow to main. Ready for review.
- **Done:** Committed and pushed all scoped changes; verified the PR contains 16
  documentation files on top of merged PR #21.
- **Verify:** Local documentation/coverage/whitespace checks passed; remote check
  results are recorded on the PR. Runtime implementation remains pending.
- **Next:** Review scope, then spec 0016 E-01.

### 2026-11-13 — Prepare Excel workflow scope for main

- **Request:** Commit and push all scoped changes and open a PR targeting main.
- **Branch:** `docs/spec-0016-excel-validation-workflow`, fast-forwarded onto
  `8d96fdc`, the merge of PR #21. The PR adds documentation only.
- **Scope:** Complete spec 0016 workspace, ordered tasks, manual acceptance
  checklist and updated catalog/interface/project priorities. Add-in distribution
  remains later work; no runtime or real-host acceptance is claimed.
- **Verification:** 16 Markdown files / 80 local links and anchors,
  workspace/task/acceptance coverage, whitespace and strict MkDocs passed.
- **Next:** Review scope; implementation starts with E-01.

### 2026-11-13 — Scope the next Excel add-in milestone

- **Branch:** `docs/spec-0016-excel-validation-workflow`, based on `ab24d76`.
- **Done:** [Spec 0016](https://github.com/thatquantguy44/finassert/blob/main/specs/0016/spec.md)
  defines one-source binding, freshness/run lifecycle, diagnostic navigation,
  explicit date interpretation, safe evidence export and real Mac acceptance.
  Required workspace files plus a manual acceptance checklist define six ordered
  implementation tasks, ten acceptance criteria and an 8–12-day planning range.
- **Decisions:** Prioritize this Excel workflow before 0012 U-08/U-09. Keep shared
  financial outcomes unchanged; captured input and policy govern current results.
- **Not done:** Implementation, host/certificate setup, pilot execution and rollout
  remain pending. The existing six-slice PR remains a separate delivery.
- **Verify:** 16 Markdown files / 80 local links and anchors, workspace/task/criteria
  coverage, strict MkDocs and whitespace checks passed. No runtime behavior changed.
- **Next:** Spec 0016 E-01.

### 2026-11-13 — Six ordered upstream slices delivered

- **Branch / PR:** `feature/six-slice-upstream-delivery`, [draft PR #21](https://github.com/thatquantguy44/finassert/pull/21), issue #20.
- **Done:** Verified release bundle (0015), bounded property profiles (0009),
  explicit workbook visibility/edge cases (0013), cash buffer, facility
  capacity/continuity/maturity and versioned cash/funding pack (0012).
- **Verify:** 3,624 tests passed; Ruff/format, mypy, strict MkDocs, browser/Excel
  builds and isolated installed-wheel CLI/FX/workbook/treasury probes passed.
- **Evidence:** Clean source `f0b9667`; [bundle hashes and commands](https://github.com/thatquantguy44/finassert/blob/feature/six-slice-upstream-delivery/specs/0015/artifacts/README.md).
- **Scope:** No tag, package publication or downstream app change. PR review remains pending.
- **Next:** Paired forecast accuracy (0012 U-08), then debt principal/issuance (U-09).

### 2026-11-13 — Ordered six-slice upstream delivery started

- **Branch:** `feature/six-slice-upstream-delivery`, issue #20.
- **Baseline:** PRs #17–#19 are merged; their historical draft labels below describe
  the earlier session, not current merge status.
- **Plan:** Verified bundle (0015), properties (0009), Excel (0013), cash buffer,
  facility schedule and policy pack (0012). Acceptance is pending for each slice.
- **Next:** Complete slice 1; no downstream runtime or release publication is authorized.

### 2026-11-13 — Measure multi-rule policies and share bounded column reads

- **Branch / PR:** `feature/shared-column-reads`, [draft PR #19](https://github.com/thatquantguy44/finassert/pull/19), from merged PR #18 (`28388d7`).
- **Done:** All four requested items: 1/10/50-rule benchmarks, extraction time/
  count and peak-memory evidence, a justified private shared-read prototype,
  and complete report/Decimal/row identity/unit-provenance parity verification.
- **Measurement:** All 24 reference/optimized reports match. Fifty shared-column
  rules materialize once rather than fifty times; peak memory stays flat.
  Alternating pairs show 5.0–7.2% wall gains in three workloads; Decimal pandas
  is neutral. All raw runs, including mixed timing differences, are retained in
  [spec 0010 evidence](https://github.com/thatquantguy44/finassert/blob/main/specs/0010/artifacts/README.md#shared-column-reads).
- **Verification:** 3,484 tests passed, including 2,644 captured-reference tests.
  Custom rules/tolerances, overloaded scalars, lazy/one-shot inputs, reset hooks, nested/
  concurrent calls, Decimal labels and per-rule FX provenance have regressions.
  Ruff lint/format, mypy (59 modules), strict docs, wheel/sdist build and isolated installed CLI/unit/FX/workbook
  flows pass.
- **Decisions:** One-column per-call retention; exact eligible built-ins only.
  No cached numeric reduction or unit context. Unsupported cases preserve scalar
  behavior. Public signatures/schemas remain unchanged; no merge/release.
- **Next step:** Review this branch and scoped fallbacks before further kernels.

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
