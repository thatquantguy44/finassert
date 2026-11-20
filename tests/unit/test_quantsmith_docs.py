"""Pinned local QuantSmith reference and same-origin API."""

from __future__ import annotations

import base64
import hashlib
import http.client
import json
import subprocess
import sys
import threading
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from quantsmith_docs import Catalog, GitHubCatalog  # noqa: E402
from serve_excel import make_server  # noqa: E402


def git(checkout: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(checkout), *args], text=True).strip()


@pytest.fixture
def pinned_checkout(tmp_path: Path) -> tuple[Path, Path, str]:
    checkout = tmp_path / "QuantSmith"
    checkout.mkdir()
    git(checkout, "init", "-q")
    git(checkout, "config", "user.name", "Fixture")
    git(checkout, "config", "user.email", "fixture@example.test")
    git(checkout, "remote", "add", "origin", "https://github.com/thatquantguy44/QuantSmith.git")
    (checkout / "agents" / "risk").mkdir(parents=True)
    (checkout / "docs").mkdir()
    (checkout / "agents" / "risk" / "prompt.md").write_text("# Risk\nRead only.")
    (checkout / "docs" / "guide.md").write_text("# Guide\nUseful.")
    (checkout / "secret.txt").write_text("private fixture")
    (checkout / "agents" / "risk" / "link.md").symlink_to(checkout / "secret.txt")
    git(checkout, "add", ".")
    git(checkout, "commit", "-qm", "fixture")
    commit = git(checkout, "rev-parse", "HEAD")
    lock = tmp_path / "lock.json"
    lock.write_text(
        json.dumps(
            {
                "version": 1,
                "repository": "thatquantguy44/QuantSmith",
                "commit": commit,
                "include": ["agents/**/prompt.md", "agents/**/link.md", "docs/*.md"],
            }
        )
    )
    return checkout, lock, commit


def test_catalog_reads_only_pinned_allowlisted_blobs(
    pinned_checkout: tuple[Path, Path, str],
) -> None:
    checkout, lock, commit = pinned_checkout
    catalog = Catalog(checkout, lock)
    listed = catalog.listing()
    assert listed["commit"] == commit
    assert [item["path"] for item in listed["documents"]] == [
        "agents/risk/prompt.md",
        "docs/guide.md",
    ]
    identifier = hashlib.sha256(b"agents/risk/prompt.md").hexdigest()
    assert catalog.read(identifier)["content"] == "# Risk\nRead only."
    assert catalog.read("../../secret.txt") is None
    (checkout / "agents" / "risk" / "prompt.md").write_text("Changed working tree")
    assert catalog.read(identifier)["content"] == "# Risk\nRead only."


def test_checkout_identity_and_revision_are_required(
    pinned_checkout: tuple[Path, Path, str],
) -> None:
    checkout, lock, _ = pinned_checkout
    git(checkout, "remote", "set-url", "origin", "https://github.com/other/repo.git")
    with pytest.raises(ValueError, match="origin"):
        Catalog(checkout, lock)
    git(checkout, "remote", "set-url", "origin", "https://github.com/thatquantguy44/QuantSmith.git")
    payload = json.loads(lock.read_text())
    payload["commit"] = "0" * 40
    lock.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="checkout"):
        Catalog(checkout, lock)


def test_github_catalog_reads_only_the_pinned_allowlisted_blobs(
    pinned_checkout: tuple[Path, Path, str],
) -> None:
    _, lock, _ = pinned_checkout
    content = b"# Remote guide\nRead only."
    blob = hashlib.sha1(f"blob {len(content)}\0".encode() + content).hexdigest()
    requested: list[str] = []

    class Response:
        def __init__(self, payload: dict[str, object]) -> None:
            self.payload = json.dumps(payload).encode()

        def __enter__(self) -> Response:
            return self

        def __exit__(self, *_: object) -> None:
            return None

        def read(self, _: int) -> bytes:
            return self.payload

    def opener(request: object, *, timeout: int) -> Response:
        assert timeout == 10
        full_url = request.full_url  # type: ignore[attr-defined]
        requested.append(full_url)
        assert request.get_header("Authorization") == "Bearer fixture-token"  # type: ignore[attr-defined]
        if "/trees/" in full_url:
            return Response(
                {
                    "truncated": False,
                    "tree": [
                        {
                            "path": "docs/guide.md",
                            "mode": "100644",
                            "type": "blob",
                            "sha": blob,
                            "size": len(content),
                        },
                        {
                            "path": "secret.txt",
                            "mode": "100644",
                            "type": "blob",
                            "sha": "0" * 40,
                            "size": 7,
                        },
                        {
                            "path": "docs/link.md",
                            "mode": "120000",
                            "type": "blob",
                            "sha": blob,
                            "size": len(content),
                        },
                    ],
                }
            )
        assert full_url.endswith("/git/blobs/" + blob)
        return Response({"encoding": "base64", "content": base64.b64encode(content).decode()})

    catalog = GitHubCatalog(lock, "fixture-token", opener=opener)
    listing = catalog.listing()
    assert listing["source"] == "github"
    assert [item["path"] for item in listing["documents"]] == ["docs/guide.md"]
    identifier = hashlib.sha256(b"docs/guide.md").hexdigest()
    assert catalog.read(identifier)["content"] == content.decode()
    assert len(requested) == 2


def test_local_api_is_opt_in_and_rejects_cross_origin(
    pinned_checkout: tuple[Path, Path, str], tmp_path: Path
) -> None:
    checkout, lock, commit = pinned_checkout
    root = tmp_path / "static"
    root.mkdir()
    (root / "taskpane.html").write_text("static pane")
    server = make_server(
        root,
        port=0,
        quiet=True,
        quantsmith_source="local",
        quantsmith_checkout=checkout,
        quantsmith_lock=lock,
    )
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        connection = http.client.HTTPConnection("127.0.0.1", server.server_port)
        connection.request("GET", "/api/quantsmith/v1/docs")
        response = connection.getresponse()
        listing = json.loads(response.read())
        assert response.status == 200
        assert response.getheader("Access-Control-Allow-Origin") is None
        assert listing["commit"] == commit
        identifier = listing["documents"][0]["id"]
        connection.request("GET", f"/api/quantsmith/v1/docs/{identifier}")
        response = connection.getresponse()
        assert json.loads(response.read())["content"] == "# Risk\nRead only."
        connection.request(
            "GET", "/api/quantsmith/v1/docs", headers={"Origin": "https://other.example"}
        )
        response = connection.getresponse()
        response.read()
        assert response.status == 403
        connection.request("GET", "/api/quantsmith/v1/docs", headers={"Host": "other.example"})
        response = connection.getresponse()
        response.read()
        assert response.status == 403
        connection.request("GET", "/api/quantsmith/v1/docs/not-an-id")
        response = connection.getresponse()
        response.read()
        assert response.status == 404
        connection.request("GET", "/taskpane.html")
        response = connection.getresponse()
        assert response.read() == b"static pane"
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)
    with pytest.raises(ValueError, match="local-only"):
        make_server(
            root,
            host="0.0.0.0",
            port=0,
            quantsmith_source="local",
            quantsmith_checkout=checkout,
            quantsmith_lock=lock,
        )
    disabled = make_server(root, port=0, quiet=True)
    disabled_worker = threading.Thread(target=disabled.serve_forever, daemon=True)
    disabled_worker.start()
    try:
        connection = http.client.HTTPConnection("127.0.0.1", disabled.server_port)
        connection.request("GET", "/api/quantsmith/v1/docs")
        response = connection.getresponse()
        response.read()
        assert response.status == 404
    finally:
        disabled.shutdown()
        disabled.server_close()
        disabled_worker.join(timeout=5)
    unavailable = make_server(
        root,
        port=0,
        quiet=True,
        quantsmith_source="local",
        quantsmith_checkout=tmp_path / "missing",
        quantsmith_lock=lock,
    )
    unavailable_worker = threading.Thread(target=unavailable.serve_forever, daemon=True)
    unavailable_worker.start()
    try:
        connection = http.client.HTTPConnection("127.0.0.1", unavailable.server_port)
        connection.request("GET", "/api/quantsmith/v1/docs")
        response = connection.getresponse()
        response.read()
        assert response.status == 503
    finally:
        unavailable.shutdown()
        unavailable.server_close()
        unavailable_worker.join(timeout=5)
