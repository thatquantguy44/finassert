import base64
import hashlib
import importlib.util
import io
import re
import subprocess
import sys
import zipfile
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[2]


def load_builder() -> ModuleType:
    spec = importlib.util.spec_from_file_location("build_web", ROOT / "scripts" / "build_web.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_built_page_has_no_placeholders_and_a_matching_script_hash() -> None:
    builder = load_builder()
    page = builder.build()

    assert "{{" not in page
    csp = re.search(r'http-equiv="Content-Security-Policy" content="([^"]+)"', page)
    assert csp is not None
    policy = csp.group(1)
    assert "default-src 'none'" in policy
    assert f"connect-src {builder.PYODIDE_URL}" in policy
    assert "'unsafe-eval'" not in policy.replace("'wasm-unsafe-eval'", "")

    inline_scripts = re.findall(r"<script>(.*?)</script>", page, re.S)
    assert len(inline_scripts) == 1
    digest = base64.b64encode(hashlib.sha256(inline_scripts[0].encode()).digest()).decode()
    assert f"'sha256-{digest}'" in policy


def test_embedded_package_imports_and_runs(tmp_path: Path) -> None:
    builder = load_builder()
    page = builder.build()
    encoded = re.search(r'id="finassert-wheel"[^>]*>([^<]+)</script>', page)
    assert encoded is not None
    archive = zipfile.ZipFile(io.BytesIO(base64.b64decode(encoded.group(1))))
    names = archive.namelist()
    assert "finassert/web.py" in names
    assert "finassert/py.typed" in names
    assert all(name.startswith("finassert/") for name in names)
    archive.extractall(tmp_path)

    script = (
        "import json, finassert.web as w; "
        "print(json.loads(w.run('weight\\n1\\n', 'd.csv', "
        "json.dumps({'version': 1, 'rules': [{'rule': 'weights_sum_to_one'}]})))['passed'])"
    )
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            f"import sys; sys.path.insert(0, {str(tmp_path)!r}); {script}",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "True"


def test_package_archive_is_reproducible() -> None:
    builder = load_builder()
    assert builder.package_archive() == builder.package_archive()


def test_application_script_makes_no_network_calls_of_its_own() -> None:
    script = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
    for forbidden in ("fetch(", "XMLHttpRequest", "WebSocket", "sendBeacon", "eval(", "innerHTML"):
        assert forbidden not in script, forbidden
