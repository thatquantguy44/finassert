"""Build the single-file browser application.

The output is one HTML file that embeds the finassert package. It can be opened
by double-clicking, emailed, or served from any static host. Python itself is
loaded from the pinned Pyodide CDN release; after that the page makes no
network requests, and its Content-Security-Policy forbids sending data
anywhere else.

Usage::

    python scripts/build_web.py [--output dist/web/finassert.html]
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "src" / "finassert"
WEB = ROOT / "web"
PYODIDE_VERSION = "0.27.7"
PYODIDE_URL = f"https://cdn.jsdelivr.net/pyodide/v{PYODIDE_VERSION}/full/"
_FIXED_TIME = (1980, 1, 1, 0, 0, 0)


def package_archive() -> bytes:
    """Return a deterministic zip of the finassert package sources."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        files = sorted(
            path
            for path in PACKAGE.rglob("*")
            if path.is_file() and (path.suffix == ".py" or path.name == "py.typed")
        )
        for path in files:
            info = zipfile.ZipInfo(
                str(path.relative_to(PACKAGE.parent).as_posix()), date_time=_FIXED_TIME
            )
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())
    return buffer.getvalue()


def package_version() -> str:
    """Read the package version without importing finassert."""
    text = (PACKAGE / "_version.py").read_text(encoding="utf-8")
    match = re.search(r'__version__ = "([^"]+)"', text)
    if match is None:
        raise SystemExit("cannot find __version__ in _version.py")
    return match.group(1)


def build(pyodide_url: str = PYODIDE_URL) -> str:
    """Return the complete application HTML."""
    version = package_version()
    app_js = (WEB / "app.js").read_text(encoding="utf-8").replace("{{PYODIDE_URL}}", pyodide_url)
    script_hash = base64.b64encode(hashlib.sha256(app_js.encode("utf-8")).digest()).decode()
    csp = "; ".join(
        [
            "default-src 'none'",
            f"script-src 'sha256-{script_hash}' 'wasm-unsafe-eval' {pyodide_url}",
            f"connect-src {pyodide_url}",
            "style-src 'unsafe-inline'",
            "img-src data:",
            "base-uri 'none'",
            "form-action 'none'",
        ]
    )
    wheel = base64.b64encode(package_archive()).decode("ascii")
    replacements = {
        "{{CSP}}": csp,
        "{{STYLE}}": (WEB / "app.css").read_text(encoding="utf-8"),
        "{{PYODIDE_URL}}": pyodide_url,
        "{{PYODIDE_VERSION}}": PYODIDE_VERSION,
        "{{VERSION}}": version,
        "{{WHEEL_NAME}}": f"finassert-{version}.zip",
        "{{WHEEL_B64}}": wheel,
        "{{APP_JS}}": app_js,
    }
    html = (WEB / "index.html").read_text(encoding="utf-8")
    for token, value in replacements.items():
        if token not in html:
            raise SystemExit(f"template is missing {token}")
        html = html.replace(token, value)
    return html


def main(argv: list[str] | None = None) -> int:
    """Write the application to the requested path."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output", default=str(ROOT / "dist" / "web" / "finassert.html"))
    parser.add_argument(
        "--pyodide-url",
        default=PYODIDE_URL,
        help="Pyodide distribution URL ending in '/', for self-hosting",
    )
    arguments = parser.parse_args(argv)
    if not arguments.pyodide_url.endswith("/"):
        parser.error("--pyodide-url must end with '/'")
    output = Path(arguments.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build(arguments.pyodide_url), encoding="utf-8")
    print(f"wrote {output} ({output.stat().st_size // 1024} KiB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
