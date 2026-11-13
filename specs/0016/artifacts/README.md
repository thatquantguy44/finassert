# 0016 E-01 baseline evidence

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
