"""Read allowlisted documents from one pinned QuantSmith Git commit.

The checkout and its objects stay on the local machine. This module does not
fetch from GitHub, execute document content, or copy it into the add-in build.
"""

from __future__ import annotations

import fnmatch
import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote

MAX_LOCK_BYTES = 16 * 1024
MAX_TREE_BYTES = 8 * 1024 * 1024
MAX_DOCUMENT_BYTES = 256 * 1024
MAX_DOCUMENTS = 5000
_SHA = re.compile(r"[0-9a-f]{40}\Z")
_REPOSITORY = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
_DOC_ID = re.compile(r"[0-9a-f]{64}\Z")
_SAFE_PATTERN = re.compile(r"[A-Za-z0-9_.*?/-]+\Z")


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
            or any(
                not isinstance(item, str) or not _SAFE_PATTERN.fullmatch(item) for item in patterns
            )
        ):
            raise ValueError("QuantSmith lockfile has invalid source or allowlist")
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
        documents: dict[str, Document] = {}
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
            if not path.endswith((".md", ".yaml", ".yml")):
                continue
            if not any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns):
                continue
            identifier = hashlib.sha256(path.encode("utf-8")).hexdigest()
            documents[identifier] = Document(identifier, path, blob_sha, size)
            if len(documents) > MAX_DOCUMENTS:
                raise ValueError("QuantSmith catalog exceeds the document limit")
        self.checkout = checkout
        self.repository = repository
        self.commit = commit
        self.documents = documents

    def listing(self) -> dict[str, Any]:
        """List public metadata for the configured local reader."""
        return {
            "repository": self.repository,
            "commit": self.commit,
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
