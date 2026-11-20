"""Public guide identity, build freshness, HTTP contracts and executable examples."""

from __future__ import annotations

import hashlib
import http.client
import json
import re
import subprocess
import sys
import threading
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import build_user_guide  # noqa: E402
import user_guide  # noqa: E402
from serve_excel import make_server  # noqa: E402


@pytest.fixture
def guide_folder(tmp_path):
    user_guide.copy_assets(tmp_path)
    (tmp_path / "taskpane.html").write_text("pane")
    return tmp_path


@pytest.fixture
def guide_server(guide_folder):
    server = make_server(guide_folder, port=0, quiet=True)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)


def request(server, method, path):
    connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
    try:
        connection.request(method, path)
        response = connection.getresponse()
        return response.status, dict(response.getheaders()), response.read()
    finally:
        connection.close()


def test_prebuilt_guide_matches_current_source_catalog_and_version(guide_folder):
    asset = user_guide.read_asset(guide_folder)
    metadata = asset.metadata
    assert metadata["source_sha256"] == hashlib.sha256(user_guide.SOURCE.read_bytes()).hexdigest()
    assert metadata["catalog_sha256"] == user_guide.catalog_sha256()
    assert metadata["rule_count"] == len(user_guide.catalog_document()["rules"])
    assert metadata["template_count"] == len(user_guide.catalog_document()["templates"])
    source = user_guide.SOURCE.read_text()
    assert build_user_guide.resolved_source(source) == source
    for rule in user_guide.catalog_document()["rules"]:
        assert f"Stable rule ID: `{rule['rule_id']}`" in source
        for parameter in rule["parameters"]:
            assert f"| `{parameter['name']}` |" in source


@pytest.mark.parametrize("path", [user_guide.API_PATH, user_guide.PDF_PATH])
def test_get_head_identity_and_download_headers(guide_server, path):
    status, headers, body = request(guide_server, "GET", path)
    assert status == 200
    assert int(headers["Content-Length"]) == len(body)
    assert headers["Cache-Control"] == "no-store"
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert "Access-Control-Allow-Origin" not in headers
    if path.endswith(".pdf"):
        assert headers["Content-Type"] == "application/pdf"
        assert headers["Content-Disposition"] == 'attachment; filename="finassert-user-guide.pdf"'
        assert body == (user_guide.ASSETS / user_guide.PDF_NAME).read_bytes()
    else:
        assert headers["Content-Type"] == "application/json; charset=utf-8"
        metadata = json.loads(body)
        assert metadata["download_url"] == user_guide.PDF_PATH
        assert (
            metadata["sha256"]
            == hashlib.sha256((user_guide.ASSETS / user_guide.PDF_NAME).read_bytes()).hexdigest()
        )
    head_status, head_headers, head_body = request(guide_server, "HEAD", path)
    assert head_status == status
    assert head_body == b""
    for name in ("Content-Type", "Content-Length", "Cache-Control", "X-Content-Type-Options"):
        assert head_headers[name] == headers[name]
    assert head_headers.get("Content-Disposition") == headers.get("Content-Disposition")


@pytest.mark.parametrize("method", ["GET", "HEAD"])
@pytest.mark.parametrize("path", [user_guide.API_PATH, user_guide.PDF_PATH])
def test_missing_guide_never_succeeds_or_looks_like_a_pdf(guide_server, guide_folder, method, path):
    (guide_folder / user_guide.PDF_NAME).unlink()
    status, headers, body = request(guide_server, method, path)
    assert status == 404
    assert not headers["Content-Type"].startswith("application/pdf")
    if method == "HEAD":
        assert body == b""


@pytest.mark.parametrize("corruption", ["pdf", "signature", "metadata", "size", "hash"])
def test_mismatched_assets_fail_closed(guide_server, guide_folder, corruption):
    pdf_path = guide_folder / user_guide.PDF_NAME
    metadata_path = guide_folder / user_guide.METADATA_NAME
    if corruption == "pdf":
        pdf_path.write_bytes(pdf_path.read_bytes() + b"changed")
    elif corruption == "metadata":
        metadata_path.write_text("{not json")
    else:
        metadata = json.loads(metadata_path.read_text())
        if corruption == "signature":
            pdf_path.write_bytes(b"<html>not a pdf</html>")
            metadata["bytes"] = pdf_path.stat().st_size
            metadata["sha256"] = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
        elif corruption == "size":
            metadata["bytes"] += 1
        else:
            metadata["sha256"] = "0" * 64
        metadata_path.write_text(json.dumps(metadata))
    for path in (user_guide.API_PATH, user_guide.PDF_PATH):
        status, headers, _ = request(guide_server, "GET", path)
        assert status == 503
        assert not headers["Content-Type"].startswith("application/pdf")


def test_guide_is_public_without_enabling_private_reader_and_unknown_routes_are_404(guide_server):
    status, _, _ = request(guide_server, "GET", user_guide.PDF_PATH + "?download=1")
    assert status == 200
    for path in (user_guide.API_PATH + "/../../secret", "/api/finassert/v1/unknown"):
        assert request(guide_server, "GET", path)[0] == 404
    assert request(guide_server, "GET", "/api/quantsmith/v1/docs")[0] == 404
    assert request(guide_server, "GET", "/taskpane.html")[2] == b"pane"


def test_stale_source_is_rejected_before_an_addin_build(tmp_path, monkeypatch):
    source = tmp_path / "guide.md"
    source.write_text(user_guide.SOURCE.read_text() + "\nSource changed.\n")
    monkeypatch.setattr(user_guide, "SOURCE", source)
    with pytest.raises(user_guide.GuideAssetError, match=r"missing or stale.*Rebuild with"):
        user_guide.copy_assets(tmp_path / "build")
    assert not (tmp_path / "build").exists()


def test_stale_catalog_is_rejected_before_an_addin_build(tmp_path, monkeypatch):
    monkeypatch.setattr(user_guide, "catalog_sha256", lambda: "0" * 64)
    with pytest.raises(user_guide.GuideAssetError, match=r"missing or stale.*Rebuild with"):
        user_guide.copy_assets(tmp_path / "build")


def test_guide_reference_requires_an_explicit_update():
    source = user_guide.SOURCE.read_text().replace("Stable rule ID:", "Changed rule ID:", 1)
    with pytest.raises(ValueError, match="reference is stale"):
        build_user_guide.resolved_source(source)
    assert build_user_guide.resolved_source(source, update_reference=True) == (
        user_guide.SOURCE.read_text()
    )


def test_guide_python_examples_execute_and_preserve_input(tmp_path, monkeypatch, guide_server):
    from openpyxl import Workbook

    from finassert.policy import get_template

    monkeypatch.chdir(tmp_path)
    Path("policy.yml").write_text(get_template("long-only-holdings").to_yaml())
    Path("positions.csv").write_text("weight,market_value\n0.4,400\n0.6,600\n")
    book = Workbook()
    book.active.title = "Positions"
    for row, values in enumerate([["weight", "market_value"], [0.4, 400], [0.6, 600]], 7):
        for column, value in enumerate(values, 3):
            book.active.cell(row, column, value)
    book.save("positions.xlsx")
    book.close()
    before = Path("positions.xlsx").read_bytes()
    source = user_guide.SOURCE.read_text()
    blocks = re.findall(r"```python\n(.*?)```", source, re.S)
    assert len(blocks) == 6
    for index, block in enumerate(blocks):
        # The download example uses this real, isolated local server rather than
        # depending on the user's current desktop add-in port/certificate.
        block = block.replace(
            'origin = "https://localhost:3002"',
            f'origin = "http://127.0.0.1:{guide_server.server_port}"',
        )
        exec(compile(block, f"user-guide-example-{index + 1}", "exec"), {})
    assert Path("review.xlsx").is_file()
    assert (
        Path("finassert-user-guide.pdf").read_bytes()
        == (user_guide.ASSETS / user_guide.PDF_NAME).read_bytes()
    )
    assert Path("positions.xlsx").read_bytes() == before


def test_guide_cli_policy_and_report_workflow_executes(tmp_path):
    source = tmp_path / "positions.csv"
    source.write_text("weight,market_value\n0.4,400\n0.6,600\n")
    policy = tmp_path / "policy.yml"
    for arguments in (
        ["rules", "--json"],
        ["templates", "--json"],
        ["init", "--template", "long-only-holdings", "--output", str(policy)],
        ["suggest", "--input", str(source)],
        [
            "check",
            "--config",
            str(policy),
            "--input",
            str(source),
            "--output",
            str(tmp_path / "report.json"),
            "--html",
            str(tmp_path / "report.html"),
            "--xlsx",
            str(tmp_path / "review.xlsx"),
        ],
    ):
        result = subprocess.run(
            [sys.executable, "-m", "finassert", *arguments],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads((tmp_path / "report.json").read_text())["report"]["passed"] is True
