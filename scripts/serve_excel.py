"""Serve the built Excel add-in files, to try the add-in on your own computer.

Office loads the task pane from a web address and insists on HTTPS, so for a real
Excel give a certificate and key that Excel trusts (Microsoft's ``office-addin-dev-certs``
tool installs one for ``localhost``). Without them the files are served over plain HTTP,
which is enough for a browser but not for Excel.

The server listens on this computer only unless you pass another ``--host``.

Usage::

    python scripts/serve_excel.py [--dir dist/excel] [--port 3000] [--cert C.pem --key K.pem]
"""

from __future__ import annotations

import argparse
import functools
import ssl
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import ClassVar

ROOT = Path(__file__).resolve().parent.parent


class Handler(SimpleHTTPRequestHandler):
    """Serves files with the content types Office and WebAssembly need, and no caching."""

    quiet: ClassVar[bool] = False
    extensions_map: ClassVar[dict[str, str]] = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".wasm": "application/wasm",
        ".js": "text/javascript",
        ".xml": "application/xml",
        ".json": "application/json",
        ".whl": "application/octet-stream",
        ".zip": "application/zip",
        ".png": "image/png",
        ".html": "text/html; charset=utf-8",
    }

    def end_headers(self) -> None:
        """Add a no-store header, then finish the headers."""
        # Always serve the newest build while the add-in is being tried out.
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, format: str, *args: object) -> None:
        """Log each request to standard error."""
        if not self.quiet:
            sys.stderr.write(f"{self.address_string()} {format % args}\n")


def make_server(
    directory: Path,
    host: str = "127.0.0.1",
    port: int = 3000,
    certfile: Path | None = None,
    keyfile: Path | None = None,
    *,
    quiet: bool = False,
) -> ThreadingHTTPServer:
    """Return a server for ``directory``; HTTPS when a certificate and key are given."""
    if (certfile is None) != (keyfile is None):
        raise ValueError("give both a certificate and a key, or neither")
    if not directory.is_dir():
        raise ValueError(f"{directory} is not a folder; build the add-in first")
    base = type("QuietHandler", (Handler,), {"quiet": True}) if quiet else Handler
    handler = functools.partial(base, directory=str(directory))
    server = ThreadingHTTPServer((host, port), handler)
    if certfile is not None and keyfile is not None:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(str(certfile), str(keyfile))
        server.socket = context.wrap_socket(server.socket, server_side=True)
    return server


def main(argv: list[str] | None = None) -> int:
    """Serve the add-in until interrupted."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dir", default=str(ROOT / "dist" / "excel"), type=Path)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=3000, type=int)
    parser.add_argument("--cert", type=Path, help="TLS certificate (PEM) for HTTPS")
    parser.add_argument("--key", type=Path, help="TLS private key (PEM) for HTTPS")
    arguments = parser.parse_args(argv)
    try:
        server = make_server(
            arguments.dir, arguments.host, arguments.port, arguments.cert, arguments.key
        )
    except (ValueError, OSError, ssl.SSLError) as exc:
        parser.error(str(exc))
    scheme = "https" if arguments.cert else "http"
    host, port = server.server_address[:2]
    print(f"serving {arguments.dir} at {scheme}://{host}:{port}/ (Ctrl+C to stop)")
    if not arguments.cert:
        print("plain HTTP: fine for a browser, but Excel needs HTTPS (see --cert and --key)")
    if arguments.host not in {"127.0.0.1", "localhost", "::1"}:
        print(f"warning: anyone who can reach {arguments.host} can read these files")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
