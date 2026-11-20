"""Build the Excel add-in: a task pane page, an add-in manifest, and icons.

The task pane is the browser application with a way to read the cells selected in
Excel and write results to a new sheet. Office loads it from a web address, so it
must be served over HTTPS; pass the address the files will be served from.

Usage::

    python scripts/build_excel.py --base-url https://example.com/finassert/
"""

from __future__ import annotations

import argparse
import struct
import sys
import uuid
import zlib
from pathlib import Path
from xml.sax.saxutils import quoteattr

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_web  # noqa: E402
import bundle_pyodide  # noqa: E402
from user_guide import GuideAssetError, copy_assets  # noqa: E402

ADD_IN_ID = uuid.uuid5(uuid.NAMESPACE_URL, "https://github.com/thatquantguy44/finassert#excel")
# Office's manifest validator requires >= 1.0. This deployment version is separate
# from the Python package/runtime version displayed in the task pane.
ADD_IN_VERSION = "1.0.0.1"
SUPPORT_URL = "https://github.com/thatquantguy44/finassert"


def manifest(base_url: str) -> str:
    """Return the add-in manifest for a task pane served from ``base_url``."""
    taskpane_url = quoteattr(base_url + "taskpane.html")
    settings_url = quoteattr(base_url + "taskpane.html?view=settings")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<OfficeApp xmlns="http://schemas.microsoft.com/office/appforoffice/1.1"
           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xmlns:bt="http://schemas.microsoft.com/office/officeappbasictypes/1.0"
           xsi:type="TaskPaneApp">
  <Id>{ADD_IN_ID}</Id>
  <Version>{ADD_IN_VERSION}</Version>
  <ProviderName>finassert</ProviderName>
  <DefaultLocale>en-US</DefaultLocale>
  <DisplayName DefaultValue="finassert"/>
  <Description DefaultValue="Check financial data in your workbook against a validation policy."/>
  <IconUrl DefaultValue={quoteattr(base_url + "icon-32.png")}/>
  <HighResolutionIconUrl DefaultValue={quoteattr(base_url + "icon-64.png")}/>
  <SupportUrl DefaultValue={quoteattr(SUPPORT_URL)}/>
  <Hosts>
    <Host Name="Workbook"/>
  </Hosts>
  <Requirements>
    <Sets DefaultMinVersion="1.7">
      <Set Name="ExcelApi" MinVersion="1.7"/>
    </Sets>
  </Requirements>
  <DefaultSettings>
    <SourceLocation DefaultValue={taskpane_url}/>
  </DefaultSettings>
  <Permissions>ReadWriteDocument</Permissions>
  <VersionOverrides xmlns="http://schemas.microsoft.com/office/taskpaneappversionoverrides"
                    xsi:type="VersionOverridesV1_0">
    <Hosts>
      <Host xsi:type="Workbook">
        <DesktopFormFactor>
          <FunctionFile resid="Taskpane.Url"/>
          <ExtensionPoint xsi:type="PrimaryCommandSurface">
            <OfficeTab id="TabHome">
              <Group id="Finassert.Ribbon.Group">
                <Label resid="Finassert.Group.Label"/>
                <Icon>
                  <bt:Image size="16" resid="Finassert.Icon.16"/>
                  <bt:Image size="32" resid="Finassert.Icon.32"/>
                  <bt:Image size="80" resid="Finassert.Icon.80"/>
                </Icon>
                <Control xsi:type="Button" id="Finassert.OpenValidation">
                  <Label resid="Finassert.OpenValidation.Label"/>
                  <Supertip>
                    <Title resid="Finassert.OpenValidation.Label"/>
                    <Description resid="Finassert.Validation.Help"/>
                  </Supertip>
                  <Icon>
                    <bt:Image size="16" resid="Finassert.Icon.16"/>
                    <bt:Image size="32" resid="Finassert.Icon.32"/>
                    <bt:Image size="80" resid="Finassert.Icon.80"/>
                  </Icon>
                  <Action xsi:type="ShowTaskpane">
                    <TaskpaneId>Finassert.Validation</TaskpaneId>
                    <SourceLocation resid="Taskpane.Url"/>
                    <Title resid="Finassert.Validation.Title"/>
                  </Action>
                </Control>
                <Control xsi:type="Button" id="Finassert.OpenSettings">
                  <Label resid="Finassert.OpenSettings.Label"/>
                  <Supertip>
                    <Title resid="Finassert.OpenSettings.Label"/>
                    <Description resid="Finassert.Settings.Help"/>
                  </Supertip>
                  <Icon>
                    <bt:Image size="16" resid="Finassert.Icon.16"/>
                    <bt:Image size="32" resid="Finassert.Icon.32"/>
                    <bt:Image size="80" resid="Finassert.Icon.80"/>
                  </Icon>
                  <Action xsi:type="ShowTaskpane">
                    <TaskpaneId>Finassert.Settings</TaskpaneId>
                    <SourceLocation resid="Settings.Url"/>
                    <Title resid="Finassert.Settings.Title"/>
                  </Action>
                </Control>
              </Group>
            </OfficeTab>
          </ExtensionPoint>
        </DesktopFormFactor>
      </Host>
    </Hosts>
    <Resources>
      <bt:Images>
        <bt:Image id="Finassert.Icon.16" DefaultValue={quoteattr(base_url + "icon-16.png")}/>
        <bt:Image id="Finassert.Icon.32" DefaultValue={quoteattr(base_url + "icon-32.png")}/>
        <bt:Image id="Finassert.Icon.80" DefaultValue={quoteattr(base_url + "icon-80.png")}/>
      </bt:Images>
      <bt:Urls>
        <bt:Url id="Taskpane.Url" DefaultValue={taskpane_url}/>
        <bt:Url id="Settings.Url" DefaultValue={settings_url}/>
      </bt:Urls>
      <bt:ShortStrings>
        <bt:String id="Finassert.Group.Label" DefaultValue="finassert"/>
        <bt:String id="Finassert.OpenValidation.Label" DefaultValue="Open validation"/>
        <bt:String id="Finassert.OpenSettings.Label" DefaultValue="Settings"/>
        <bt:String id="Finassert.Validation.Title" DefaultValue="finassert Validation"/>
        <bt:String id="Finassert.Settings.Title" DefaultValue="finassert Settings"/>
      </bt:ShortStrings>
      <bt:LongStrings>
        <bt:String id="Finassert.Validation.Help"
                   DefaultValue="Open the finassert validation task pane for this workbook."/>
        <bt:String id="Finassert.Settings.Help"
                   DefaultValue="Open the finassert task pane at freshness and capture settings."/>
      </bt:LongStrings>
    </Resources>
  </VersionOverrides>
</OfficeApp>
"""


def icon(size: int) -> bytes:
    """Return a plain placeholder PNG: a blue square with a white centre."""
    blue, white = bytes((0x1F, 0x5F, 0xBF)), bytes((0xFF, 0xFF, 0xFF))
    margin = size // 4
    rows = []
    for y in range(size):
        inside_y = margin <= y < size - margin
        row = b"".join(
            white if inside_y and margin <= x < size - margin else blue for x in range(size)
        )
        rows.append(b"\x00" + row)

    def chunk(kind: bytes, data: bytes) -> bytes:
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))

    header = struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(b"".join(rows), 9))
        + chunk(b"IEND", b"")
    )


def main(argv: list[str] | None = None) -> int:
    """Write the task pane, manifest, and icons."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--base-url",
        default="https://localhost:3000/",
        help="HTTPS address, ending in '/', that the output files will be served from",
    )
    parser.add_argument("--output-dir", default=str(ROOT / "dist" / "excel"))
    parser.add_argument("--pyodide-url", default=build_web.PYODIDE_URL)
    parser.add_argument(
        "--bundle-pyodide",
        metavar="DIR|download",
        help=(
            "carry Pyodide inside the add-in, for use with no CDN: a local Pyodide "
            "distribution folder, or 'download' to fetch it"
        ),
    )
    arguments = parser.parse_args(argv)
    if not arguments.base_url.startswith("https://") or not arguments.base_url.endswith("/"):
        parser.error("--base-url must start with https:// and end with '/'")
    if not arguments.pyodide_url.endswith("/"):
        parser.error("--pyodide-url must end with '/'")

    output = Path(arguments.output_dir)
    sys.path.insert(0, str(ROOT / "src"))
    try:
        copy_assets(output)
    except GuideAssetError as exc:
        parser.error(str(exc))
    output.mkdir(parents=True, exist_ok=True)
    pyodide_url = arguments.pyodide_url
    if arguments.bundle_pyodide:
        try:
            if arguments.bundle_pyodide == "download":
                bundle_pyodide.download(output / "pyodide")
            else:
                bundle_pyodide.bundle(Path(arguments.bundle_pyodide), output / "pyodide")
        except bundle_pyodide.BundleError as exc:
            parser.error(f"cannot bundle Pyodide: {exc}")
        pyodide_url = "pyodide/"
    (output / "taskpane.html").write_text(
        build_web.build(pyodide_url, excel=True), encoding="utf-8"
    )
    (output / "manifest.xml").write_text(manifest(arguments.base_url), encoding="utf-8")
    for size in (16, 32, 64, 80):
        (output / f"icon-{size}.png").write_bytes(icon(size))
    print(f"wrote the Excel add-in to {output} (serve it at {arguments.base_url})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
