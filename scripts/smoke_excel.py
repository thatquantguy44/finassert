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
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from smoke_web import _serve_locally

OFFICE_JS = "https://appsforoffice.microsoft.com/lib/1/hosted/office.js"
_PYODIDE_URL = re.compile(r'src="(https://[^"]+/)pyodide\.js"')

SHEET = {
    "name": "Holdings",
    "rowIndex": 2,  # the selection starts on sheet row 3
    "values": [
        ["portfolio", "ticker", "weight", "market_value", "nav"],
        ["Alpha", "AAPL", 0.6, 600000, 1000000],
        ["Alpha", "MSFT", 0.4, 400000, 1000000],
        ["Beta", "JNJ", 0.5, "#N/A", 1000000],
        ["Beta", "XOM", 0.3, 375000, 1000000],
    ],
}

STUB = (Path(__file__).resolve().parent / "excel_stub.js").read_text(encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    """Run the smoke test and return a process exit code."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("page", type=Path, help="built task pane HTML")
    parser.add_argument("--pyodide-dir", type=Path, help="serve Pyodide from this directory")
    parser.add_argument("--browser", help="Chromium executable to use")
    parser.add_argument("--timeout", type=float, default=180)
    arguments = parser.parse_args(argv)

    from playwright.sync_api import expect, sync_playwright

    page_text = arguments.page.read_text(encoding="utf-8")
    match = _PYODIDE_URL.search(page_text)
    if match is None:
        parser.error("cannot find the Pyodide URL in the page")
    failures: list[str] = []
    console: list[str] = []
    with sync_playwright() as playwright:
        launch: dict[str, Any] = {}
        if arguments.browser:
            launch["executable_path"] = arguments.browser
        browser = playwright.chromium.launch(**launch)
        for selected in ("range", "single"):
            context = browser.new_context()
            page = context.new_page()
            page.on("console", lambda message: console.append(f"{message.type}: {message.text}"))
            page.on("pageerror", lambda error: console.append(f"pageerror: {error}"))
            stub = STUB.replace("__SHEET__", json.dumps(SHEET)).replace("__SELECTED__", selected)
            page.route(OFFICE_JS, _office_stub(stub))
            if arguments.pyodide_dir:
                _serve_locally(page, match.group(1), arguments.pyodide_dir)
            page.goto(arguments.page.resolve().as_uri())
            expect(page.locator("#status")).to_have_text(
                re.compile(r"^(Ready|The checking engine could not)"),
                timeout=arguments.timeout * 1000,
            )
            if not page.locator("#status").inner_text().startswith("Ready"):
                print(f"FAIL: engine did not start: {page.locator('#status').inner_text()}")
                return 1
            failures += _exercise(page, selected, expect)
            context.close()
        browser.close()

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


def _exercise(page: Any, selected: str, expect: Any) -> list[str]:
    failures: list[str] = []
    expect(page.locator("#excel-panel")).to_be_visible()
    if page.evaluate("document.getElementById('excel-write').hidden"):
        failures.append(f"{selected}: the write button was not enabled")
    page.click("#excel-read")
    expect(page.locator("#data-name")).to_contain_text("Holdings!A3:E7: 4 row(s), 5 column(s)")
    expect(page.locator("#data-notes")).to_contain_text("1 cell(s) show Excel errors")
    expect(page.locator("#data-notes")).to_contain_text("#N/A in column 'market_value', row 6")
    expect(page.locator("#suggestions button").first).to_contain_text("5 of 5 columns matched")

    page.select_option("#template", "multi-portfolio-holdings")
    expect(page.locator(".check")).to_have_count(4)
    page.click("#run")
    banner = page.locator("#result-banner").inner_text()
    print(f"{selected} result: {banner}")
    if not banner.startswith("✗ Failed"):
        failures.append(f"{selected}: unexpected banner {banner!r}")
    expect(page.locator("#cli-note")).to_contain_text("Save the workbook")

    page.click("#excel-write")
    expect(page.locator("#status")).to_contain_text("Your data was not changed")
    written = page.evaluate("window.__excel.written")
    name = page.evaluate("window.__excel.sheetName")
    if name != "finassert results":
        failures.append(f"{selected}: results went to sheet {name!r}")
    if not written or written[0] != ["Check", "Result", "Severity", "Row", "Details"]:
        failures.append(f"{selected}: unexpected results header {written and written[0]!r}")
    elif 6 not in [row[3] for row in written]:
        failures.append(f"{selected}: no row refers to sheet row 6")
    return failures


if __name__ == "__main__":
    sys.exit(main())
