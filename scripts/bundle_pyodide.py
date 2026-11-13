"""Collect the files of a Pyodide distribution that the add-in needs, for offline use.

The browser app loads Pyodide from a CDN. The Excel add-in can instead carry its own
copy, so that after Office's own library the page makes no network request at all. This
copies the core runtime, the package index, and the packages the application loads
(PyYAML and what it depends on) into one folder, checking every package against the
index's SHA-256 and the loader against the pinned subresource-integrity hash.

Usage::

    python scripts/bundle_pyodide.py DIST_DIR TARGET_DIR      # a local Pyodide distribution
    python scripts/bundle_pyodide.py --download TARGET_DIR    # fetch it from the CDN
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import sys
import urllib.request
from collections.abc import Callable
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_web

CORE_FILES = (
    "pyodide.js",
    "pyodide.asm.js",
    "pyodide.asm.wasm",
    "python_stdlib.zip",
    "pyodide-lock.json",
)
# SHA-256 of the runtime files for build_web.PYODIDE_VERSION. The package index checks the
# packages and a pinned hash checks the loader; these cover the rest of the runtime.
RUNTIME_SHA256 = {
    "pyodide.asm.js": "6b4c90de5b7172873f04f21884d0e9d2274e305fe32116558fe3e4fbe3618d51",
    "pyodide.asm.wasm": "a50dd1843f805a0b7c45b61037ee0d7b26dfe85efe0e18ef95a34ad24e401f5f",
    "python_stdlib.zip": "16611534726e5d8ac2bd8f926410b2dcb8d6f49aa24913463533b457a2115c16",
}
PACKAGES = ("pyyaml",)
"""Packages the application loads at start-up (``pyodide.loadPackage`` in app.js)."""

Fetch = Callable[[str], bytes]


class BundleError(Exception):
    """The Pyodide files are missing, from another version, or fail a check."""


def integrity(data: bytes) -> str:
    """Return the subresource-integrity string (``sha384-...``) of ``data``."""
    return "sha384-" + base64.b64encode(hashlib.sha384(data).digest()).decode()


def package_files(lock: dict) -> list[tuple[str, str]]:
    """Return ``(file_name, sha256)`` for each bundled package and its dependencies."""
    packages = {name.lower(): entry for name, entry in lock["packages"].items()}
    wanted: dict[str, tuple[str, str]] = {}
    pending = list(PACKAGES)
    while pending:
        name = pending.pop().lower()
        if name in wanted:
            continue
        if name not in packages:
            raise BundleError(f"the package index has no package {name!r}")
        entry = packages[name]
        wanted[name] = (entry["file_name"], entry["sha256"])
        pending.extend(entry.get("depends", []))
    return list(wanted.values())


def bundle(source: Path, target: Path) -> str:
    """Copy the needed files from a Pyodide distribution folder and return the loader's hash.

    Raises:
        BundleError: If a file is missing, the version is wrong, or a check fails.
    """
    return _collect(lambda name: _read(source, name), target)


def download(
    target: Path, base_url: str = build_web.PYODIDE_URL, fetch: Fetch | None = None
) -> str:
    """Fetch the needed files from a Pyodide CDN folder and bundle them into ``target``."""
    get = fetch or _fetch
    return _collect(lambda name: get(base_url + name), target)


def _collect(read: Callable[[str], bytes], target: Path) -> str:
    lock_bytes = read("pyodide-lock.json")
    lock = json.loads(lock_bytes)
    version = lock.get("info", {}).get("version")
    if version != build_web.PYODIDE_VERSION:
        raise BundleError(f"expected Pyodide {build_web.PYODIDE_VERSION}, found {version!r}")
    files = {name: read(name) for name in CORE_FILES if name != "pyodide-lock.json"}
    loader_hash = integrity(files["pyodide.js"])
    if loader_hash != build_web.PYODIDE_INTEGRITY:
        raise BundleError("pyodide.js is not the release this add-in is pinned to")
    for name, expected in RUNTIME_SHA256.items():
        if hashlib.sha256(files[name]).hexdigest() != expected:
            raise BundleError(f"{name} is not the file of the release this add-in is pinned to")
    for name, digest in package_files(lock):
        data = read(name)
        if hashlib.sha256(data).hexdigest() != digest:
            raise BundleError(f"{name} does not match the package index's checksum")
        files[name] = data
    files["pyodide-lock.json"] = lock_bytes
    target.mkdir(parents=True, exist_ok=True)
    for name, data in files.items():
        (target / name).write_bytes(data)
    return loader_hash


def _read(folder: Path, name: str) -> bytes:
    path = folder / name
    if not path.is_file():
        raise BundleError(f"{path} is missing")
    return path.read_bytes()


class _HttpsOnly(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        if not newurl.startswith("https://"):
            raise BundleError(f"refusing to follow a redirect to {newurl!r}")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _fetch(url: str) -> bytes:
    if not url.startswith("https://"):
        raise BundleError(f"refusing to download from {url!r}")
    opener = urllib.request.build_opener(_HttpsOnly)
    with opener.open(url, timeout=120) as response:
        return bytes(response.read())


def main(argv: list[str] | None = None) -> int:
    """Bundle Pyodide into a folder."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("paths", nargs="+", metavar="PATH")
    parser.add_argument("--download", action="store_true", help="fetch the files from the CDN")
    arguments = parser.parse_args(argv)
    try:
        if arguments.download:
            if len(arguments.paths) != 1:
                parser.error("--download takes the target folder only")
            download(Path(arguments.paths[0]))
        else:
            if len(arguments.paths) != 2:
                parser.error("give the Pyodide distribution folder and the target folder")
            bundle(Path(arguments.paths[0]), Path(arguments.paths[1]))
    except BundleError as exc:
        print(f"bundle_pyodide: {exc}", file=sys.stderr)
        return 1
    print("bundled Pyodide", build_web.PYODIDE_VERSION)
    return 0


if __name__ == "__main__":
    sys.exit(main())
