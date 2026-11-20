"""The optional QuantSmith reader displays only fetched reference text."""

from __future__ import annotations

import hashlib
import json
import os

import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get("FINASSERT_EXCEL_PAGE"), reason="requires the bundled Excel browser job"
)


@pytest.mark.parametrize("pane", [{"startUnbound": True}], indirect=True)
def test_reader_loads_on_request_and_renders_document_as_text(pane) -> None:
    from playwright.sync_api import expect

    path = "agents/risk/prompt.md"
    identifier = hashlib.sha256(path.encode()).hexdigest()
    commit = "a" * 40
    calls: list[str] = []

    def serve(route):
        calls.append(route.request.url)
        if route.request.url.endswith("/docs"):
            body = {
                "repository": "thatquantguy44/QuantSmith",
                "commit": commit,
                "source": "local",
                "documents": [{"id": identifier, "path": path, "title": "prompt.md", "bytes": 28}],
            }
        else:
            body = {
                "id": identifier,
                "path": path,
                "commit": commit,
                "sha256": "b" * 64,
                "content": "# Risk\n<img src=x onerror=alert(1)>",
            }
        route.fulfill(body=json.dumps(body), content_type="application/json")

    pane.route("**/api/quantsmith/v1/**", serve)
    assert calls == []
    pane.click("#quantsmith-reference summary")
    pane.click("#quantsmith-load")
    expect(pane.locator("#quantsmith-status")).to_contain_text("1 document(s) match")
    expect(pane.locator("#quantsmith-status")).to_contain_text("Source: local checkout")
    pane.fill("#quantsmith-search", "risk")
    expect(pane.locator("#quantsmith-list button")).to_have_count(1)
    pane.click("#quantsmith-list button")
    expect(pane.locator("#quantsmith-content")).to_contain_text("<img src=x onerror=alert(1)>")
    assert pane.locator("#quantsmith-content img").count() == 0
    assert len(calls) == 2
