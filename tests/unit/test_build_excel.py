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
    assert "excel-panel" not in page and "appsforoffice" not in page
    assert not re.search(r"\bExcel\.run\(", page)
    assert "spike-run" not in page and "{{VERSION}}" not in page


def test_the_manifest_names_the_task_pane_and_asks_for_the_permission_it_needs() -> None:
    builder = load("build_excel")

    root = ElementTree.fromstring(builder.manifest("https://example.com/finassert/"))

    ns = {"o": "http://schemas.microsoft.com/office/appforoffice/1.1"}
    assert root.tag == "{http://schemas.microsoft.com/office/appforoffice/1.1}OfficeApp"
    # The deployment version meets Office's >=1.0 constraint independently of
    # the package's prerelease version; the pane retains its real package version.
    assert root.find("o:Version", ns).text == "1.0.0.1"  # type: ignore[union-attr]
    assert root.find("o:Permissions", ns).text == "ReadWriteDocument"  # type: ignore[union-attr]
    assert root.find("o:Hosts/o:Host", ns).get("Name") == "Workbook"  # type: ignore[union-attr]
    requirement = root.find("o:Requirements/o:Sets/o:Set", ns)
    assert requirement is not None
    # getRangeByIndexes is used for sheet writes and requires ExcelApi 1.7.
    assert requirement.attrib == {"Name": "ExcelApi", "MinVersion": "1.7"}
    source = root.find("o:DefaultSettings/o:SourceLocation", ns)
    assert source is not None and source.get("DefaultValue") == (
        "https://example.com/finassert/taskpane.html"
    )
    assert root.find("o:Id", ns).text == str(builder.ADD_IN_ID)  # type: ignore[union-attr]
    # The add-in keeps one identity across builds.
    assert builder.manifest("https://a.example/").count(str(builder.ADD_IN_ID)) == 1


def test_manifest_adds_home_ribbon_commands_for_validation_and_settings() -> None:
    builder = load("build_excel")
    root = ElementTree.fromstring(builder.manifest("https://example.com/finassert/"))
    ns = {
        "vo": "http://schemas.microsoft.com/office/taskpaneappversionoverrides",
        "bt": "http://schemas.microsoft.com/office/officeappbasictypes/1.0",
    }
    group = root.find(
        "vo:VersionOverrides/vo:Hosts/vo:Host/vo:DesktopFormFactor/"
        "vo:ExtensionPoint/vo:OfficeTab/vo:Group[@id='Finassert.Ribbon.Group']",
        ns,
    )
    assert group is not None
    assert group.find("vo:Label", ns).get("resid") == "Finassert.Group.Label"  # type: ignore[union-attr]
    controls = {control.get("id"): control for control in group.findall("vo:Control", ns)}
    validation = controls["Finassert.OpenValidation"]
    settings = controls["Finassert.OpenSettings"]
    for control, pane_id, resource, title in (
        (validation, "Finassert.Validation", "Taskpane.Url", "Finassert.Validation.Title"),
        (settings, "Finassert.Settings", "Settings.Url", "Finassert.Settings.Title"),
    ):
        action = control.find("vo:Action", ns)
        assert action is not None
        assert action.get("{http://www.w3.org/2001/XMLSchema-instance}type") == "ShowTaskpane"
        assert action.find("vo:TaskpaneId", ns).text == pane_id  # type: ignore[union-attr]
        assert action.find("vo:SourceLocation", ns).get("resid") == resource  # type: ignore[union-attr]
        assert action.find("vo:Title", ns).get("resid") == title  # type: ignore[union-attr]
    resources = root.find("vo:VersionOverrides/vo:Resources", ns)
    assert resources is not None
    urls = {
        url.get("id"): url.get("DefaultValue") for url in resources.findall("bt:Urls/bt:Url", ns)
    }
    assert urls == {
        "Taskpane.Url": "https://example.com/finassert/taskpane.html",
        "Settings.Url": "https://example.com/finassert/taskpane.html?view=settings",
    }
    strings = {
        item.get("id"): item.get("DefaultValue")
        for item in resources.findall("bt:ShortStrings/bt:String", ns)
    }
    assert strings["Finassert.Validation.Title"] == "finassert Validation"
    assert strings["Finassert.Settings.Title"] == "finassert Settings"


def test_manifest_values_are_escaped() -> None:
    builder = load("build_excel")

    text = builder.manifest('https://example.com/a"b&c/')

    ElementTree.fromstring(text)  # still well-formed
    assert "&amp;" in text


@pytest.mark.parametrize("size", [16, 32, 64, 80])
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
        "finassert-user-guide.json",
        "finassert-user-guide.pdf",
        "icon-16.png",
        "icon-32.png",
        "icon-64.png",
        "icon-80.png",
        "manifest.xml",
        "taskpane.html",
    ]
