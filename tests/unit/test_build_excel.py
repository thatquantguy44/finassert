import base64
import hashlib
import importlib.util
import re
import struct
import sys
import zlib
from pathlib import Path
from types import ModuleType
from xml.etree import ElementTree

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load(name: str) -> ModuleType:
    sys.path.insert(0, str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_the_task_pane_adds_excel_support_and_every_inline_script_is_hashed() -> None:
    page = load("build_web").build(excel=True)

    assert "{{" not in page
    assert 'id="excel-panel"' in page and 'id="excel-read"' in page and 'id="excel-write"' in page
    for control in ("excel-spike", "spike-run", "spike-copy", "spike-report", "spike-how"):
        assert f'id="{control}"' in page
    assert (
        '<script src="https://appsforoffice.microsoft.com/lib/1/hosted/office.js"></script>' in page
    )
    policy = re.search(r'http-equiv="Content-Security-Policy" content="([^"]+)"', page)
    assert policy is not None
    text = policy.group(1)
    assert "https://appsforoffice.microsoft.com" in text
    assert "'unsafe-inline'" not in text.split("style-src")[0]
    scripts = re.findall(r"<script>(.*?)</script>", page, re.S)
    assert len(scripts) == 2  # the application and the Excel script
    for script in scripts:
        digest = base64.b64encode(hashlib.sha256(script.encode()).digest()).decode()
        assert f"'sha256-{digest}'" in text


def test_the_plain_browser_app_has_no_excel_code_and_loads_nothing_from_microsoft() -> None:
    page = load("build_web").build()

    assert "{{" not in page
    assert "excel-panel" not in page and "appsforoffice" not in page and "Excel.run" not in page
    assert "spike-run" not in page and "{{VERSION}}" not in page


def test_the_manifest_names_the_task_pane_and_asks_for_the_permission_it_needs() -> None:
    builder = load("build_excel")

    root = ElementTree.fromstring(builder.manifest("https://example.com/finassert/", "0.1.0"))

    ns = {"o": "http://schemas.microsoft.com/office/appforoffice/1.1"}
    assert root.tag == "{http://schemas.microsoft.com/office/appforoffice/1.1}OfficeApp"
    assert root.find("o:Version", ns).text == "0.1.0.0"  # type: ignore[union-attr]
    assert root.find("o:Permissions", ns).text == "ReadWriteDocument"  # type: ignore[union-attr]
    assert root.find("o:Hosts/o:Host", ns).get("Name") == "Workbook"  # type: ignore[union-attr]
    source = root.find("o:DefaultSettings/o:SourceLocation", ns)
    assert source is not None and source.get("DefaultValue") == (
        "https://example.com/finassert/taskpane.html"
    )
    assert root.find("o:Id", ns).text == str(builder.ADD_IN_ID)  # type: ignore[union-attr]
    # The add-in keeps one identity across builds.
    assert builder.manifest("https://a.example/", "0.1.0").count(str(builder.ADD_IN_ID)) == 1


def test_manifest_values_are_escaped() -> None:
    builder = load("build_excel")

    text = builder.manifest('https://example.com/a"b&c/', "0.1.0")

    ElementTree.fromstring(text)  # still well-formed
    assert "&amp;" in text


@pytest.mark.parametrize("size", [32, 64])
def test_the_placeholder_icons_are_valid_pngs(size: int) -> None:
    data = load("build_excel").icon(size)

    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    length, kind = struct.unpack(">I4s", data[8:16])
    assert kind == b"IHDR" and length == 13
    width, height = struct.unpack(">II", data[16:24])
    assert (width, height) == (size, size)
    idat = data[data.index(b"IDAT") + 4 : data.index(b"IEND") - 8]
    assert len(zlib.decompress(idat)) == size * (1 + size * 3)


def test_the_build_script_requires_an_https_base_address(tmp_path: Path) -> None:
    builder = load("build_excel")

    with pytest.raises(SystemExit):
        builder.main(["--base-url", "http://example.com/", "--output-dir", str(tmp_path)])
    with pytest.raises(SystemExit):
        builder.main(["--base-url", "https://example.com", "--output-dir", str(tmp_path)])
    assert (
        builder.main(["--base-url", "https://example.com/x/", "--output-dir", str(tmp_path)]) == 0
    )
    assert sorted(path.name for path in tmp_path.iterdir()) == [
        "icon-32.png",
        "icon-64.png",
        "manifest.xml",
        "taskpane.html",
    ]
