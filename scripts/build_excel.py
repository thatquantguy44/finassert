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

ADD_IN_ID = uuid.uuid5(uuid.NAMESPACE_URL, "https://github.com/thatquantguy44/finassert#excel")
SUPPORT_URL = "https://github.com/thatquantguy44/finassert"


def manifest(base_url: str, version: str) -> str:
    """Return the add-in manifest for a task pane served from ``base_url``."""
    parts = [*version.split("."), "0", "0", "0", "0"][:4]
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<OfficeApp xmlns="http://schemas.microsoft.com/office/appforoffice/1.1"
           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xsi:type="TaskPaneApp">
  <Id>{ADD_IN_ID}</Id>
  <Version>{".".join(parts)}</Version>
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
  <DefaultSettings>
    <SourceLocation DefaultValue={quoteattr(base_url + "taskpane.html")}/>
  </DefaultSettings>
  <Permissions>ReadWriteDocument</Permissions>
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
    arguments = parser.parse_args(argv)
    if not arguments.base_url.startswith("https://") or not arguments.base_url.endswith("/"):
        parser.error("--base-url must start with https:// and end with '/'")
    if not arguments.pyodide_url.endswith("/"):
        parser.error("--pyodide-url must end with '/'")

    output = Path(arguments.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "taskpane.html").write_text(
        build_web.build(arguments.pyodide_url, excel=True), encoding="utf-8"
    )
    (output / "manifest.xml").write_text(
        manifest(arguments.base_url, build_web.package_version()), encoding="utf-8"
    )
    for size in (32, 64):
        (output / f"icon-{size}.png").write_bytes(icon(size))
    print(f"wrote the Excel add-in to {output} (serve it at {arguments.base_url})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
