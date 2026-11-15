"""Shared pane/engine fixtures; all non-loopback network access is blocked."""

from __future__ import annotations

import json
import os
import re
import sys
import threading
from pathlib import Path
from urllib.parse import urlsplit

import pytest

ROOT = Path(__file__).resolve().parents[2]
PAGE = os.environ.get("FINASSERT_EXCEL_PAGE")
pytestmark = pytest.mark.skipif(
    not PAGE, reason="run explicitly with the bundled Excel browser job"
)

VALUES = [
    ["portfolio", "ticker", "weight", "market_value", "nav"],
    ["Alpha", "AAA", 0.4, 400, 1000],
    ["Alpha", "BBB", 0.6, 600, 1000],
]
ISSUE = "https://github.com/thatquantguy44/finassert/issues/23"


@pytest.fixture(scope="module")
def served_page():
    """Serve the supplied bundle on loopback, without fetching any runtime files."""
    if not PAGE:
        pytest.skip("FINASSERT_EXCEL_PAGE is required")
    path = Path(PAGE).resolve()
    if not path.is_file() or not (path.parent / "pyodide" / "pyodide.js").is_file():
        raise RuntimeError("FINASSERT_EXCEL_PAGE must name a built bundled-runtime add-in")
    sys.path.insert(0, str(ROOT / "scripts"))
    from serve_excel import make_server

    server = make_server(path.parent, port=0, quiet=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}/{path.name}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.fixture
def pane(served_page, request):
    from playwright.sync_api import expect, sync_playwright

    config = {"values": VALUES, "selected": "range", "table": True, **getattr(request, "param", {})}
    stub = (
        (ROOT / "scripts" / "excel_stub.js").read_text().replace("__CONFIG__", json.dumps(config))
    )
    origin = urlsplit(served_page).netloc
    unexpected = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context()
        page = context.new_page()

        def route(request_route):
            url = request_route.request.url
            if url == "https://appsforoffice.microsoft.com/lib/1/hosted/office.js":
                request_route.fulfill(body=stub, content_type="application/javascript")
            elif urlsplit(url).netloc == origin:
                request_route.continue_()
            else:
                unexpected.append(url)
                request_route.abort()

        page.route("**/*", route)
        page.goto(served_page)
        expect(page.locator("#status")).to_have_text(re.compile(r"^Ready\."), timeout=120000)
        if not config.get("startUnbound"):
            page.select_option("#excel-date-system", "1900")
            page.click("#excel-read")
            expect(page.locator("#excel-freshness")).to_have_attribute("data-state", "Ready")
            page.select_option("#template", "long-only-holdings")
            page.click("#run")
            expect(page.locator("#result-banner")).to_contain_text("✓ Passed")
        try:
            yield page
        finally:
            browser.close()
    if unexpected:
        raise RuntimeError(f"bundled regression attempted unexpected network access: {unexpected}")
