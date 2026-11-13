# 0016 — Excel add-in validation workflow: plan

**Status:** E-01 in progress; later workflow tasks remain proposed.

## Approach

Deliver one reviewable milestone in six ordered implementation commits. Freeze
the [requirements and acceptance criteria](spec.md#acceptance-criteria) first;
record host/API discoveries as amendments rather than weakening currentness or
financial parity to make a test pass. Keep commits usable as a stack; do not
ship an intermediate UI that labels unverified snapshots Current.

| Step | Work and completion evidence | Estimate |
| --- | --- | --- |
| E-01 | Open the implementation proposal issue; reproduce stale-results behavior; inventory stable Office APIs/sets; install/read/run the current build on Mac and retain environment/timing findings | 1 day |
| E-02 | Table/range picker, source descriptor, totals/visibility/bounds, explicit date-system choice, source-error UI and capture fixtures | 1–2 days |
| E-03 | One active operation, generations, stable captures, calculation checks, event lifecycle, shared-app invalidation and pre-action verification | 2–3 days |
| E-04 | Canonical diagnostic panel, bounded row/cell navigation and keyboard actions; offset/key/group/missing-target tests | 1–2 days |
| E-05 | Versioned source provenance, verified JSON/HTML/results-sheet export, owned-output/source-overlap guards and write-error recovery | 1–2 days |
| E-06 | Complete real Mac workflow, 50,000-row measurements, parity/input-integrity evidence, regression suite and user documentation | 2 days |

The 8–12-day aggregate is a planning range for one engineer. E-01 refines it;
access to a real Excel installation can affect elapsed time. The disabled local
Developer Add-ins entry blocks E-01's native read/run measurements; the remaining
8–12-day estimate is not refined from stand-in timings.

## Dependencies and affected areas

| Area | Expected change |
| --- | --- |
| web/excel.js, web/excel-panel.html | Source picker, host lifecycle, date choice, selection/navigation and output guards |
| web/app.js, web/index.html, web/excel-results.html | Shared result invalidation, current/stale controls, diagnostic actions and accessible feedback |
| src/finassert/web.py, src/finassert/excel.py | Private source-context/navigation support and existing Python parsing/report reuse |
| src/finassert/reporting/artifact.py | Optional additive input.excel context; legacy artifacts unchanged |
| scripts/build_excel.py | Stable API requirements/capability messaging; retain CDN and bundled builds |
| scripts/excel_stub.js, scripts/smoke_excel.py | Controllable capability/event/structural/race/write-failure scenarios |
| tests/unit/test_excel.py, test_web_bridge.py, test_build_excel.py | Input, date, source/provenance, lifecycle and compatibility regressions |
| docs/excel-add-in.md, docs/design/excel-spike.md | User workflow, changed defaults and real-host evidence |

Add focused test modules when existing files no longer fit. This is an expected
area list, not permission to rewrite the engine or every shared UI component.
Spec 0011 remains the interface parent; update its compatibility notes and 0005's
artifact contract with implementation. File-reader changes require 0013 review.

This scope was inspected at ab24d76. PR #21 is now merged; the scope branch has
been fast-forwarded onto main at 8d96fdc. The scope PR adds documentation only.
E-01 refreshed onto main at 3b5a014 (merged scope PR #22) on branch
feature/excel-host-baseline. No stacked PR dependency remains from the original
six-slice delivery. See [API findings](api-matrix.md) and [baseline](artifacts/README.md).

## Implementation decisions to retain

- Bind one source per session. Persisted configurations are deferred.
- Use stable Office APIs; initial baseline ExcelApi 1.9, verified in E-01.
- Require an explicit date-system choice unless stable host detection is proven.
- Events invalidate; captures and generation checks authorize current-result use.
- Read again on Run and before navigation/export; do not trust cached selection.
- Use canonical diagnostic samples and exact row mappings; never guess a target.
- Keep prior results historical on invalidation; no new engine status or automatic
  revalidation. A Current result may still be failed/error/skipped.
- Preserve source cells; owned output cannot overwrite a bound source.

## Verification

For this documentation scope: check local links/anchors, required workspace files,
requirement/task/acceptance coverage, whitespace and strict MkDocs. Runtime tests
are not evidence of a proposed capability and need not be rerun for these files.

For implementation, start with focused existing tests plus the new lifecycle and
navigation modules added by E-02–E-05:

```bash
PYTHONPATH="$PWD/src" .venv/bin/python -m pytest -q \
  tests/unit/test_excel.py tests/unit/test_web_bridge.py \
  tests/unit/test_build_excel.py tests/integration/test_workbook_reports.py
PYTHONPATH="$PWD/src" .venv/bin/python scripts/build_excel.py --output-dir /tmp/finassert-0016-excel
uv run --with playwright==1.55.0 playwright install chromium
PYTHONPATH="$PWD/src" uv run --with playwright==1.55.0 python \
  scripts/smoke_excel.py /tmp/finassert-0016-excel/taskpane.html
```

Also build with --bundle-pyodide download (or a verified local distribution) and
run smoke_excel.py with --serve. Retain the existing fully offline browser audit.
Run tests/browser/test_excel_freshness.py with FINASSERT_EXCEL_PAGE pointing to
that bundled taskpane.html and Playwright 1.55.0 available. Its three strict
expected failures track issue #23 until E-03; unrelated harness failures must fail.
Network/runtime setup is described in the existing build scripts; secrets and
workbook contents do not belong in logs or committed evidence.

Before promotion, run all CONTRIBUTING.md checks, existing web/add-in smoke flows,
and the [real-host acceptance checklist](acceptance.md). Compare canonical report
results, not environment timestamps or differing input locators. Document failures,
unsupported capabilities and actual Excel build/platform. External review remains
separate from successful local or CI verification.
