import base64
import hashlib
import http.client
import importlib.util
import json
import shutil
import ssl
import subprocess
import sys
import threading
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load(name: str) -> ModuleType:
    if name in sys.modules and getattr(sys.modules[name], "__file__", "").startswith(str(ROOT)):
        return sys.modules[name]
    sys.path.insert(0, str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# Bundling Pyodide ----------------------------------------------------------------------


def fake_distribution(
    folder: Path, *, version: str = "0.27.7", loader: bytes | None = None
) -> None:
    bundle = load("bundle_pyodide")
    build_web = load("build_web")
    wheels = {"pyyaml-6.0-py3-none-any.whl": b"yaml wheel", "extra-1.0-py3-none-any.whl": b"dep"}
    lock = {
        "info": {"version": version},
        "packages": {
            "PyYAML": {
                "file_name": "pyyaml-6.0-py3-none-any.whl",
                "sha256": hashlib.sha256(wheels["pyyaml-6.0-py3-none-any.whl"]).hexdigest(),
                "depends": ["extra"],
            },
            "extra": {
                "file_name": "extra-1.0-py3-none-any.whl",
                "sha256": hashlib.sha256(wheels["extra-1.0-py3-none-any.whl"]).hexdigest(),
                "depends": [],
            },
            "numpy": {"file_name": "numpy.whl", "sha256": "0" * 64, "depends": []},
        },
    }
    folder.mkdir(parents=True, exist_ok=True)
    for name in bundle.CORE_FILES:
        (folder / name).write_bytes(b"core " + name.encode())
    (folder / "pyodide.js").write_bytes(loader if loader is not None else b"LOADER")
    (folder / "pyodide-lock.json").write_text(json.dumps(lock))
    for name, data in wheels.items():
        (folder / name).write_bytes(data)
    assert build_web.PYODIDE_VERSION == "0.27.7"


@pytest.fixture
def pinned_loader(monkeypatch: pytest.MonkeyPatch) -> bytes:
    """Make the fake loader the release the add-in is pinned to."""
    bundle = load("bundle_pyodide")
    monkeypatch.setattr(bundle.build_web, "PYODIDE_INTEGRITY", bundle.integrity(b"LOADER"))
    runtime = {
        name: hashlib.sha256(b"core " + name.encode()).hexdigest() for name in bundle.RUNTIME_SHA256
    }
    monkeypatch.setattr(bundle, "RUNTIME_SHA256", runtime)
    return b"LOADER"


def test_bundling_copies_the_core_files_and_only_the_needed_packages(
    tmp_path: Path, pinned_loader: bytes
) -> None:
    bundle = load("bundle_pyodide")
    fake_distribution(tmp_path / "dist")

    digest = bundle.bundle(tmp_path / "dist", tmp_path / "out")

    assert digest == bundle.integrity(b"LOADER")
    assert sorted(path.name for path in (tmp_path / "out").iterdir()) == sorted(
        [*bundle.CORE_FILES, "pyyaml-6.0-py3-none-any.whl", "extra-1.0-py3-none-any.whl"]
    )


def test_a_package_that_fails_its_checksum_is_refused(tmp_path: Path, pinned_loader: bytes) -> None:
    bundle = load("bundle_pyodide")
    fake_distribution(tmp_path / "dist")
    (tmp_path / "dist" / "extra-1.0-py3-none-any.whl").write_bytes(b"tampered")

    with pytest.raises(bundle.BundleError, match="checksum"):
        bundle.bundle(tmp_path / "dist", tmp_path / "out")
    assert not (tmp_path / "out").exists()


def test_a_runtime_file_that_is_not_the_pinned_release_is_refused(
    tmp_path: Path, pinned_loader: bytes
) -> None:
    bundle = load("bundle_pyodide")
    fake_distribution(tmp_path / "dist")
    (tmp_path / "dist" / "pyodide.asm.wasm").write_bytes(b"swapped")

    with pytest.raises(bundle.BundleError, match=r"pyodide\.asm\.wasm is not the file"):
        bundle.bundle(tmp_path / "dist", tmp_path / "out")


def test_the_wrong_version_loader_or_missing_files_are_refused(
    tmp_path: Path, pinned_loader: bytes
) -> None:
    bundle = load("bundle_pyodide")
    fake_distribution(tmp_path / "old", version="0.26.0")
    fake_distribution(tmp_path / "odd", loader=b"something else")
    fake_distribution(tmp_path / "short")
    (tmp_path / "short" / "pyodide.asm.wasm").unlink()

    with pytest.raises(bundle.BundleError, match=r"expected Pyodide 0\.27\.7"):
        bundle.bundle(tmp_path / "old", tmp_path / "a")
    with pytest.raises(bundle.BundleError, match="not the release"):
        bundle.bundle(tmp_path / "odd", tmp_path / "b")
    with pytest.raises(bundle.BundleError, match="is missing"):
        bundle.bundle(tmp_path / "short", tmp_path / "c")


def test_a_missing_package_in_the_index_is_reported(tmp_path: Path, pinned_loader: bytes) -> None:
    bundle = load("bundle_pyodide")
    fake_distribution(tmp_path / "dist")
    lock = json.loads((tmp_path / "dist" / "pyodide-lock.json").read_text())
    del lock["packages"]["PyYAML"]
    (tmp_path / "dist" / "pyodide-lock.json").write_text(json.dumps(lock))

    with pytest.raises(bundle.BundleError, match="no package 'pyyaml'"):
        bundle.bundle(tmp_path / "dist", tmp_path / "out")


def test_downloading_uses_the_cdn_folder_and_the_same_checks(
    tmp_path: Path, pinned_loader: bytes
) -> None:
    bundle = load("bundle_pyodide")
    fake_distribution(tmp_path / "cdn")
    requested: list[str] = []

    def fetch(url: str) -> bytes:
        requested.append(url)
        return (tmp_path / "cdn" / url.rsplit("/", 1)[1]).read_bytes()

    bundle.download(tmp_path / "out", "https://cdn.example/pyodide/v0.27.7/full/", fetch)

    assert all(url.startswith("https://cdn.example/pyodide/v0.27.7/full/") for url in requested)
    assert (tmp_path / "out" / "pyodide.asm.wasm").is_file()


def test_downloading_refuses_plain_http_and_redirects_to_it() -> None:
    bundle = load("bundle_pyodide")

    with pytest.raises(bundle.BundleError, match="refusing to download"):
        bundle._fetch("http://example.com/pyodide.js")
    handler = bundle._HttpsOnly()
    with pytest.raises(bundle.BundleError, match="refusing to follow a redirect"):
        handler.redirect_request(None, None, 302, "Found", {}, "http://evil.example/x")


def test_the_bundle_command_reports_errors_and_usage(tmp_path: Path, capsys: Any) -> None:
    bundle = load("bundle_pyodide")

    assert bundle.main([str(tmp_path / "nowhere"), str(tmp_path / "out")]) == 1
    assert "bundle_pyodide:" in capsys.readouterr().err
    with pytest.raises(SystemExit):
        bundle.main(["only-one"])
    with pytest.raises(SystemExit):
        bundle.main(["--download", "a", "b"])


def test_an_offline_task_pane_loads_nothing_from_a_cdn(
    tmp_path: Path, pinned_loader: bytes
) -> None:
    builder = load("build_excel")
    fake_distribution(tmp_path / "dist")
    out = tmp_path / "out"

    builder.main(["--output-dir", str(out), "--bundle-pyodide", str(tmp_path / "dist")])

    page = (out / "taskpane.html").read_text(encoding="utf-8")
    assert "jsdelivr" not in page and 'src="pyodide/pyodide.js"' in page
    policy = page.split('content="default-src', 1)[1].split('"', 1)[0]
    assert "connect-src 'self'" in policy and "https://cdn" not in policy
    assert "https://appsforoffice.microsoft.com" in policy
    assert (out / "pyodide" / "pyodide.asm.wasm").is_file()


def test_a_failed_bundle_stops_the_build(tmp_path: Path) -> None:
    builder = load("build_excel")

    with pytest.raises(SystemExit):
        builder.main(["--output-dir", str(tmp_path / "o"), "--bundle-pyodide", str(tmp_path / "x")])


# Serving ---------------------------------------------------------------------------------


@pytest.fixture
def served(tmp_path: Path) -> Any:
    server_module = load("serve_excel")
    (tmp_path / "taskpane.html").write_text("<p>hi</p>", encoding="utf-8")
    (tmp_path / "manifest.xml").write_text("<x/>", encoding="utf-8")
    (tmp_path / "engine.wasm").write_bytes(b"\0asm")
    server = server_module.make_server(tmp_path, port=0, quiet=True)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield server
    server.shutdown()
    server.server_close()


def fetch(server: Any, path: str) -> tuple[int, dict[str, str], bytes]:
    connection = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=10)
    connection.request("GET", path)
    response = connection.getresponse()
    headers = {name.lower(): value for name, value in response.getheaders()}
    return response.status, headers, response.read()


def test_the_server_sends_the_content_types_office_and_webassembly_need(served: Any) -> None:
    for path, kind in [
        ("/taskpane.html", "text/html"),
        ("/manifest.xml", "application/xml"),
        ("/engine.wasm", "application/wasm"),
    ]:
        status, headers, _ = fetch(served, path)
        assert status == 200 and headers["content-type"].startswith(kind), path
        assert headers["cache-control"] == "no-store"


def test_the_server_stays_inside_its_folder(served: Any) -> None:
    assert fetch(served, "/missing.html")[0] == 404
    assert fetch(served, "/../../etc/passwd")[0] in {301, 400, 404}
    assert fetch(served, "/%2e%2e/%2e%2e/etc/passwd")[0] in {301, 400, 404}


def test_the_server_listens_on_this_computer_only_by_default(served: Any) -> None:
    assert served.server_address[0] == "127.0.0.1"


def test_the_server_needs_a_real_folder_and_both_halves_of_a_certificate(tmp_path: Path) -> None:
    server_module = load("serve_excel")

    with pytest.raises(ValueError, match="build the add-in first"):
        server_module.make_server(tmp_path / "nope", port=0)
    with pytest.raises(ValueError, match="both a certificate and a key"):
        server_module.make_server(tmp_path, port=0, certfile=tmp_path / "c.pem")


@pytest.mark.skipif(shutil.which("openssl") is None, reason="needs the openssl command")
def test_the_server_can_serve_over_https(tmp_path: Path) -> None:
    server_module = load("serve_excel")
    (tmp_path / "taskpane.html").write_text("<p>secure</p>", encoding="utf-8")
    cert, key = tmp_path / "cert.pem", tmp_path / "key.pem"
    subprocess.run(
        ["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", str(key),
         "-out", str(cert), "-days", "1", "-subj", "/CN=localhost"],
        check=True, capture_output=True,
    )  # fmt: skip
    server = server_module.make_server(tmp_path, port=0, certfile=cert, keyfile=key, quiet=True)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        context = ssl.create_default_context(cafile=str(cert))
        connection = http.client.HTTPSConnection(
            "localhost", server.server_address[1], timeout=10, context=context
        )
        connection.request("GET", "/taskpane.html")
        assert connection.getresponse().read() == b"<p>secure</p>"
    finally:
        server.shutdown()
        server.server_close()


def test_the_integrity_helper_matches_the_standard_format() -> None:
    bundle = load("bundle_pyodide")

    expected = "sha384-" + base64.b64encode(hashlib.sha384(b"x").digest()).decode()
    assert bundle.integrity(b"x") == expected
