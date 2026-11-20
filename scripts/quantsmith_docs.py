"""Read allowlisted documents from one pinned QuantSmith Git commit.

The checkout and its objects stay on the local machine. This module does not
fetch from GitHub, execute document content, or copy it into the add-in build.
"""

from __future__ import annotations

import base64
import binascii
import fnmatch
import hashlib
import json
import re
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

MAX_LOCK_BYTES = 16 * 1024
MAX_TREE_BYTES = 8 * 1024 * 1024
MAX_DOCUMENT_BYTES = 256 * 1024
MAX_DOCUMENTS = 5000
_SHA = re.compile(r"[0-9a-f]{40}\Z")
_REPOSITORY = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
_DOC_ID = re.compile(r"[0-9a-f]{64}\Z")
_SAFE_PATTERN = re.compile(r"[A-Za-z0-9_.*?/-]+\Z")


def _read_lock(lockfile: Path) -> tuple[str, str, list[str]]:
    """Return the validated repository, commit, and permitted path patterns."""
    raw = lockfile.read_bytes()
    if len(raw) > MAX_LOCK_BYTES:
        raise ValueError("QuantSmith lockfile is too large")
    try:
        lock = json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise ValueError("QuantSmith lockfile is invalid JSON") from exc
    if not isinstance(lock, dict) or lock.get("version") != 1:
        raise ValueError("QuantSmith lockfile version must be 1")
    repository = lock.get("repository")
    commit = lock.get("commit")
    patterns = lock.get("include")
    if (
        not isinstance(repository, str)
        or not _REPOSITORY.fullmatch(repository)
        or not isinstance(commit, str)
        or not _SHA.fullmatch(commit)
        or not isinstance(patterns, list)
        or not patterns
        or len(patterns) > 32
        or any(not isinstance(item, str) or not _SAFE_PATTERN.fullmatch(item) for item in patterns)
    ):
        raise ValueError("QuantSmith lockfile has invalid source or allowlist")
    return repository, commit, patterns


def _documents_from_entries(
    entries: list[tuple[str, str, int]], patterns: list[str]
) -> dict[str, Document]:
    """Filter bounded Git blob metadata through the reviewed allowlist."""
    documents: dict[str, Document] = {}
    for path, blob_sha, size in entries:
        if not path.endswith((".md", ".yaml", ".yml")):
            continue
        if not any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns):
            continue
        identifier = hashlib.sha256(path.encode("utf-8")).hexdigest()
        documents[identifier] = Document(identifier, path, blob_sha, size)
        if len(documents) > MAX_DOCUMENTS:
            raise ValueError("QuantSmith catalog exceeds the document limit")
    return documents


def _git(checkout: Path, *args: str, timeout: int = 10) -> bytes:
    try:
        result = subprocess.run(
            ["git", "-C", str(checkout), *args],
            check=True,
            capture_output=True,
            timeout=timeout,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise ValueError("the pinned QuantSmith checkout cannot be read") from exc
    return result.stdout


@dataclass(frozen=True)
class Document:
    """A regular, allowlisted Git blob at the pinned commit."""

    id: str
    path: str
    blob_sha: str
    size: int

    def metadata(self, repository: str, commit: str) -> dict[str, Any]:
        """Return bounded catalog metadata with a source link."""
        encoded_path = "/".join(quote(part, safe="") for part in self.path.split("/"))
        return {
            "id": self.id,
            "path": self.path,
            "title": self.path.rsplit("/", 1)[-1],
            "bytes": self.size,
            "source_url": f"https://github.com/{repository}/blob/{commit}/{encoded_path}",
        }


class Catalog:
    """Read-only document catalog backed by a verified local Git object store."""

    def __init__(self, checkout: Path, lockfile: Path) -> None:
        if not checkout.is_dir():
            raise ValueError("QuantSmith checkout is not a directory")
        repository, commit, patterns = _read_lock(lockfile)
        remote = _git(checkout, "remote", "get-url", "origin").decode("utf-8").strip()
        if remote not in {
            f"https://github.com/{repository}",
            f"https://github.com/{repository}.git",
            f"git@github.com:{repository}",
            f"git@github.com:{repository}.git",
        }:
            raise ValueError("QuantSmith checkout origin does not match the lockfile")
        actual = _git(checkout, "rev-parse", "--verify", f"{commit}^{{commit}}").decode().strip()
        if actual != commit:
            raise ValueError("pinned QuantSmith commit is unavailable")
        tree = _git(checkout, "ls-tree", "-r", "-z", "--long", commit)
        if len(tree) > MAX_TREE_BYTES:
            raise ValueError("QuantSmith tree exceeds the listing limit")
        entries: list[tuple[str, str, int]] = []
        for entry in tree.split(b"\0"):
            if not entry:
                continue
            try:
                header, path_bytes = entry.split(b"\t", 1)
                mode, kind, blob_sha, size_text = header.decode("ascii").split()
                path = path_bytes.decode("utf-8")
                size = int(size_text)
            except (ValueError, UnicodeError) as exc:
                raise ValueError("QuantSmith tree contains an invalid entry") from exc
            if (
                mode not in {"100644", "100755"}
                or kind != "blob"
                or not 0 <= size <= MAX_DOCUMENT_BYTES
            ):
                continue
            entries.append((path, blob_sha, size))
        self.checkout = checkout
        self.repository = repository
        self.commit = commit
        self.documents = _documents_from_entries(entries, patterns)

    def listing(self) -> dict[str, Any]:
        """List public metadata for the configured local reader."""
        return {
            "repository": self.repository,
            "commit": self.commit,
            "source": "local",
            "documents": [
                document.metadata(self.repository, self.commit)
                for document in sorted(self.documents.values(), key=lambda item: item.path)
            ],
        }

    def read(self, identifier: str) -> dict[str, Any] | None:
        """Read one catalog document by its opaque ID, if present."""
        if not _DOC_ID.fullmatch(identifier):
            return None
        document = self.documents.get(identifier)
        if document is None:
            return None
        content = _git(self.checkout, "cat-file", "blob", document.blob_sha)
        if len(content) != document.size or len(content) > MAX_DOCUMENT_BYTES:
            raise ValueError("QuantSmith document size changed unexpectedly")
        try:
            text = content.decode("utf-8")
        except UnicodeError as exc:
            raise ValueError("QuantSmith document is not UTF-8") from exc
        return {
            **document.metadata(self.repository, self.commit),
            "commit": self.commit,
            "sha256": hashlib.sha256(content).hexdigest(),
            "content": text,
        }


class GitHubCatalog:
    """Read the same pinned, allowlisted blobs directly from GitHub on demand.

    This mode is deliberately separate from :class:`Catalog`: it is opt-in at
    server startup, uses the exact commit in the lockfile, and has no access to
    workbook data.  Private repositories can use a token supplied only through
    the local process environment.
    """

    def __init__(
        self,
        lockfile: Path,
        token: str | None = None,
        *,
        opener: Callable[..., Any] = urlopen,
        api_base: str = "https://api.github.com",
    ) -> None:
        repository, commit, patterns = _read_lock(lockfile)
        self.repository = repository
        self.commit = commit
        self.token = token
        self._opener = opener
        self._api_base = api_base.rstrip("/")
        payload = self._json(f"/repos/{repository}/git/trees/{commit}?recursive=1", MAX_TREE_BYTES)
        tree = payload.get("tree")
        if payload.get("truncated") or not isinstance(tree, list):
            raise ValueError("GitHub QuantSmith tree is incomplete")
        entries: list[tuple[str, str, int]] = []
        for entry in tree:
            if not isinstance(entry, dict):
                raise ValueError("GitHub QuantSmith tree is invalid")
            path = entry.get("path")
            mode = entry.get("mode")
            kind = entry.get("type")
            blob_sha = entry.get("sha")
            size = entry.get("size")
            if not all((isinstance(path, str), isinstance(blob_sha, str), isinstance(size, int))):
                raise ValueError("GitHub QuantSmith tree is invalid")
            if mode not in {"100644", "100755"} or kind != "blob" or not _SHA.fullmatch(blob_sha):
                continue
            if not 0 <= size <= MAX_DOCUMENT_BYTES:
                continue
            entries.append((path, blob_sha, size))
        self.documents = _documents_from_entries(entries, patterns)

    def _json(self, path: str, maximum: int) -> dict[str, Any]:
        request = Request(
            self._api_base + path,
            headers={
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                **({"Authorization": f"Bearer {self.token}"} if self.token else {}),
            },
        )
        try:
            with self._opener(request, timeout=10) as response:
                raw = response.read(maximum + 1)
        except (HTTPError, URLError, OSError, TimeoutError) as exc:
            raise ValueError("the pinned QuantSmith GitHub source cannot be read") from exc
        if len(raw) > maximum:
            raise ValueError("GitHub QuantSmith response exceeds its limit")
        try:
            payload = json.loads(raw)
        except (ValueError, UnicodeError) as exc:
            raise ValueError("GitHub QuantSmith response is invalid") from exc
        if not isinstance(payload, dict):
            raise ValueError("GitHub QuantSmith response is invalid")
        return payload

    def listing(self) -> dict[str, Any]:
        """List metadata without retrieving any document text."""
        return {
            "repository": self.repository,
            "commit": self.commit,
            "source": "github",
            "documents": [
                document.metadata(self.repository, self.commit)
                for document in sorted(self.documents.values(), key=lambda item: item.path)
            ],
        }

    def read(self, identifier: str) -> dict[str, Any] | None:
        """Retrieve and verify one selected blob from the pinned GitHub tree."""
        if not _DOC_ID.fullmatch(identifier):
            return None
        document = self.documents.get(identifier)
        if document is None:
            return None
        payload = self._json(
            f"/repos/{self.repository}/git/blobs/{document.blob_sha}",
            MAX_DOCUMENT_BYTES * 2,
        )
        content = payload.get("content")
        if payload.get("encoding") != "base64" or not isinstance(content, str):
            raise ValueError("GitHub QuantSmith blob is invalid")
        try:
            raw = base64.b64decode(content, validate=False)
        except (ValueError, binascii.Error) as exc:
            raise ValueError("GitHub QuantSmith blob is invalid") from exc
        blob_sha = hashlib.sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()
        if (
            len(raw) != document.size
            or len(raw) > MAX_DOCUMENT_BYTES
            or blob_sha != document.blob_sha
        ):
            raise ValueError("GitHub QuantSmith blob changed unexpectedly")
        try:
            text = raw.decode("utf-8")
        except UnicodeError as exc:
            raise ValueError("GitHub QuantSmith document is not UTF-8") from exc
        return {
            **document.metadata(self.repository, self.commit),
            "commit": self.commit,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "content": text,
        }
