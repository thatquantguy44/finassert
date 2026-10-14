"""Drive the Excel task pane in headless Chromium against a stand-in for Excel.

Office.js is replaced by a small stub that serves a fixed sheet and records what the
add-in writes, so this checks everything on the finassert side: reading the selected
cells (or the used range for a single cell), row numbers that match the sheet, notes
about Excel errors, running checks, and writing a results sheet without changing the
data. It cannot show how real Excel behaves: that needs the spike in
``docs/design/excel-integration.md``.

Requires Playwright. Pass ``--pyodide-dir`` to serve a local Pyodide distribution.

Usage::

    python scripts/smoke_excel.py dist/excel/taskpane.html [--pyodide-dir DIR]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import threading
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from smoke_web import _serve_locally

OFFICE_JS = "https://appsforoffice.microsoft.com/lib/1/hosted/office.js"
_PYODIDE_URL = re.compile(r'src="(https://[^"]+/)pyodide\.js"')

VALUES = [
    ["portfolio", "ticker", "weight", "market_value", "nav"],
    ["Alpha", "AAPL", 0.6, 600000, 1000000],
    ["Alpha", "MSFT", 0.4, 400000, 1000000],
    ["Beta", "JNJ", 0.5, "#N/A", 1000000],
    ["Beta", "XOM", 0.3, 375000, 1000000],
]
# (name, what is selected, whether the data is a named table, what the add-in should say)
SCENARIOS = [
    ("selection", "range", True, "the selected cells"),
    ("single cell in a table", "single", True, 'the table "HoldingsTable"'),
    ("single cell, no table", "single", False, "everything on the sheet"),
]

STUB = (Path(__file__).resolve().parent / "excel_stub.js").read_text(encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    """Run the smoke test and return a process exit code."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("page", type=Path, help="built task pane HTML")
    parser.add_argument("--pyodide-dir", type=Path, help="serve Pyodide from this directory")
    parser.add_argument(
        "--serve",
        action="store_true",
        help="serve the page's folder over HTTP and open it there (for a bundled, offline build)",
    )
    parser.add_argument("--browser", help="Chromium executable to use")
    parser.add_argument("--timeout", type=float, default=180)
    arguments = parser.parse_args(argv)

    from playwright.sync_api import expect, sync_playwright

    page_text = arguments.page.read_text(encoding="utf-8")
    match = _PYODIDE_URL.search(page_text)
    if match is None and not arguments.serve:
        parser.error("cannot find the Pyodide URL in the page")
    server = None
    address = arguments.page.resolve().as_uri()
    if arguments.serve:
        from serve_excel import make_server

        server = make_server(arguments.page.resolve().parent, port=0, quiet=True)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        address = f"http://127.0.0.1:{server.server_address[1]}/{arguments.page.name}"
    failures: list[str] = []
    console: list[str] = []
    with sync_playwright() as playwright:
        launch: dict[str, Any] = {}
        if arguments.browser:
            launch["executable_path"] = arguments.browser
        browser = playwright.chromium.launch(**launch)
        for label, selected, table, what in SCENARIOS:
            context = browser.new_context()
            page = context.new_page()
            page.on("console", lambda message: console.append(f"{message.type}: {message.text}"))
            page.on("pageerror", lambda error: console.append(f"pageerror: {error}"))
            config = {"values": VALUES, "selected": selected, "table": table}
            stub = STUB.replace("__CONFIG__", json.dumps(config))
            page.route(OFFICE_JS, _office_stub(stub))
            if arguments.pyodide_dir and match is not None:
                _serve_locally(page, match.group(1), arguments.pyodide_dir)
            page.goto(address)
            expect(page.locator("#status")).to_have_text(
                re.compile(r"^(Ready|The checking engine could not)"),
                timeout=arguments.timeout * 1000,
            )
            if not page.locator("#status").inner_text().startswith("Ready"):
                print(f"FAIL: engine did not start: {page.locator('#status').inner_text()}")
                return 1
            failures += _exercise(page, label, what, expect)
            context.close()
        browser.close()
    if server is not None:
        server.shutdown()

    violations = [
        line for line in console if "Content Security Policy" in line or "pageerror" in line
    ]
    if violations:
        failures.append(f"console errors: {violations}")
    for failure in failures:
        print(f"FAIL: {failure}")
    if not failures:
        print("PASS: Excel task pane smoke test")
    return 1 if failures else 0


def _office_stub(stub: str) -> Any:
    def handle(route: Any) -> None:
        route.fulfill(body=stub, content_type="application/javascript")

    return handle


def _exercise(page: Any, label: str, what: str, expect: Any) -> list[str]:
    failures: list[str] = []
    expect(page.locator("#excel-panel")).to_be_visible()
    for control in ("excel-write", "excel-save-policy", "excel-load-policy"):
        if page.evaluate(f"document.getElementById('{control}').hidden"):
            failures.append(f"{label}: {control} was not enabled")
    before = page.evaluate("JSON.stringify(window.__excel.sheets.Holdings.cells)")
    page.click("#excel-read")
    expect(page.locator("#status")).to_contain_text(f"Read {what} (Holdings!A3:E7)")
    expect(page.locator("#data-name")).to_contain_text("Holdings!A3:E7: 4 row(s), 5 column(s)")
    expect(page.locator("#data-notes")).to_contain_text("1 cell(s) show Excel errors")
    expect(page.locator("#data-notes")).to_contain_text("#N/A in column 'market_value', row 6")
    expect(page.locator("#suggestions button").first).to_contain_text("5 of 5 columns matched")

    page.select_option("#template", "multi-portfolio-holdings")
    expect(page.locator(".check")).to_have_count(4)
    page.click("#run")
    banner = page.locator("#result-banner").inner_text()
    print(f"{label}: {banner}")
    if not banner.startswith("✗ Failed"):
        failures.append(f"{label}: unexpected banner {banner!r}")
    expect(page.locator("#cli-note")).to_contain_text("Save the workbook")

    page.click("#excel-write")
    expect(page.locator("#status")).to_contain_text("Your data was not changed")
    sheet = page.evaluate("window.__excel.sheets['finassert results']")
    cells = sheet["cells"] if sheet else []
    if not cells or cells[0][0] != "finassert results":
        failures.append(f"{label}: no results sheet with a stamp ({cells[:1]})")
    else:
        stamp = {row[0]: row[1] for row in cells[:9] if len(row) > 1}
        if stamp.get("Outcome") != "Failed" or stamp.get("Checked") != "Holdings!A3:E7":
            failures.append(f"{label}: unexpected stamp {stamp}")
        if not str(stamp.get("Policy fingerprint", "")).startswith("sha256:"):
            failures.append(f"{label}: the stamp has no policy fingerprint")
        header = next((i for i, row in enumerate(cells) if row[0] == "Check"), None)
        if header is None or 6 not in [row[3] for row in cells[header:]]:
            failures.append(f"{label}: the results do not refer to sheet row 6")
        if sheet["bold"][:2] != [0, header]:
            failures.append(f"{label}: unexpected bold rows {sheet['bold']}")

    page.click("#excel-save-policy")
    expect(page.locator("#status")).to_contain_text("Saved the checks")
    saved = page.evaluate("window.__excel.sheets['finassert policy']")
    lines = [row[0] for row in saved["cells"]] if saved else []
    if lines[:1] != ["finassert policy"] or "version: 1" not in lines:
        failures.append(f"{label}: unexpected policy sheet {lines[:4]}")
    while page.locator(".check").count():
        page.locator(".check button.link").first.click()
    page.click("#excel-load-policy")
    expect(page.locator("#status")).to_contain_text("Opened the checks saved in this workbook")
    expect(page.locator(".check")).to_have_count(4)

    if page.evaluate("JSON.stringify(window.__excel.sheets.Holdings.cells)") != before:
        failures.append(f"{label}: the add-in changed the data")
    return failures


if __name__ == "__main__":
    sys.exit(main())
