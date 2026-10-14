"""Drive the built browser app in headless Chromium and check it end to end.

The script opens the single-file app, loads ``examples/positions.csv``, opens
``examples/policy.yml``, runs the checks, and verifies that:

* the engine starts under the page's Content-Security-Policy;
* the report shows the expected outcome counts, also for a two-sheet Excel
  workbook once its sheet is chosen;
* the downloaded policy, run through the Python API, gives identical results,
  and the browser ran the opened policy unchanged (same fingerprint as the CLI);
* no network request is made after start-up, and no CSP violation occurs.

Requires Playwright (``uv run --with playwright python scripts/smoke_web.py``).
By default Pyodide is fetched from the CDN, as a user's browser would. Pass
``--pyodide-dir`` to serve a local copy of the Pyodide distribution instead.

Usage::

    python scripts/smoke_web.py dist/web/finassert.html
"""

from __future__ import annotations

import argparse
import csv
import json
import mimetypes
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from finassert.loaders import load_input  # noqa: E402
from finassert.policy import load_policy  # noqa: E402

EXAMPLES = ROOT / "examples"
EXPECTED_BANNER = "✗ Failed: 1 failed, 0 could not run, 1 passed."
_PYODIDE_URL = re.compile(r'src="(https://[^"]+/)pyodide\.js"')


def main(argv: list[str] | None = None) -> int:
    """Run the smoke test and return a process exit code."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("page", type=Path, help="built application HTML")
    parser.add_argument("--pyodide-dir", type=Path, help="serve Pyodide from this directory")
    parser.add_argument("--browser", help="Chromium executable to use")
    parser.add_argument("--timeout", type=float, default=180, help="seconds to wait for start-up")
    arguments = parser.parse_args(argv)

    try:
        from playwright.sync_api import expect, sync_playwright
    except ImportError:
        parser.error("Playwright is required: uv run --with playwright python scripts/smoke_web.py")

    page_text = arguments.page.read_text(encoding="utf-8")
    match = _PYODIDE_URL.search(page_text)
    if match is None:
        parser.error("cannot find the Pyodide URL in the page")
    pyodide_url = match.group(1)

    failures: list[str] = []
    console: list[str] = []
    requests: list[str] = []
    with sync_playwright() as playwright, tempfile.TemporaryDirectory() as scratch:
        launch: dict[str, Any] = {}
        if arguments.browser:
            launch["executable_path"] = arguments.browser
        browser = playwright.chromium.launch(**launch)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        page.on("request", lambda request: requests.append(request.url))
        page.on("console", lambda message: console.append(f"{message.type}: {message.text}"))
        page.on("pageerror", lambda error: console.append(f"pageerror: {error}"))
        if arguments.pyodide_dir:
            _serve_locally(page, pyodide_url, arguments.pyodide_dir)

        page.goto(arguments.page.resolve().as_uri())
        status = page.locator("#status")
        expect(status).to_have_text(
            re.compile(r"^(Ready|The checking engine could not)"),
            timeout=arguments.timeout * 1000,
        )
        if not status.inner_text().startswith("Ready"):
            browser.close()
            print(f"FAIL: engine did not start: {status.inner_text()}")
            print("\n".join(console))
            return 1
        startup_requests = len(requests)
        print(f"engine ready after {startup_requests} request(s)")

        page.set_input_files("#data-file", str(EXAMPLES / "positions.csv"))
        expect(page.locator("#data-name")).to_contain_text("5 row(s), 4 column(s)")
        page.set_input_files("#policy-file", str(EXAMPLES / "policy.yml"))
        expect(page.locator(".check")).to_have_count(2)
        page.click("#run")
        expect(page.locator("#results")).to_be_visible()
        banner = page.locator("#result-banner").inner_text()
        print(f"result: {banner}")
        if banner != EXPECTED_BANNER:
            failures.append(f"unexpected result banner {banner!r}")

        report = page.frame_locator("#report-frame")
        expect(report.locator("h1")).to_have_text("Daily positions")
        expect(report.locator(".card.failed")).to_have_count(1)

        policy_path = Path(scratch) / "policy.yml"
        artifact_path = Path(scratch) / "report.json"
        with page.expect_download() as download:
            page.click("#download-policy")
        download.value.save_as(policy_path)
        with page.expect_download() as download:
            page.click("#download-json")
        download.value.save_as(artifact_path)

        _check_workbook(page, Path(scratch), failures)

        page.select_option("#template", "long-only-holdings")
        expect(page.locator(".check")).to_have_count(3)
        expect(page.locator("#template-notes")).to_contain_text("Before relying on this template")

        _check_cash_reconciliation(page, Path(scratch), failures)
        _check_multi_portfolio(page, failures)
        _check_limits_policy(page, failures)
        _check_suggestions(page, Path(scratch), failures)
        _check_warning_severity(page, Path(scratch), failures)

        page.wait_for_timeout(500)
        browser.close()

        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        exported = load_policy(policy_path)
        rerun = exported.check(load_input(EXAMPLES / "positions.csv"))
        if rerun.to_dict() != artifact["report"]:
            failures.append("exported policy gives different results from the browser run")
        if exported.digest != artifact["policy"]["digest"]:
            failures.append("exported policy digest differs from the browser run")
        if load_policy(EXAMPLES / "policy.yml").digest != artifact["policy"]["digest"]:
            failures.append("the browser ran a different policy from the file it opened")

    late = [url for url in requests[startup_requests:] if not _is_local(url)]
    if late:
        failures.append(f"network requests after start-up: {late}")
    violations = [
        line for line in console if "Content Security Policy" in line or "pageerror" in line
    ]
    if violations:
        failures.append(f"console errors: {violations}")

    for failure in failures:
        print(f"FAIL: {failure}")
    if not failures:
        print("PASS: browser app smoke test")
    return 1 if failures else 0


def _check_workbook(page: Any, scratch: Path, failures: list[str]) -> None:
    """Open a two-sheet Excel workbook, pick the sheet, and run the checks."""
    from openpyxl import Workbook
    from playwright.sync_api import expect

    book = Workbook()
    book.active.title = "Notes"
    book.active.append(["Prepared by the operations team"])
    sheet = book.create_sheet("Positions")
    for row in (EXAMPLES / "positions.csv").read_text(encoding="utf-8").splitlines():
        cells = next(csv.reader([row]))
        sheet.append([_cell(value) for value in cells])
    path = scratch / "positions.xlsx"
    book.save(path)

    page.set_input_files("#data-file", str(path))
    expect(page.locator("#sheet-picker")).to_be_visible()
    page.select_option("#sheet-select", "Positions")
    expect(page.locator("#data-name")).to_contain_text('sheet "Positions": 5 row(s)')
    page.click("#run")
    banner = page.locator("#result-banner").inner_text()
    print(f"workbook result: {banner}")
    if banner != EXPECTED_BANNER:
        failures.append(f"unexpected workbook result {banner!r}")


def _check_cash_reconciliation(page: Any, scratch: Path, failures: list[str]) -> None:
    """Start from the cash template on a daily cash file with one break."""
    from playwright.sync_api import expect

    path = scratch / "cash.csv"
    path.write_text(
        "portfolio,date,currency,opening_balance,inflows,outflows,cash_income,closing_balance\n"
        "A,2026-01-02,USD,100.00,25.00,10.00,0.05,115.05\n"
        "A,2026-01-02,EUR,50.00,0,5.00,0,45.02\n",
        encoding="utf-8",
    )
    page.set_input_files("#data-file", str(path))
    expect(page.locator("#data-name")).to_contain_text("2 row(s), 8 column(s)")
    page.select_option("#template", "cash-reconciliation")
    expect(page.locator(".check")).to_have_count(1)
    expect(page.locator("fieldset.columns input:checked")).to_have_count(2)
    expect(page.locator("fieldset.columns legend").first).to_be_visible()
    page.click("#run")
    banner = page.locator("#result-banner").inner_text()
    print(f"cash result: {banner}")
    if banner != "✗ Failed: 1 failed, 0 could not run, 0 passed.":
        failures.append(f"unexpected cash reconciliation result {banner!r}")
    report = page.frame_locator("#report-frame")
    expect(report.locator(".card.failed")).to_contain_text("EUR")
    command = page.locator("#cli-command").text_content() or ""
    if not command.startswith('finassert check --config policy.yml --input "cash.csv"'):
        failures.append(f"unexpected command hint {command!r}")
    expect(page.locator("#cli-note")).to_be_hidden()


def _check_multi_portfolio(page: Any, failures: list[str]) -> None:
    """Run the multi-portfolio template on examples/holdings.csv: one break."""
    from playwright.sync_api import expect

    page.set_input_files("#data-file", str(EXAMPLES / "holdings.csv"))
    expect(page.locator("#data-name")).to_contain_text("4 row(s), 5 column(s)")
    page.select_option("#template", "multi-portfolio-holdings")
    expect(page.locator(".check")).to_have_count(4)
    page.click("#run")
    banner = page.locator("#result-banner").inner_text()
    print(f"holdings result: {banner}")
    if banner != "✗ Failed: 1 failed, 0 could not run, 3 passed.":
        failures.append(f"unexpected multi-portfolio result {banner!r}")
    report = page.frame_locator("#report-frame")
    expect(report.locator(".card.failed")).to_contain_text("Beta")


def _check_limits_policy(page: Any, failures: list[str]) -> None:
    """Open the exposure-limits policy and run it on the holdings file: one breach."""
    from playwright.sync_api import expect

    page.set_input_files("#policy-file", str(EXAMPLES / "limits-policy.yml"))
    expect(page.locator(".check")).to_have_count(3)
    page.click("#run")
    banner = page.locator("#result-banner").inner_text()
    print(f"limits result: {banner}")
    if banner != "✗ Failed: 1 failed, 0 could not run, 2 passed.":
        failures.append(f"unexpected limits result {banner!r}")
    report = page.frame_locator("#report-frame")
    expect(report.locator(".card.failed")).to_contain_text("JNJ")

    # Build the same position limit by hand: a typed limit is a plain-number field.
    while page.locator(".check").count():
        page.locator(".check button.link").first.click()
    page.select_option("#add-check", "position_within_limit")
    page.click("#add-check-button")
    check = page.locator(".check")
    expect(check).to_have_count(1)
    check.get_by_label("Value column (required)").select_option("market_value")
    check.get_by_label("Base column (for example NAV)").select_option("nav")
    check.get_by_label("Largest allowed position (required)").fill("0.6")
    check.locator("fieldset.columns").first.get_by_label("portfolio").check()
    page.click("#run")
    banner = page.locator("#result-banner").inner_text()
    print(f"hand-built limit result: {banner}")
    if banner != "✗ Failed: 1 failed, 0 could not run, 0 passed.":
        failures.append(f"unexpected hand-built limit result {banner!r}")


def _check_suggestions(page: Any, scratch: Path, failures: list[str]) -> None:
    """Open a file with unfamiliar headers and let the app match a template to them."""
    from playwright.sync_api import expect

    path = scratch / "odd.csv"
    path.write_text(
        "Fund,Security,Wt,MV (Base),NAV\nA,X,0.5,10,20\nA,Y,0.5,10,20\n",
        encoding="utf-8",
    )
    page.set_input_files("#data-file", str(path))
    expect(page.locator("#data-name")).to_contain_text("2 row(s), 5 column(s)")
    suggestions = page.locator("#suggestions")
    expect(suggestions).to_be_visible()
    expect(suggestions.locator("button").first).to_contain_text("5 of 5 columns matched")
    suggestions.locator("button").first.click()
    expect(page.locator(".check")).to_have_count(4)
    expect(page.locator("#template-notes")).to_contain_text("Confirm the columns finassert matched")
    page.click("#run")
    banner = page.locator("#result-banner").inner_text()
    print(f"matched-columns result: {banner}")
    if not banner.startswith("✓ Passed"):
        failures.append(f"unexpected matched-columns result {banner!r}")


def _check_warning_severity(page: Any, scratch: Path, failures: list[str]) -> None:
    """A failed check set to 'warning' is reported but does not fail the run."""
    from playwright.sync_api import expect

    policy = scratch / "warn.yml"
    policy.write_text(
        (EXAMPLES / "policy.yml")
        .read_text(encoding="utf-8")
        .replace("  - rule: non_negative\n", "  - rule: non_negative\n    severity: warning\n"),
        encoding="utf-8",
    )
    page.set_input_files("#data-file", str(EXAMPLES / "positions.csv"))
    expect(page.locator("#data-name")).to_contain_text("5 row(s), 4 column(s)")
    page.set_input_files("#policy-file", str(policy))
    expect(page.locator(".check")).to_have_count(2)
    page.click("#run")
    banner = page.locator("#result-banner").inner_text()
    print(f"warning result: {banner}")
    if banner != "✓ Passed with 1 warning(s): 1 passed, 0 skipped.":
        failures.append(f"unexpected warning result {banner!r}")
    expect(page.frame_locator("#report-frame").locator(".card.warning")).to_have_count(1)


def _cell(value: str) -> Any:
    try:
        return float(value) if "." in value else int(value)
    except ValueError:
        return value


def _serve_locally(page: Any, base_url: str, directory: Path) -> None:
    def handle(route: Any) -> None:
        name = route.request.url[len(base_url) :].split("?")[0]
        path = directory / name
        if not path.is_file():
            route.abort()
            return
        content_type = "application/wasm" if name.endswith(".wasm") else None
        route.fulfill(
            path=str(path),
            content_type=content_type
            or mimetypes.guess_type(name)[0]
            or "application/octet-stream",
            headers={"Access-Control-Allow-Origin": "*"},
        )

    page.route(base_url + "**", handle)


def _is_local(url: str) -> bool:
    return url.startswith(("file:", "blob:", "about:", "data:"))


if __name__ == "__main__":
    sys.exit(main())
