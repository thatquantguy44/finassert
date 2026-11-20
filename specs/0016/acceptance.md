# 0016 — Real Excel acceptance record

**Status:** E-06 partially verified on Mac. Native 50,000-row diagnostics,
verified capture, JSON/HTML/results-sheet parity, CLI tie-out and source integrity
passed on 2026-11-16. AC-07's native 1900 correction/Stale/reread/pass/export loop
passed on 2026-11-19, including actual JSON/HTML/worksheet/CLI equality and source
integrity. The native 1904 repeat passed on 2026-11-20; table/hidden/failure/race/
keyboard cases remain open.
The Home-ribbon validation/settings manifest is schema-valid and has controlled
browser-host route coverage for distinct validation and settings states; native
Home visibility and both launch actions passed on 2026-11-20 (AC-11).
Automated preflights do not
complete the remaining host rows.
Early E-01/E-02 native evidence is retained separately in [artifacts](artifacts/README.md).
E-03's partial native freshness/configuration checks are also recorded there;
they do not complete the navigation/output checklist below.
Normative behavior and criteria remain in [spec.md](spec.md#acceptance-criteria).

Use the existing [spike runbook](../../docs/design/excel-spike.md) for build,
certificate and sideload setup. Run only synthetic fixtures in a disposable
workbook. Keep diagnostics and fixture/policy digests under artifacts/; do not
commit user workbooks, contents, absolute personal paths or credentials.

## Environment to record

| Field | Actual value |
| --- | --- |
| Tested source commit and build/bundle identity | Runtime `67c3c1c`; bundled pane `b0070aa2…`; manifest `3eb69c50…`; full hashes in [native diagnostic](artifacts/e06-native-diagnostics.json) |
| macOS version / hardware summary | 26.5.1 (25F80); Mac17,9, Apple M5 Pro, 24 GiB |
| Excel version/build / license channel | Installed 16.115 / 16.115.26110837; license channel not observed |
| Add-in loading route / stable API capabilities | Microsoft sideload template; scale used localhost:3000, recovered AC-07 uses trusted HTTPS localhost:3002; stable API sets through 1.13 reported supported |
| CDN or bundled Pyodide / engine version | Bundled Pyodide 0.27.7; finassert 0.1.0 |
| Calculation mode / date system and source | Native Automatic/Done; explicit user 1900, matching the saved scale workbook; 1904 case pending |
| Fixture / effective policy digest | Native 50,000-row source, retained exports and policy identities in [parity record](artifacts/e06-native-scale-parity.json) |
| Run date / tester / review status | 2026-11-15–20; Codex automated/native UI verification; external human review pending |

## Workflow checklist

Record actual PASS/FAIL/BLOCKED, timings and evidence references; leave unexecuted
rows pending. Repeat date-sensitive cases with both workbook epochs.

| Case | Expected observation | Actual |
| --- | --- | --- |
| Install and load | Pane ready; capabilities recorded; unsupported host explained | PASS: current bundled pane Ready; capabilities through 1.13, calculation and startup recorded. Unsupported-host alternatives remain automated coverage. |
| Home ribbon | finassert group exposes validation and settings; validation opens the workflow and Settings opens its distinct settings view | PASS: static manifest/browser coverage plus native Home buttons and both launch routes on 2026-11-20; validation engine Ready. |
| Explicit table | Correct headers/body/source summary; total row excluded | pending |
| Fixed offset range | C7:H20-style bounds and physical row numbers preserved | PASS: native Sheet1!C7:H9, header 7, two physical/parsed rows, six columns; retained failure points to row 8. |
| Filter/hidden rows | All physical data rows included and policy visible | pending |
| Financial failure | Negative market value fails at the correct row | PASS: Current, one failed/two passed; market_value -400 at row 8, one retained violation/cap 20. |
| Navigate | Click/keyboard selects that row/cell without changing values | Click PASS: retained row-8 finding selects F8/-400 with fresh preflight; saved source unchanged. Keyboard case pending. |
| Correct in Excel | Old result visibly stale; current export disabled | PASS: native F8 edit produced Stale; HTML/JSON/results export and navigation disabled. Corrected numeric F8=400 verified by reread and saved file. |
| Rerun | New source read; corrected input passes the intended policy | PASS: 1900 source reread displayed 400 and both dates 2026-01-01; Current with three passes. |
| Policy/date edit | Prior result stale even when source values are unchanged | pending |
| 1900 and 1904 | Same intended date, explicit interpretation in evidence | PASS: both native epochs show 2026-01-01; 1904 full small loop and export/CLI parity retained in the demo record. |
| Formula/calc state | Recalculation invalidates; pending/manual mode handled explicitly | Automatic/Done observed; formula/recalc/manual/pending cases pending. |
| Mid-read edit | No mixed/obsolete candidate becomes Current | pending |
| Delayed event | Export/navigation preflight detects changed source | pending |
| Sort/resize/delete | Old targets rejected; table/range binding follows its contract | pending |
| Duplicate/missing key | Ambiguous or absent target explained; no guessed address | pending |
| Missing treasury series | Group/period context shown without a fabricated row | pending |
| Export parity | JSON/HTML/results sheet match canonical findings and caps | PASS on native scale and corrected AC-07: actual downloads and all 41/34 respective worksheet rows match; exact counts/caps retained. |
| Read-only/protected/collision | Clear export error or safe new sheet; source untouched | Unique results (2) preserved existing outputs/source on scale run; protected/read-only failures pending. |
| Rebind/reopen pane | No duplicated events or cross-source result reuse | pending |
| Python/CLI tie-out | Same normalized input/policy/labels produce identical results | PASS on scale and small failing/passing 1900 cases: strict canonical report/policy equality against actual CLI. Native 1904 tie-out also passes in the 2026-11-20 demo record. |
| 50,000 rows × 5 columns | Exact planted failures; complete counts; timings retained | PASS: three weight and three NAV groups fail, two data checks pass; native timings and stable captures retained. |
| Network/input integrity | No cell-data transmission or source value/format edits | PASS for observed native scale: resource/CSP diagnostic, local server trace, all source cells/types/formats and four unrelated sheets unchanged. |

## Completion record

- Automated preflight: Mac checks/tooling and historical Linux checks below.
- Native verification: scale diagnostics/capture/export/CLI/integrity and the
  [small 1900 correction loop](#2026-11-19-ac-07-native-correction-and-export-completion) pass.
- Manual failures: generated table fixture still prompts repair; an actual repair
  log identified its table part. Experimental metadata/filter variants did not
  establish a clean open. Earlier generator corrections were insufficient.
- Tested platform support statement: focused earlier Mac evidence only; full E-06
  support is not promoted by this checkpoint.
- Remaining limitations: native table/hidden-row and remaining failure/race/keyboard
  cases remain. Window-capture interruptions recovered during the 1900 loop;
  only observed actions and retained actual exports are counted.
- Reviewer/sign-off reference: external human review pending; no sign-off inferred.

A successful Office stand-in run does not complete this record. Add Windows/web
records separately if those platforms become delivery targets.

## 2026-11-20 full regression and native demo validation

[Retained evidence](artifacts/e06-native-demo-validation.json) records all 3,724
runtime and 110 browser tests passing; lint/format, mypy (64 source modules),
both Excel smoke modes, shared browser and isolated installed distribution checks
also pass. The tests now use the focused Settings view and return before actions
in validation. Recovery fixtures accept native numbered web-extension names by
content type, with 14 harness controls. Initial failures and their repairs are
recorded explicitly; no runtime financial/capture/export semantics changed.

Native Mac Excel's [50,000-row diagnostic](artifacts/e06-native-demo-diagnostics.txt)
passed every step: 951 ms startup, 241 ms write, 631 ms read and 692 ms check/render.
It found the exact three weight and three NAV groups, passed both data checks,
round-tripped the policy and confirmed unchanged source cells.

The 1904 source opened cleanly at Sheet1!C7:H9 and previewed both dates as
2026-01-01. A fresh run failed market_value at row 8 (-400) with two passes;
the finding selected F8. Explicit selection and replacement with numeric 400
produced Stale and disabled JSON/HTML/sheet exports and navigation. Run reread
the source and reached Current with three passes. Actual
[JSON](artifacts/ac07-native-1904-passed-report.json),
[HTML](artifacts/ac07-native-1904-passed-report.html),
[YAML](artifacts/ac07-native-1904-policy.yml), all 34 × 5 result-sheet cells and
an actual CLI run match. Every source value/type/number format is identical
across the native pre-export/final workbook snapshots.

`dist/demo/finassert-demo.xlsx` is saved with the passing result and completed
results/policy sheets. Its source has no stray populated cells; F8 is the only
changed value from the synthetic fixture. Excel's save normalized literal date
format escapes without changing dates; native export snapshots compare exactly.
Native capture/foreground interruptions and excluded selection attempts are
recorded in the evidence. These observations complete the 1904 small loop,
not the remaining table/hidden/failure/race/keyboard cases or external review.

## 2026-11-20 local startup and native Home-ribbon launches

Rebuilt the absent temporary add-in with the current working tree and
hash-verified bundled Pyodide 0.27.7, then restarted HTTPS localhost:3002 using
the existing development certificate. The generated manifest exactly matches
installed finassert.xml; no registration or certificate-trust change was needed.
Pane SHA-256 is `bb36604fe553c371a88a407208017885f6c192001ff15278824783a12818f04f`;
manifest SHA-256 is `561a804dfdd3b12d047e3ba14cb006427cc0e085e4d29c2f249c221f9fca4972`.

Native observations in the already open blank Book1:

1. Retry loaded the validation workflow and engine Ready.
2. Home visibly exposes Open validation and Settings.
3. Settings opened `taskpane.html?view=settings` with capture/freshness/request
   controls and Back to validation; policy/run/source workflow controls were hidden.
4. Home Open validation opened the normal source/policy/run workflow and its
   engine reached Ready. The final native screenshot also shows both Home buttons.

These observations complete AC-11's native launch slice. No source was bound,
cells edited, financial checks run or exports created in this startup session.
Settings return/session preservation retains its earlier controlled-browser
coverage; it was not retested natively. Full E-06 and external review remain open.
The previous temporary recovery workbook/fixtures are gone and must be recreated
before the native 1904 repeat. The server remains running for user testing.

## 2026-11-19 interface and Home-ribbon preparation

The task pane has a narrower, workbook-first presentation: a single explicit
workbook-source workflow, clear Current/Stale status treatment, grouped exports
and collapsible advanced/report content. The browser file picker is hidden in an
Excel host so it cannot compete with source binding.

The generated manifest now includes an additive **finassert** group on Excel
Home. **Open validation** uses the normal task-pane URL; **Settings** uses the
same URL with `view=settings`, which expands the existing freshness/capture
controls. The generated manifest passed Microsoft `office-addin-manifest validate`;
unit coverage checks both `ShowTaskpane` actions, resource URLs and generated icon
assets. A controlled 390-pixel Office stand-in reached Current through the normal
workflow and confirmed the settings route and absent browser file picker.

This is build/static and controlled-browser evidence only. Manifest reload plus
native Home-tab visibility and both launch actions must be observed in Excel before
AC-11 can be marked verified.

## 2026-11-19 AC-07 native correction and export completion

[Completion evidence](artifacts/ac07-native-completion.json) records the actual
Mac 1900 workflow. The [JSON](artifacts/ac07-native-passed-report.json) and
[HTML](artifacts/ac07-native-passed-report.html) are actual native downloads.
All 34 × 5 cells of the saved `finassert results` sheet and the real CLI match
the same run; only each action's `verified_at` differs. F8 is now numeric **400**.
Navigation left the source unchanged, and the final export sequence preserved
every pre-existing cell's value, type and number format on Sheet1 and Sheet2.
Across the initial failing source and final source, only F8 changed (-400 → 400).

The old temporary workbook/build were gone. Port 3000 belonged to a plain HTTP
Dagster server; the existing finassert development manifests still requested
HTTPS there. Rebuilt the identical bundled pane (`b0070aa2…`), served it locally
on **HTTPS port 3002** with the existing development certificate, and updated
both original-ID development manifests after backing them up. After the user
saved/closed Book1 and restarted Excel, the original-ID pane reached Ready.
An isolated test registration was removed after that recovery.

[prepare_ac07_fixture.py](artifacts/prepare_ac07_fixture.py) recreates simple
1900/1904 C7:H9 fixtures from an explicitly supplied Office-generated sideload
workbook, retaining its task-pane parts. It does not register an add-in, open
Excel, or count generated data as native evidence. Thirteen harness checks pass,
including pane-part preservation, both epochs/physical row labels, rejection of
a plain workbook and protection against overwriting the seed. Both generated
fixtures reproduce the historical failed native report/policy through the CLI;
only the 1900 fixture was opened natively in this session.

```bash
PYTHONPATH=src .venv/bin/python specs/0016/artifacts/prepare_ac07_fixture.py \
  /tmp/finassert-ac07-recovery --sideload-seed "$FINASSERT_SIDELOAD_SEED"
```

Set `FINASSERT_SIDELOAD_SEED` to the disposable workbook generated by Microsoft's
sideload tool for the registered local manifest. Do not use a user workbook.
Current native snapshots, matching final downloads and policy remain under
`/tmp/finassert-ac07-recovery`; replay their strict comparison with:

```bash
PYTHONPATH=src .venv/bin/python specs/0016/artifacts/verify_e06_exports.py \
  --json /tmp/finassert-ac07-recovery/ac07-final-1900.json \
  --html /tmp/finassert-ac07-recovery/ac07-final-1900.html \
  --workbook /tmp/finassert-ac07-recovery/native-final-1900.xlsx \
  --policy /tmp/finassert-ac07-recovery/long-only-holdings.yml \
  --results-sheet 'finassert results'
```

The initial formula-bar entry appended text, yielding -400400; rereading caught
it. Native Go To F8, clear and paste corrected it to numeric 400 before the
passing evidence. Capture errors and a binding change interrupted the first
export sequence. Rebinding/rerunning produced the consistent final evidence;
no timed-out action was counted without later visible and saved-file proof.
Full E-06 and external human review remain open.

## 2026-11-17 AC-07 progress; correction remains open

The preceding E-06 checkpoint was committed/pushed as
[`6328253`](https://github.com/thatquantguy44/finassert/commit/632825368ab69cf39d214a3d6bc6b01279bf7b43)
before continuing AC-07. Production runtime remains unchanged. Actual native
observations and hashes are in [ac07-native-progress.json](artifacts/ac07-native-progress.json);
the [failed report](artifacts/ac07-native-failed-report.json) is an actual download.

1. Applied native **Short Date** to selected H8:H9. Formula Bar H8 showed
   `1/1/2026`; the saved workbook has the 1900 epoch and both dates 2026-01-01.
2. Bound **Sheet1!C7:H9**. The pane reported header 7, two physical/parsed rows,
   six columns, explicit 1900 and both preview dates 2026-01-01; rebinding cleared
   the prior scale result. Applied the matched long-only template.
3. Run reached Current at `2026-11-17T01:54:18.516Z`: one failed, two passed,
   no errors/skips. Market value has one row-8 violation, cap 20, one shown.
4. Clicked the retained row-8 cell action. At `2026-11-17T01:55:27.109Z` it
   reported **Selected cell in row 8**; Name Box **F8**, Formula Bar **-400**.
   Current remained after preflight. Saved before/after C7:H9 values, types and
   formats match exactly.
5. Saved the actual failed JSON after another preflight at
   `2026-11-17T01:55:40.562Z`. Its complete canonical report/policy equals the
   actual CLI against the same saved workbook/region and long-only policy.
   CLI exit 1 is the expected invariant failure, not a harness error.

Native capture then repeatedly returned `cgWindowNotFound`. A pending save
sequence had earlier been resolved by saving only the known disposable workbook
and canceling at the unrelated Book1 prompt. A later isolated test launch retained
the known native E-02 seed's web-extension parts with a temporary test manifest;
CLI/SDK launch messages did not establish a visible native window. No isolated
fixture result is counted as acceptance evidence, and the production add-in ID
was not changed. User assistance to foreground the original test workbook and
dismiss dialogs was requested.

### AC-07 immediate pickup

The historical 1900 pickup above is superseded by the
[completed correction/export loop](#2026-11-19-ac-07-native-correction-and-export-completion).
F8 is saved as **400** and actual passing exports/CLI/integrity checks pass.
The native **1904** repeat is now also verified, including actual exports,
epoch/date/CLI evidence and exact source integrity; see the
[demo validation](#2026-11-20-full-regression-and-native-demo-validation).
Next complete clean table/hidden/filtered and remaining failure/race/keyboard cases. The local server
currently serves `/tmp/finassert-ac07-build` at **https://localhost:3002**;
full E-06 acceptance and external review remain open.

Retained negative-source copies are
`/tmp/finassert-ac07-native-failed-before-nav.xlsx` and
`/tmp/finassert-ac07-native-failed-after-nav.xlsx`. The actual failed export is
`/tmp/finassert-e06-fixtures/ac07-failed-1900.json`; CLI output is
`/tmp/finassert-ac07-failed-cli.json`, with policy
`/tmp/finassert-ac07-native/policy.yml`. Isolated 1900/1904 seed-derived fixtures
and their identities are in `/tmp/finassert-ac07-native`; their native opening
is unverified. The temporary test add-in ID is recorded in the progress artifact.

## 2026-11-16 native scale and export verification

The current bundled runtime opened from Microsoft's **empty sideload template**.
The CLI's `--document` option copies a supplied workbook without adding the
template's web-extension parts; a fresh openpyxl fixture does not auto-open the
pane through that option. Excel also initially retained the old localhost:3000
source despite a registered 3002 manifest. The identified old development server
was replaced with the current build at trusted localhost:3000; the disposable
template was reopened. The page hash and visible QuantSmith panel establish the
current runtime identity. No certificate trust or application security changed.

- [Native diagnostic](artifacts/e06-native-diagnostics.json): **all steps passed**.
  Engine ready **1,351 ms**; write **322 ms**, read **732 ms**, check/render
  **750 ms**, results write **95 ms**, policy round-trip **162 ms**, source check
  **229 ms**. These are actual Excel timings, distinct from the stand-in below.
- Bound the full `'finassert spike data'!A1:E50001` using native Edit → Find →
  Go To, then **Use selected range**. The source summary reported 50,000 physical
  and parsed rows, five columns and explicit 1900. A single-cell attempt was
  rejected before binding; setting only the Name Box text did not select bounds.
- **Run checks** reached Current at `2026-11-16T09:48:31.590Z`. There were exactly
  three failed groups for each financial rule, cap 20 with three shown; both data
  rules passed. The capture-to-first-Current interval was **1,562 ms**, measured
  from the artifact's capture timestamp; it is not total Run-button latency.
- Saved actual native [JSON](artifacts/e06-native-scale-report.json) and
  [HTML](artifacts/e06-native-scale-report.html) downloads through Excel's Save
  dialogs. Each action reverified the same snapshot. A new owned
  `finassert results (2)` worksheet contained the canonical 41 × 5 output.
- The [parity/integrity record](artifacts/e06-native-scale-parity.json) reports
  strict JSON/embedded-HTML/worksheet/CLI equality, including policy, full findings
  and caps. Source A1:E50001 values, types and number formats match before/after
  hashes. The four pre-existing sheets' cells/types/formats also remain identical.
- The native resource/CSP diagnostic reported no post-startup requests; the local
  server trace contained startup page/runtime GETs only. No workbook contents were
  placed in a request. The optional reference panel was not opened in this run.

### Current pickup and retained native files

**Current AC-07 pickup:** use the [later progress record](#ac-07-immediate-pickup).
The scale files and earlier stopping point below remain useful historical context;
date formatting, binding, failure and navigation have since been verified.

Saved native snapshots are `/tmp/finassert-e06-scale-native-initial.xlsx` and
`/tmp/finassert-e06-scale-native-final.xlsx`; their hashes are retained. Repeat the
actual comparison with:

```bash
PYTHONPATH=src .venv/bin/python specs/0016/artifacts/verify_e06_exports.py \
  --json /tmp/finassert-e06-fixtures/e06-native-scale.json \
  --html /tmp/finassert-e06-fixtures/e06-native-scale.html \
  --workbook /tmp/finassert-e06-scale-native-final.xlsx \
  --policy /tmp/finassert-e06-scale-policy.yml \
  --results-sheet 'finassert results (2)'
```

The live disposable workbook subsequently received the small source in
**Sheet1!C7:H9**: headers portfolio/ticker/weight/market_value/nav/date; rows
Alpha/AAA/0.4/-400/1000/46023 and Alpha/BBB/0.6/600/1000/46023. This paste was
observed, but was **not saved** into the retained scale snapshot. Native control
then repeatedly timed out while selecting H8:H9 for date formatting. A reconnect
and user assistance were requested; successful date formatting is not inferred.

Resume by inspecting/dismissing any live Go To dialog. Format H8:H9 as dates,
bind C7:H9, load the long-only policy and execute negative → navigate → correct
F8 to 400 → Stale → reread → pass → export/CLI parity. Repeat with a confirmed
1904 workbook. Fix/cleanly reopen the generated table fixture or construct the
same table natively and retain its identity; a repaired table is not acceptance
proof. Finish all pending failure/structure/race/keyboard rows and external review.
Use native Go To with its **OK** button and Save dialogs with **settable names**;
do not infer selection or keypress success from text in the Name Box alone.

## 2026-11-15 Mac preflight and blocked native setup

[Structured record](artifacts/e06-mac-preflight.json) retains build hashes,
prepared fixture identities, actual setup failures, stand-in timings and limits.
The runtime is merged main `67c3c1c`; branch
`feature/excel-e06-mac-acceptance` adds acceptance tools and documentation only.

- Existing runtime suite: **3,700 passed**, with the 107 browser cases skipped
  and run separately. New acceptance harness: **10 passed** across both epochs.
- Bundled browser suite: **104 passed**, three engine-startup timeouts; all three
  passed on focused retry. This is recorded as a retry, not a clean first run.
- Ruff check/format, mypy (64 source files), strict MkDocs and local documentation
  links/anchors pass. Wheel/sdist build and isolated installed-distribution probes
  pass. Initial builds failed with an unexpected-end-of-data read error; stable
  retries succeeded without a packaging change.
- Bundled/served and CDN-page/local-runtime Excel smoke flows and shared browser
  smoke pass. The latter runtime mode does not prove external CDN availability.
- Mac Chromium/Office stand-in 50,000 × 5 run: **8 ms write, 1,122 ms read,
  4,312 ms check/render**, exactly three failing groups each for weights and NAV,
  clean data checks, identical source values, no post-startup requests. These are
  **not native Excel timings**.
- Optional QuantSmith localhost HTTPS reader: 1,400 documents from the actual
  pinned checkout; README content matched the pinned Git blob by SHA-256.
  No document contents were retained. Native reference-panel acceptance remains.

The initial generated fixture prompted content recovery. The final generator
explicitly excludes totals from the table filter and supplies the correct legacy
policy-sheet layout; Python and actual CLI controls pass. Native Open/Go To
dialogs then repeatedly returned `cgWindowNotFound`, `noWindowsAvailable` or
invalid element IDs, including after reconnecting automation. Successful native
opening and fixture repair are **not** claimed. The user was asked to dismiss
dialogs and open the fixture; native execution must resume from that point.

### Resume with retained files

The generated workbooks and policies are disposable and local. Regeneration
changes workbook byte identities; retain the new `identities.json` for each run.

```bash
PYTHONPATH=src .venv/bin/python specs/0016/artifacts/prepare_e06_fixtures.py /tmp/finassert-e06-fixtures
```

1. Dismiss native dialogs and cleanly open `holdings-1900.xlsx` from that folder.
   Resolve any repair prompt before testing; do not accept a repaired fixture as
   proof that the generator opens cleanly. The built manifest/server are in
   `/tmp/finassert-e06-native`, at trusted HTTPS `localhost:3002`. Rebuild/restart
   using the spike runbook if the temporary server has ended.
2. Bind `AcceptanceHoldings`, choose 1900 and load `long-only-holdings.yml` (or
   the legacy saved policy). Expect two physical/parsed rows, hidden row 9
   included, totals row 10 excluded, date 2026-01-01 and one failure at F8.
   Repeat fixed range C7:H9 and the full checklist, including keyboard navigation,
   correction to 400, Stale, reread/rerun and actual exports. Repeat with 1904.
3. Save JSON/HTML downloads, policy YAML and the native workbook with results.
   Compare those **actual native files**, supplying the exact unique output name:

   ```bash
   PYTHONPATH=src .venv/bin/python specs/0016/artifacts/verify_e06_exports.py \
     --json /tmp/native-report.json --html /tmp/native-report.html \
     --workbook /tmp/native-saved.xlsx --policy /tmp/native-policy.yml \
     --results-sheet 'finassert results (2)'
   ```

   The verifier checks the embedded HTML artifact, every canonical worksheet row,
   provenance/bounds/epoch, policy, full canonical CLI results and unchanged saved
   workbook bytes. Only per-action `verified_at` may differ between exports.
   It does not inspect visible HTML layout, drive Excel, validate ownership or
   prove native execution. Its generated unit-test exports are never host evidence.
4. In a separate empty disposable workbook run native diagnostics at 1,000
   portfolios, retain timings/capabilities, then exercise the 50,000-row source
   through verified capture and output. Finish failure/structure/race rows and
   source-integrity checks; record external review separately.

## 2026-11-15 automated preflight (Linux)

- Build source: `feature/excel-diagnostic-navigation` at
  `4862ce791fd442e341e88b8390dd4fd549267d11`; browser/smoke harness and
  evidence edits are local and uncommitted.
- Host: Linux x86_64, CPython 3.11.18, Playwright 1.55.0 / Chromium 140.
- The complete non-browser Python suite passed: **3,697 tests**. The initial
  restricted-sandbox run could not open loopback sockets; the full rerun with
  loopback access passed, including the MCP integration cases.
- Ruff check, Ruff format check, mypy and strict MkDocs build passed.
- The wheel and source distribution built and passed `scripts/verify_dist.py`
  from an isolated installed environment.
- Bundled Pyodide add-in build: taskpane SHA-256
  `7bd505786c053702da501c7482609a8bc343a47e0724ee8e12f8f5e66c572c9a`;
  manifest SHA-256
  `3eb69c50794a756886325bc107f4d3b7616e64d73697736d0203c90d88ffbf45`.
- Bundled Pyodide/Office stand-in browser regression: **106 passed**. The first
  pass exposed a test harness reading `innerText` from a hidden preview; the
  corrected test reads DOM text and the complete rerun passed.
- Excel smoke passed in both bundled/served and CDN-page/local-runtime modes;
  the shared browser/file smoke passed. Their hidden-result assertions were
  corrected to read DOM text. The CDN-page mode supplied Pyodide locally and
  does not establish availability of the external CDN.
- Synthetic 50,000-row × 5-column Office stand-in diagnostic passed: 9 ms to
  write, 1,566 ms to read, 1,941 ms to check/render. It found the three planted
  failures in each grouped check, preserved source data and reported no requests
  after engine startup. These are Linux stand-in timings, not Mac Excel timings.
- No Mac Excel host is attached to this session. Environment, workflow,
  calculation, parity, 50,000-row timing and source-integrity rows above remain
  pending; prior focused native E-01–E-05 evidence is not substituted for E-06.

## 2026-11-20 named panes and human failure actions

Observed **finassert Validation** and **finassert Settings** as distinct native
Excel tabs after the approved save/restart/reopen. Each view begins with its
matching level-one heading. The updated native demo read C7:H9 with explicit 1904,
loaded the saved three-rule policy, passed all three checks, and replaced only its
completed owned results sheet after source/policy revalidation. Saved inspection
finds **If check fails** / **Block validation** beside the three passed outcomes
and the expected original source cells/dates/epoch. See
[evidence](artifacts/pane-titles-and-failure-actions.json). Full E-06 and review remain open.
