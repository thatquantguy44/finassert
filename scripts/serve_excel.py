"""Serve the built Excel add-in files, to try the add-in on your own computer.

Office loads the task pane from a web address and insists on HTTPS, so for a real
Excel give a certificate and key that Excel trusts (Microsoft's ``office-addin-dev-certs``
tool installs one for ``localhost``). Without them the files are served over plain HTTP,
which is enough for a browser but not for Excel.

The server listens on this computer only unless you pass another ``--host``.

Usage::

    python scripts/serve_excel.py [--dir dist/excel] [--port 3000] [--cert C.pem --key K.pem]
      [--quantsmith-checkout ../QuantSmith]
"""

from __future__ import annotations

import argparse
import functools
import json
import os
import ssl
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import ClassVar
from urllib.parse import urlsplit

from quantsmith_docs import Catalog, GitHubCatalog
from user_guide import API_PATH, PDF_PATH, GuideAssetError, read_asset

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_QUANTSMITH_CHECKOUT = Path(
    os.environ.get(
        "FINASSERT_QUANTSMITH_LOCAL_PATH",
        "/Users/joshualutkemuller/Documents/Quant Sandbox/agentic_workflows/qf_workflow_sdk_public",
    )
)


class Handler(SimpleHTTPRequestHandler):
    """Serves files with the content types Office and WebAssembly need, and no caching."""

    quiet: ClassVar[bool] = False
    docs_catalog: ClassVar[Catalog | GitHubCatalog | None] = None
    docs_error: ClassVar[str | None] = None
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

    def do_GET(self) -> None:
        """Serve static files or the optional same-origin read-only docs API."""
        if self._serve_guide(head=False):
            return
        path = urlsplit(self.path).path
        prefix = "/api/quantsmith/v1/docs"
        if path != prefix and not path.startswith(prefix + "/"):
            super().do_GET()
            return
        if self.docs_catalog is None:
            if self.docs_error is None:
                self.send_error(404)
            else:
                self.send_error(503, "Pinned reference unavailable")
            return
        host = self.headers.get("Host", "")
        try:
            parsed_host = urlsplit("http://" + host)
            valid_host = (
                parsed_host.hostname in {"localhost", "127.0.0.1", "::1"}
                and parsed_host.port == self.server.server_port
            )
        except ValueError:
            valid_host = False
        origin = self.headers.get("Origin")
        scheme = "https" if isinstance(self.connection, ssl.SSLSocket) else "http"
        if not valid_host or (origin and origin != f"{scheme}://{host}"):
            self.send_error(403)
            return
        try:
            if path == prefix:
                result = self.docs_catalog.listing()
            else:
                result = self.docs_catalog.read(path[len(prefix) + 1 :])
        except ValueError:
            self.send_error(503, "Pinned reference unavailable")
            return
        if result is None:
            self.send_error(404)
            return
        body = json.dumps(result, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def do_HEAD(self) -> None:
        """Expose download metadata without transferring the PDF body."""
        if not self._serve_guide(head=True):
            super().do_HEAD()

    def _serve_guide(self, *, head: bool) -> bool:
        path = urlsplit(self.path).path
        if path not in {API_PATH, PDF_PATH}:
            if path.startswith("/api/finassert/"):
                self.send_error(404, "Unknown documentation route")
                return True
            return False
        try:
            asset = read_asset(Path(self.directory))
        except FileNotFoundError:
            self.send_error(404, "User guide not built; rebuild the add-in assets")
            return True
        except (OSError, GuideAssetError):
            self.send_error(503, "User guide unavailable; rebuild the guide and add-in assets")
            return True
        pdf = path == PDF_PATH
        body = (
            asset.pdf
            if pdf
            else json.dumps(asset.metadata, ensure_ascii=False, separators=(",", ":")).encode()
        )
        self.send_response(200)
        self.send_header(
            "Content-Type", "application/pdf" if pdf else "application/json; charset=utf-8"
        )
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        if pdf:
            self.send_header(
                "Content-Disposition", 'attachment; filename="finassert-user-guide.pdf"'
            )
        self.end_headers()
        if not head:
            self.wfile.write(body)
        return True


def make_server(
    directory: Path,
    host: str = "127.0.0.1",
    port: int = 3000,
    certfile: Path | None = None,
    keyfile: Path | None = None,
    *,
    quiet: bool = False,
    quantsmith_source: str = "disabled",
    quantsmith_checkout: Path | None = None,
    quantsmith_lock: Path | None = None,
    quantsmith_github_token: str | None = None,
) -> ThreadingHTTPServer:
    """Return a server for ``directory``; HTTPS when a certificate and key are given."""
    if (certfile is None) != (keyfile is None):
        raise ValueError("give both a certificate and a key, or neither")
    if not directory.is_dir():
        raise ValueError(f"{directory} is not a folder; build the add-in first")
    if quantsmith_source not in {"disabled", "local", "github"}:
        raise ValueError("QuantSmith source must be disabled, local, or github")
    if quantsmith_source == "disabled" and (
        quantsmith_checkout is not None or quantsmith_lock is not None or quantsmith_github_token
    ):
        raise ValueError("choose a QuantSmith source before configuring it")
    if quantsmith_source != "disabled" and host not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("the private QuantSmith reference is local-only")
    catalog: Catalog | GitHubCatalog | None = None
    docs_error: str | None = None
    if quantsmith_source != "disabled":
        try:
            lock = quantsmith_lock or ROOT / "integrations" / "quantsmith-docs.lock.json"
            if quantsmith_source == "local":
                catalog = Catalog(quantsmith_checkout or DEFAULT_QUANTSMITH_CHECKOUT, lock)
            else:
                catalog = GitHubCatalog(lock, quantsmith_github_token)
        except ValueError:
            # Preserve the validation pane when a local checkout is absent or the
            # explicitly selected GitHub source cannot authenticate.  The API
            # returns 503 rather than silently exposing a different revision.
            docs_error = "Pinned reference unavailable"
    base = type(
        "ReferenceHandler",
        (Handler,),
        {"quiet": quiet, "docs_catalog": catalog, "docs_error": docs_error},
    )
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
    parser.add_argument(
        "--quantsmith-source",
        choices=("local", "github", "disabled"),
        default=os.environ.get("FINASSERT_QUANTSMITH_SOURCE", "local"),
        help="reference source (default: local; GitHub is explicit and read-only)",
    )
    parser.add_argument(
        "--quantsmith-checkout",
        type=Path,
        default=DEFAULT_QUANTSMITH_CHECKOUT,
        help=f"pinned local checkout (default: {DEFAULT_QUANTSMITH_CHECKOUT})",
    )
    parser.add_argument(
        "--quantsmith-lock",
        type=Path,
        help="override the pinned reference manifest",
    )
    parser.add_argument(
        "--quantsmith-github-token-env",
        default="FINASSERT_QUANTSMITH_GITHUB_TOKEN",
        help="environment variable with a GitHub Contents-read token for GitHub mode",
    )
    arguments = parser.parse_args(argv)
    try:
        server = make_server(
            arguments.dir,
            arguments.host,
            arguments.port,
            arguments.cert,
            arguments.key,
            quantsmith_source=arguments.quantsmith_source,
            quantsmith_checkout=(
                arguments.quantsmith_checkout if arguments.quantsmith_source == "local" else None
            ),
            quantsmith_lock=arguments.quantsmith_lock,
            quantsmith_github_token=(
                os.environ.get(arguments.quantsmith_github_token_env)
                if arguments.quantsmith_source == "github"
                else None
            ),
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
    if arguments.quantsmith_source == "local":
        print(f"QuantSmith reference: local checkout {arguments.quantsmith_checkout}")
    elif arguments.quantsmith_source == "github":
        print("QuantSmith reference: GitHub API at the pinned commit")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
