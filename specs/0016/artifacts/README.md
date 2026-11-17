# 0016 Excel workflow evidence

**Current:** E-01 completed and E-02 verified on 2026-11-13. The initial attempt
below is historical; the later native report supersedes its unresolved status.
See [E-01 completion](#e-01-native-completion) and [E-02](#e-02-source-and-date-evidence).
E-03's session-configurable freshness/capture evidence is recorded
[below](#e-03-configurable-freshness-and-stable-capture).
E-04/E-05 focused evidence and the E-06 Mac preflight are retained below;
the full host gate is still open. Current pickup is in the
[acceptance record](../acceptance.md#current-pickup-and-retained-native-files).

## E-06 native scale and exports

On 2026-11-16 the current build opened on native Mac Excel 16.115.
[Diagnostics](e06-native-diagnostics.json) record all steps passing: 1,351 ms
startup, 322 ms write, 732 ms read and 750 ms check/render for 50,000 × 5 cells.
Explicit range binding and stable capture reached Current with exact planted
findings. The [parity record](e06-native-scale-parity.json) validates actual
[JSON](e06-native-scale-report.json), [HTML](e06-native-scale-report.html), all
41 × 5 results-sheet cells and the real CLI. Source values/types/formats and
four pre-existing sheets remain identical. Source, policy, export and workbook
digests are retained; workbooks stay in temporary storage.

The generated table fixture still triggered repair; metadata/filter variants
did not establish a clean native open. The live native workbook instead received
a small C7:H9 source in Sheet1, then control timed out during date formatting.
That unsaved setup, both epochs, correction/rerun, table/hidden/failure/race cases
and external review remain. Follow the [current pickup](../acceptance.md#current-pickup-and-retained-native-files).

## E-06 Mac preflight and acceptance tools

[e06-mac-preflight.json](e06-mac-preflight.json) is the historical setup checkpoint:
it records the runtime/build identity,
prepared fixture hashes, native setup failure, Mac automated checks, stand-in
scale timings and actual pinned-checkout HTTP verification. Native dialog target
errors prevented a host acceptance claim in that attempt. The later native
scale/export record above supersedes that limitation for its executed cases.

[prepare_e06_fixtures.py](prepare_e06_fixtures.py) creates disposable 1900/1904
workbooks and validated policies. [verify_e06_exports.py](verify_e06_exports.py)
checks actual saved JSON, embedded HTML artifact, every canonical results-sheet
row and the real CLI, allowing only per-action verification time differences.
Ten harness controls pass across both epochs, including rejection of changed
source, diagnostic counts, output cells and an incorrect epoch. The harness's
generated exports are test data, never native acceptance evidence. Follow the
[resume instructions](../acceptance.md#resume-with-retained-files).

## Initial E-01 attempt (historical)

Recorded 2026-11-13 on branch feature/excel-host-baseline, from integrated main
3b5a014394054d173e7be7cb29578848a3937981. Tracking
[issue #23](https://github.com/thatquantguy44/finassert/issues/23).

## Actual Mac observations

[e01-baseline.json](e01-baseline.json) records installed-application metadata and
hashes of the unmodified main baseline built before the E-01 diagnostic changes.
Installed Excel: 16.115, build 16.115.26110837; macOS 26.5.1, build 25F80.

An existing localhost HTTPS server, development certificate files and sideloaded
finassert manifest were present. Reading its taskpane.html using the existing CA
pin succeeded; its 253,532 bytes and SHA-256 matched the fresh baseline build.
This verifies the served content identity, not Excel's certificate trust or loading.

Created an empty disposable workbook and inspected Home → Add-ins → Developer
Add-ins. finassert was listed but disabled. The pane could not be opened; the
cause was not established. Closed the empty workbook. No user workbook data,
certificate trust, application settings, existing server or sideload manifest was
changed. A connected workbook session was not available.

Microsoft's manifest validator subsequently accepted the XML schema but rejected
the old 0.1.0.0 deployment version as below 1.0. The builder now maintains manifest
deployment version 1.0.0.0 separately from the package version. The new manifest
has not replaced the existing sideloaded copy; this finding does not establish
why the native entry was disabled.
The corrected 1.0.0.0 / ExcelApi 1.7 manifest passed Microsoft's
office-addin-manifest validator. The service result establishes manifest validity,
not actual host compatibility.

**E-01 remains incomplete.** Actual Office.js requirement-set answers, calculation
mode/state, startup/read timings and a successful synthetic native read/run are
pending. E-06 acceptance has not run. Installed-app metadata and a passing browser
stand-in do not establish real Excel support.

## Automated baseline

tests/browser/test_excel_freshness.py runs the real pane and bundled Python engine
with a configurable Office stand-in and blocks non-loopback network requests.
Six controls/probe cases pass. Three strict expected failures reproduce:

1. Run evaluates the old snapshot after a worksheet cell changes.
2. Explicitly rereading changed cells leaves the old current-result export available.
3. Editing tolerance leaves the old current-result export available.

The passing control rereads and reruns the same negative D4 value and verifies the
canonical row-4 finding. Other cases cover an invalid run and the read-only
diagnostic in Automatic/Done, Manual/Pending, Automatic/Calculating and unsupported
1.9 scenarios. These are behavioral tests, not host capability evidence. E-03 must
remove the expected-failure markers as it implements freshness; strict XPASS fails CI.

Reproduce with the repository development environment and Playwright 1.55.0:

```bash
PYTHONPATH="$PWD/src" .venv/bin/python scripts/build_excel.py \
  --output-dir /tmp/finassert-e01-excel --bundle-pyodide download
uv run --with playwright==1.55.0 playwright install chromium
FINASSERT_EXCEL_PAGE=/tmp/finassert-e01-excel/taskpane.html \
  PYTHONPATH="$PWD/src" uv run --with playwright==1.55.0 \
  pytest -q -rx tests/browser/test_excel_freshness.py
```

The [API matrix](../api-matrix.md) separates the corrected current-prototype 1.7
floor from the proposed 1.9 workflow. The added diagnostic step reads host metadata
only; the existing full spike still creates and uses its synthetic sheets as
described in the [runbook](../../../docs/design/excel-spike.md).

Repository verification: 3,624 tests passed (the nine browser cases run separately),
Ruff lint/format, mypy across 62 source modules, strict MkDocs, distribution build
and isolated installed-wheel probes passed. Existing CDN and bundled/offline
Excel smoke flows passed, including canonical report counts and source integrity.

## Next host action

Resolve why Excel disables the finassert Developer Add-ins entry, then open a
fresh E-01 build using the existing [sideload/runbook](../../../docs/excel-add-in.md).
Capture the diagnostic text, exact build hashes and synthetic read/run timings.
Record failures as well as successes; do not substitute browser values for native
measurements or promote the support claim before completion.

## E-01 native completion

The corrected 1.0.0.0 / ExcelApi 1.7 manifest was built from branch HEAD ccafd3d
and replaced the existing finassert sideload manifest. HTTPS content matched the
fresh build by SHA-256 using the existing CA pin. No certificate trust or privacy
setting was changed. The menu still showed disabled add-ins; optional connected
experiences were already enabled. Microsoft's office-addin-debugging launcher
provided the working route described in its
[Mac sideload guide](https://learn.microsoft.com/en-us/office/dev/add-ins/testing/sideload-an-office-add-in-on-mac).

The CLI expects package.json in its working directory, so a disposable directory
with a minimal private package was used, without adding Node packaging to this
repository. Invocation (replace MANIFEST with the built absolute path):

```bash
npx --yes office-addin-debugging start MANIFEST desktop --app excel \
  --no-debug --no-live-reload --dev-server-port 3000
```

Opened the generated synthetic sideload workbook in native Excel. The pane became
Ready. Ran the 1,000-portfolio / 50,000-row diagnostics; every step passed. The
full [native text report](e01-native-diagnostics.txt) and
[structured baseline/build identity](e01-native-baseline.json) are retained.
Office.js reported Mac / 16.115.1108.0 (installed app 16.115.26110837), all audited
ExcelApi sets through 1.9, Automatic/Done calculation, and edit/calculation/format
event members. No stable automatic date-system path was established.

| Measured operation | Native milliseconds |
| --- | ---: |
| Engine startup | 1,062 |
| Write 50,000 synthetic rows | 265 |
| Read and preview 50,000 rows | 561 |
| Template check and render | 631 |
| Write results sheet | 41 |
| Policy save/load round-trip | 93 |
| Input-integrity reread | 158 |

The two grouped checks each found exactly three planted failing portfolios; both
data checks passed. The policy round-tripped unchanged and source values reread
identically after output. No CSP violations or post-ready requests were reported.
These are one native run's wall timings, not benchmarks or full E-06 acceptance.
The report was copied into a blank sheet in that disposable workbook and read
from its saved XLSX, preserving the native report verbatim.

E-01 is complete. The remaining E-03–E-06 estimate after E-02 is 6–9 engineering
days; race/navigation/output contracts, rather than this measured host latency,
drive that planning range. No release, distribution rollout or broad support
claim follows from the baseline.

## E-02 source and date evidence

The [native verification](e02-native-verification.json) records explicit table and
fixed-range capture, header row 7, offset bounds and a hidden second data row.
Both 1900 and 1904 selections displayed 2026-01-01 from their corresponding
serials. Moving selection to P18 preserved the C7:H9 binding; a fresh native Run
passed all three long-only checks. Exact host quoting is retained for
'Holdings O''Brien'!C7:H9. Stable ExcelApi 1.13 range-merge detection ran successfully.

An initial generated table fixture required repair. Totals were then created in
native Excel, with a -99999 sentinel in F11. The saved native fixture reopened
without repair, including its table. Its table capture ended at H10 with three
data rows; the totals row 11 was excluded. A row containing the ordinary text
Totals remained a body row: totals exclusion follows the actual table boundary,
never cell text. [Fixture identities](e02-native-fixture-identities.json) record
the temporary synthetic files; no user workbook or absolute personal path is stored.

Automated evidence: 29 browser passes and one strict expected E-03 policy-edit
freshness failure, with every non-loopback request blocked except the replaced
Office script. Tests cover fixed selection, quoted addresses, offsets/row gaps,
physical failure labels, totals, table resize/rename, ID replacement, date equality
and cleared choice, header review, structure-handler disposal, invalid/empty/
oversized input, merged headers, wide requests and failed partial reads.
The original stale-Run and rebind/export reproductions now pass; policy/event/
calculation freshness and stable captures remain E-03 work.

Verification commands:

```bash
PYTHONPATH="$PWD/src" .venv/bin/python scripts/build_excel.py \
  --output-dir /tmp/finassert-e02-browser --bundle-pyodide download
FINASSERT_EXCEL_PAGE=/tmp/finassert-e02-browser/taskpane.html \
  PYTHONPATH="$PWD/src" uv run --with playwright==1.55.0 python -m pytest -q -rx tests/browser
PYTHONPATH="$PWD/src" uv run --with playwright==1.55.0 python \
  scripts/smoke_excel.py /tmp/finassert-e02-browser/taskpane.html --serve
```

The CDN and bundled Excel smoke flows and shared browser/file smoke flow pass.
Full runtime suite: 3,624 passed (browser cases run separately); Ruff lint/format,
mypy and isolated installed-distribution verification pass. Strict documentation,
local links/anchors and whitespace are checked at session completion. E-06 remains
pending, including the complete correction/navigation/freshness/export workflow.

Final-build native recovery check: Add-in options → Reload left a blank pane;
the cause was not established. Closing the disposable workbook and reopening via
the verified sideload CLI recovered the final build. It reset to unbound/no epoch,
then explicitly read the 1904 C7:H9 source and passed all three long-only checks.
The final served-byte hash matches the build. Retain Reload recovery for E-06;
it does not invalidate the recorded source/date or initial E-01 diagnostic run.

## E-03 configurable freshness and stable capture

Recorded 2026-11-14 on feature/excel-source-binding-dates. The user selected
session-only pane controls. Defaults: live events, verified capture, two matching
captures, 5,000 rows / 50,000 cells per request and 120 seconds. Controls allow
on-demand monitoring, unverified snapshot-only mode, 2–4 captures, smaller request
bounds and 1–300 seconds. Restore defaults and cancellation are available.

[Native observations](e03-native-verification.json) retain actual Excel 16.115
results on the same disposable 1904 offset fixture as E-02. The pane opened Ready,
read C7:H9 with the hidden row included, and a verified Run passed three checks
as Current with a UTC verification time. Editing F8 to -400 made the old result
Stale and disabled HTML/JSON/sheet actions. Rerunning produced a Current result
with one financial failure and a retained physical row-8 example. Changing the
capture count to three invalidated that result. Snapshot-only mode stayed
unverified/Stale with every current-result export disabled. Restore defaults
returned the original controls. Test changes were confined to the disposable
CLI-generated workbook; the source fixture remained intact.

The [independent vectors](e03-capture-vectors.json) define typed UTF-8/JSON/SHA-256
identity for offset/quoted/Unicode sources, both date systems, number
versus text, signed zero, nulls, booleans, formats/types and private formulas.
The public evaluated snapshot digest remains distinct from the private formula
digest. Provenance has not yet been added to exported artifact schemas.

Automated verification: **72 browser cases passed, no expected failures**. These
exercise the real bundled pane/Python with non-loopback network blocked, including
immediate event/policy invalidation, unrelated edits, on-demand preflight, missing
events, successful/blocked HTML/JSON/sheet exports, failed parses, disposed
callbacks, mixed chunks and edits during evaluation, formula-only/format changes,
calculation/manual guards, overlapping jobs, cancel/timeouts, input/date/config
changes, bounds/reset/reload and digest vectors. Existing unowned results/policy
sheets are preserved and the action reports a collision; full E-05 unique-name
and durable ownership behavior remains pending.

Reproduce:

```bash
PYTHONPATH="$PWD/src" .venv/bin/python scripts/build_excel.py \
  --output-dir /tmp/finassert-e03-browser --bundle-pyodide download
FINASSERT_EXCEL_PAGE=/tmp/finassert-e03-browser/taskpane.html \
  PYTHONPATH="$PWD/src" uv run --with playwright==1.55.0 python -m pytest -q tests/browser
PYTHONPATH="$PWD/src" uv run --with playwright==1.55.0 python \
  scripts/smoke_excel.py /tmp/finassert-e03-browser/taskpane.html --serve
```

Full runtime: 3,624 passed (72 browser cases run separately); Ruff lint/format,
mypy across 62 source files, installed-distribution probes, strict MkDocs,
local Markdown links/anchors and whitespace pass. CDN and bundled Excel smoke
and shared browser/file smoke pass. The first restricted runtime attempt could
not bind loopback; the complete rerun with loopback access passed. A fresh mypy
cache resolved an internal cached-state error. A distribution attempt concurrent
with document edits hit an archive-size race; rebuild after edits passed.

This implements E-03, not complete E-06 acceptance. No atomic Excel snapshot,
interruptible host/Python operation, persistent settings, new financial outcome,
automatic validation, diagnostic navigation or broad platform support is claimed.
The historical native Reload blank-pane finding is retained for E-06; closing
and reopening through Microsoft's CLI remains the verified recovery route.

Final verification note: the latest 72-case browser run passes. A duplicate full
runtime rerun stalled before collection in local dependency file reads (confirmed
by a macOS process sample), including a fresh-bytecode-cache attempt; it was
stopped. The prior complete 3,624-test pass remains the runtime evidence; no
Python runtime implementation changed afterward. Final served bytes matched the
build and the latest native pane reopened Ready/Unbound with no epoch selected.

## E-04 diagnostic navigation

Implemented on `feature/excel-diagnostic-navigation` atop main `2515422`.
The private Python bridge resolves only canonical retained examples before labels
are serialized. The pane displays complete totals, caps and truncation, group
context and missing-target explanations. Native buttons and live feedback use
the same guarded action for keyboard and mouse. Duplicate/colliding business
keys require a unique key and rerun. No public policy or artifact schema changed.

[Focused native observations](e04-native-navigation.json) retain the actual build
hash, fixture hash, policy fingerprint and host results. On the synthetic
`'Holdings O''Brien'!C7:H9` source with explicit 1904 interpretation, a retained
negative market-value finding selected F8 from F10; the formula bar still showed
-400. Correcting F8 to 400 made the old target Stale/disabled, and rerunning
returned Current with three passing checks. Native evidence establishes this
focused action; the full [E-06 checklist](../acceptance.md) remains unexecuted.

Automated identity tests cover physical gaps/offsets, effective mapping row keys,
numeric business keys, duplicate/type-collision/unsafe keys, bounded group samples,
zero caps and unchanged canonical artifact samples. The 19 E-04 browser cases
cover cell/row selection and source preservation, keyboard/status parity,
quoted/malicious text, missing series, silent edits/sort/delete/formula changes,
worksheet/table replacement, table resize, stale/obsolete actions, cancellation,
selection failure and on-demand/four-capture settings. The 72 existing browser
regressions also passed in the full run; two newly written fixture expectations
were corrected before all 19 E-04 cases passed. Those expectations attempted an
unexposed grouped catalog setting and assumed a different missing-series reason;
canonical financial behavior was preserved.

Reproduce the focused cases using a bundled Pyodide 0.27.7 runtime:

```bash
PYTHONPATH="$PWD/src" .venv/bin/python scripts/build_excel.py \
  --output-dir /tmp/finassert-e04-browser --bundle-pyodide download
FINASSERT_EXCEL_PAGE=/tmp/finassert-e04-browser/taskpane.html \
  PYTHONPATH="$PWD/src" uv run --with playwright==1.55.0 python -m pytest -q tests/browser
PYTHONPATH="$PWD/src" .venv/bin/python -m pytest -q tests/unit/test_excel_navigation_identity.py
```

E-05 remains responsible for source provenance and durable output ownership;
E-06 remains responsible for full native workflow, export parity and scale evidence.

Final verification: 3,675 runtime tests passed, with the 91 browser cases skipped
in that ordinary job. The 72 pre-existing browser cases passed in the full browser
run and all 19 final E-04 cases passed together. Ruff lint/format, mypy (63 source
files), CDN/bundled Excel smoke, shared browser/file smoke, Markdown links/anchors,
strict MkDocs and installed wheel/source-distribution probes passed.

## E-05 evidence and safe output

E-04 was committed and pushed as `6bbf6b9`; E-05 continues on that same branch.
The private bridge validates source schema 1 and stamps optional input.excel only
after stable capture. Exports retain generated_at/captured_at and canonical
financial results; each preflight updates verified_at. Live HTML and worksheet
views show canonical complete totals/caps/truncation and all retained samples,
without a second hidden formatter cap. File/CLI artifacts stay unchanged.

New outputs always use unique names. Completed owned results can be replaced only
by explicit saved worksheet ID, with source/role checks repeated before clearing.
Policy saves use new unique sheets and a saved-policy picker; valid policy-only
actions work independently of capture settings/freshness. Ownership schema 1 is
saved in add-in-scoped workbook settings. Body/style writes remain incomplete
until acknowledged; failures/cancellation quarantine the same operation where the
host permits it and otherwise report uncertainty. No partial sheet is deleted.

[Native E-05 observations](e05-native-exports.json) identify the actual tested
build and synthetic saved workbooks. Excel 16.115.26110837 / macOS 26.5.1 created
two unique results sheets, replaced an explicitly owned destination and saved a
policy. A saved-workbook ZIP contained two results ownership entries and one
policy entry, all complete. Reopening discovered and loaded the saved policy;
after rebinding/choosing 1904, saved-ID replacement succeeded again. The source
C7:H11 values/formats/types and hidden row matched the original after both saves,
including the excluded totals sentinels. Snapshot identity stayed unchanged.

Saved-cell inspection caught native Range.values consuming a leading apostrophe
even with text formatting. The final writer escapes literal leading apostrophes;
the stand-in models that behavior. A fresh native run/export/save verifies that
Checked and Excel address equal the exact quoted source text and are stored as
strings. Source cells/formats/types and hidden state remain unchanged. The native
record distinguishes initial ownership-case bytes from the corrected final build.

Automated evidence adds 22 provenance/parity cases and 15 browser export cases:
canonical JSON/embedded HTML/sheet parity and exact Decimal samples, no second
sample cap, unknown/unsafe context rejection, unique/renamed/recreated sheets,
bound-source rejection, protected/partial/after-write failures, cancellation and
recovery, Excel cell limits, policy independence and saved ownership on a new
pane. The full runtime suite passes 3,697 tests (106 browser cases run separately).
An early full browser run had 104 passes and a test polling failure caused by
the unchanged CSP; a deterministic promise replaced the polling expression and
all export cases passed. The final whole suite passes 106 browser cases, including
the native quote regression. CDN/bundled Excel and shared browser/file smoke tests
pass. Final verification is also recorded in the master checkpoint.

Reproduce with the E-04 bundled-runtime commands, changing the output folder to
`/tmp/finassert-e05-browser`; the focused modules are
`tests/unit/test_excel_evidence_context.py` and
`tests/browser/test_excel_exports.py`. Full E-06 acceptance remains pending.

Final static/distribution checks pass: Ruff lint/format (312 files), mypy (64
source files), strict MkDocs, 21 changed Markdown files / 179 local links/anchors,
whitespace, immutable handoff history/field consistency and installed wheel/source
distribution probes. The final native build hash matches the recorded tested bytes.
