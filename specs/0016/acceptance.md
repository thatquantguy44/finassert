# 0016 — Real Excel acceptance record

**Status:** E-06 real-Mac workflow NOT RUN. A Linux automated preflight was run
on 2026-11-15; it does not complete any real-host row below.
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
| Tested source commit and build/bundle identity | pending |
| macOS version / hardware summary | pending |
| Excel version/build / license channel | pending |
| Add-in loading route / stable API capabilities | pending |
| CDN or bundled Pyodide / engine version | pending |
| Calculation mode / date system and source | pending |
| Fixture / effective policy digest | pending |
| Run date / tester / review status | pending |

## Workflow checklist

Record actual PASS/FAIL/BLOCKED, timings and evidence references; leave unexecuted
rows pending. Repeat date-sensitive cases with both workbook epochs.

| Case | Expected observation | Actual |
| --- | --- | --- |
| Install and load | Pane ready; capabilities recorded; unsupported host explained | pending |
| Explicit table | Correct headers/body/source summary; total row excluded | pending |
| Fixed offset range | C7:H20-style bounds and physical row numbers preserved | pending |
| Filter/hidden rows | All physical data rows included and policy visible | pending |
| Financial failure | Negative market value fails at the correct row | pending |
| Navigate | Click/keyboard selects that row/cell without changing values | pending |
| Correct in Excel | Old result visibly stale; current export disabled | pending |
| Rerun | New source read; corrected input passes the intended policy | pending |
| Policy/date edit | Prior result stale even when source values are unchanged | pending |
| 1900 and 1904 | Same intended date, explicit interpretation in evidence | pending |
| Formula/calc state | Recalculation invalidates; pending/manual mode handled explicitly | pending |
| Mid-read edit | No mixed/obsolete candidate becomes Current | pending |
| Delayed event | Export/navigation preflight detects changed source | pending |
| Sort/resize/delete | Old targets rejected; table/range binding follows its contract | pending |
| Duplicate/missing key | Ambiguous or absent target explained; no guessed address | pending |
| Missing treasury series | Group/period context shown without a fabricated row | pending |
| Export parity | JSON/HTML/results sheet match canonical findings and caps | pending |
| Read-only/protected/collision | Clear export error or safe new sheet; source untouched | pending |
| Rebind/reopen pane | No duplicated events or cross-source result reuse | pending |
| Python/CLI tie-out | Same normalized input/policy/labels produce identical results | pending |
| 50,000 rows × 5 columns | Exact planted failures; complete counts; timings retained | pending |
| Network/input integrity | No cell-data transmission or source value/format edits | pending |

## Completion record

- Automated preflight: see below; final E-06 commit pending.
- Manual failures and fixes: pending.
- Tested platform support statement: pending.
- Remaining limitations: no Mac Excel host for full workflow, parity and native scale checks.
- Reviewer/sign-off reference: pending.

A successful Office stand-in run does not complete this record. Add Windows/web
records separately if those platforms become delivery targets.

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
