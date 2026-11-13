# 0016 — Real Excel acceptance record

**Status:** NOT RUN. This is a checklist/template, not test evidence.
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

- Automated check run/commit: pending.
- Manual failures and fixes: pending.
- Tested platform support statement: pending.
- Remaining limitations: pending.
- Reviewer/sign-off reference: pending.

A successful Office stand-in run does not complete this record. Add Windows/web
records separately if those platforms become delivery targets.
