"""Download the current PDF through the visible pane's same-origin API link."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get("FINASSERT_EXCEL_PAGE"), reason="requires the bundled Excel browser job"
)


def test_user_guide_download_matches_metadata_and_does_not_read_workbook(pane):
    from playwright.sync_api import expect

    link = pane.get_by_role("link", name="Download user guide (PDF)")
    expect(link).to_be_visible()
    reads = pane.evaluate("window.__excel.reads.length")
    source = pane.evaluate("JSON.stringify(window.__excel.sheets.Holdings.cells)")
    response = pane.request.get(pane.url.rsplit("/", 1)[0] + "/api/finassert/v1/user-guide")
    assert response.status == 200
    metadata = json.loads(response.body())
    with pane.expect_download() as downloaded:
        link.click()
    download = downloaded.value
    assert download.suggested_filename == "finassert-user-guide.pdf"
    pdf = Path(download.path()).read_bytes()
    assert pdf.startswith(b"%PDF-")
    assert len(pdf) == metadata["bytes"]
    assert hashlib.sha256(pdf).hexdigest() == metadata["sha256"]
    assert pane.evaluate("window.__excel.reads.length") == reads
    assert pane.evaluate("JSON.stringify(window.__excel.sheets.Holdings.cells)") == source
