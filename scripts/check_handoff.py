#!/usr/bin/env python3
"""Keep the master project handoff synchronized with staged and committed work."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import uuid
from datetime import UTC, date, datetime
from pathlib import Path

HANDOFF = "docs/handoff.md"
START = "<!-- finassert-handoff-checkpoint:v1 -->"
END = "<!-- /finassert-handoff-checkpoint -->"
FILESYSTEM_CONTEXT = "Filesystem checkpoint context"
FILESYSTEM_START = "<!-- finassert-filesystem-checkpoint:v1 -->"
FILESYSTEM_END = "<!-- /finassert-filesystem-checkpoint -->"
FILESYSTEM_STATE_DIR = ".finassert-handoff"
FILESYSTEM_STATE_FILE = "state.json"
FILESYSTEM_VERSION = 1
FILESYSTEM_DEFAULT_EXCLUDES = (
    ".git/**",
    ".hg/**",
    ".svn/**",
    ".venv/**",
    "venv/**",
    "__pycache__/**",
    "**/__pycache__/**",
    ".pytest_cache/**",
    ".mypy_cache/**",
    ".ruff_cache/**",
    "build/**",
    "dist/**",
    "site/**",
    "node_modules/**",
)
OID = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
FIELDS = {
    "Last worked on": "Worked on",
    "Stopping point": "Stopping point",
    "Highest priority": "Priorities",
    "Next pickup": "Next pickup",
    "Verification": "Verification",
}
RECOVERY = (
    "Update docs/handoff.md Current state and Next up; prepend a complete dated entry.\n"
    "Stage intended changes, run python3 scripts/check_handoff.py --refresh,\n"
    "then git add -- docs/handoff.md and retry. Historical entries must stay unchanged."
)
FILESYSTEM_RECOVERY = (
    "Use --filesystem-check to inspect the current checkpoint. If the saved filesystem "
    "baseline is missing or damaged, review the project and run --filesystem-recover "
    "--confirm-filesystem-recovery. Recovery starts a new local baseline; it does not "
    "verify or recreate prior filesystem history."
)


class HandoffError(ValueError):
    """An incomplete, stale or inconsistent checkpoint."""


class Repository:
    """Read Git objects and the index independently of unstaged working files."""

    def __init__(self) -> None:
        self.root = Path.cwd()
        self.root = Path(self.git("rev-parse", "--show-toplevel").decode().strip())

    def git(self, *args: str) -> bytes:
        """Run a read-only Git command at the repository root."""
        result = subprocess.run(
            ["git", "-C", str(self.root), *args], check=True, capture_output=True
        )
        return result.stdout

    def resolve(self, ref: str) -> str | None:
        """Resolve an available commit, including an annotated tag."""
        try:
            return (
                self.git("rev-parse", "--verify", "--end-of-options", f"{ref}^{{commit}}")
                .decode()
                .strip()
            )
        except subprocess.CalledProcessError:
            return None

    def document(self, revision: str) -> str:
        """Read the handoff blob from a tree or the index."""
        try:
            return self.git("show", f"{revision}:{HANDOFF}").decode("utf-8")
        except subprocess.CalledProcessError:
            return ""

    def parents(self, revision: str) -> list[str]:
        """Return a commit's ordered parent IDs."""
        return self.git("show", "-s", "--format=%P", revision).decode().split()

    def paths(self, base: str | None, tip: str | None = None) -> list[str]:
        """Return changed paths with renames represented as deletion/addition."""
        if tip is None:
            output = self.git("diff", "--cached", "--name-only", "--no-renames", "-z")
        elif base:
            output = self.git("diff", "--name-only", "--no-renames", "-z", base, tip)
        else:
            output = self.git(
                "diff-tree",
                "--root",
                "--no-commit-id",
                "--name-only",
                "--no-renames",
                "-r",
                "-z",
                tip,
            )
        return sorted(p.decode("utf-8", "surrogateescape") for p in output.split(b"\0") if p)

    def manifest_digest(self, revision: str | None = None) -> str:
        """Hash tracked path/mode/blob identity, excluding the self-referential master."""
        records: list[bytes] = []
        if revision:
            raw = self.git("ls-tree", "-r", "-z", revision)
            for item in raw.split(b"\0"):
                if item:
                    meta, path = item.split(b"\t", 1)
                    mode, _, oid = meta.split()
                    if path != HANDOFF.encode():
                        records.append(mode + b" " + oid + b"\t" + path + b"\0")
        else:
            head = self.resolve("HEAD")
            tracked = set()
            if head:
                tracked = set(self.git("ls-tree", "-r", "--name-only", "-z", head).split(b"\0"))
            changed = {p.encode("utf-8", "surrogateescape") for p in self.paths(head)}
            for item in self.git("ls-files", "--stage", "-z").split(b"\0"):
                if item:
                    meta, path = item.split(b"\t", 1)
                    mode, oid, stage = meta.split()
                    if stage != b"0":
                        raise HandoffError(
                            "Resolve and stage index conflicts before checkpointing."
                        )
                    # Intent-to-add files are not part of a commit until actually staged.
                    if path != HANDOFF.encode() and (path in tracked or path in changed):
                        records.append(mode + b" " + oid + b"\t" + path + b"\0")
        return hashlib.sha256(b"".join(sorted(records))).hexdigest()

    def recent(self, parent: str | None) -> list[dict[str, str]]:
        """Read up to five actual first-parent commits preceding a checkpoint."""
        if not parent:
            return []
        raw = self.git("log", "-5", "--first-parent", "--format=%H%x00%s", parent)
        return [
            dict(zip(("commit", "subject"), line.split("\0", 1), strict=True))
            for line in raw.decode("utf-8", "replace").splitlines()
        ]


def sections(document: str) -> dict[str, tuple[int, int, str]]:
    """Find unique level-two sections outside fenced examples."""
    headings: list[tuple[str, int, int]] = []
    position = 0
    fence = ""
    for line in document.splitlines(keepends=True):
        stripped = line.lstrip()
        if stripped.startswith(("```", "~~~")):
            token = stripped[:3]
            if not fence:
                fence = token
            elif token == fence:
                fence = ""
        elif not fence and line.startswith("## "):
            headings.append((line[3:].strip(), position, position + len(line)))
        position += len(line)
    result = {}
    for index, (title, start, body) in enumerate(headings):
        if title in result:
            raise HandoffError(f"Duplicate master section: {title}.")
        end = headings[index + 1][1] if index + 1 < len(headings) else len(document)
        result[title] = (start, end, document[body:end])
    return result


def meaningful(value: str, label: str) -> None:
    """Reject missing text and unfilled template values."""
    value = re.sub(r"[`*_]", "", value).strip()
    if not value or re.fullmatch(
        r"(?:todo|tbd|pending|n/?a|none|\.\.\.|<[^>]*>)[.!]?", value, re.IGNORECASE
    ):
        raise HandoffError(f"Fill in {label}; placeholders are not a checkpoint.")


def fields(body: str) -> dict[str, str]:
    """Read named Markdown bullets with wrapped continuation lines."""
    result: dict[str, str] = {}
    current = None
    for line in body.splitlines():
        match = re.match(r"^- \*\*([^*]+):\*\*\s*(.*)$", line)
        if match:
            current, value = match.groups()
            if current in result:
                raise HandoffError(f"Duplicate checkpoint field: {current}.")
            result[current] = value.strip()
        elif line.startswith(("- ", "#")):
            current = None
        elif current and line.strip():
            result[current] += " " + line.strip()
    return result


def entry(body: str) -> str:
    """Return the newest dated entry without the older historical suffix."""
    body = body.lstrip("\n")
    heading = re.match(r"### (\d{4}-\d{2}-\d{2}) [\u2014\u2013-] (.+)\n", body)
    if not heading:
        raise HandoffError("Prepend a dated ### YYYY-MM-DD — title entry under Entries.")
    try:
        date.fromisoformat(heading[1])
    except ValueError as error:
        raise HandoffError("The newest handoff entry needs a valid ISO date.") from error
    meaningful(heading[2], "entry title")
    return re.split(r"(?m)\n(?=### )", body, maxsplit=1)[0]


def review(document: str, previous: str = "") -> tuple[dict[str, tuple[int, int, str]], str]:
    """Validate human-owned state, priority, pickup and immutable entry history."""
    parts = sections(document)
    for title in ("Current state", "Next up", "Entries"):
        if title not in parts:
            raise HandoffError(f"The master is missing ## {title}.")
    newest = entry(parts["Entries"][2])
    current, latest = fields(parts["Current state"][2]), fields(newest)
    for state_name, entry_name in FIELDS.items():
        meaningful(current.get(state_name, ""), f"Current state / {state_name}")
        meaningful(latest.get(entry_name, ""), f"newest entry / {entry_name}")
        if current[state_name] != latest[entry_name]:
            raise HandoffError(
                f"Current state / {state_name} must match newest entry / {entry_name}."
            )
    priorities = re.findall(r"(?m)^(\d+)\. (.*)$", parts["Next up"][2])
    if not priorities or [int(n) for n, _ in priorities] != list(range(1, len(priorities) + 1)):
        raise HandoffError("Next up must contain a sequential priority list starting at 1.")
    for _, title in priorities:
        meaningful(title, "priority title")
    if priorities[0][1].strip() != current["Highest priority"]:
        raise HandoffError("Next up item 1 must match Current state / Highest priority.")
    if previous:
        old = sections(previous).get("Entries")
        if old and old[2].lstrip("\n"):
            history = old[2].lstrip("\n")
            updated = parts["Entries"][2].lstrip("\n")
            if not updated.endswith(history) or updated == history:
                raise HandoffError("Prepend a new entry; preserve historical Entries verbatim.")
            # The new entry must be new text, not a duplicate copy of the last one.
            if newest.strip() in history:
                raise HandoffError(
                    "The newest entry duplicates history; record the actual new work."
                )
    return parts, newest


def review_digest(parts: dict[str, tuple[int, int, str]], newest: str) -> str:
    """Identify the exact human-reviewed sections outside generated Git context."""
    text = parts["Current state"][2] + "\0" + parts["Next up"][2] + "\0" + newest
    return hashlib.sha256(text.encode()).hexdigest()


def context_block(context: dict[str, object]) -> str:
    """Render the generated context as inspectable Markdown/JSON."""
    return (
        "## Commit context\n\n"
        "This checkpoint is the enclosing Git commit. Recent commits below precede it;\n"
        "use `git log -5 --oneline` for the live tip. Regenerate with --refresh.\n\n"
        + START
        + "\n```json\n"
        + json.dumps(context, indent=2, ensure_ascii=True)
        + "\n```\n"
        + END
        + "\n\n"
    )


def refresh(repo: Repository) -> None:
    """Update only generated Git context; require explicit staging by the contributor."""
    path = repo.root / HANDOFF
    staged = repo.document("")
    if not staged or path.read_text(encoding="utf-8") != staged:
        raise HandoffError(
            "Stage your master handoff prose first; --refresh never stages "
            "or overwrites unstaged edits."
        )
    parent = repo.resolve("HEAD")
    parts, newest = review(staged, repo.document(parent) if parent else "")
    changed = repo.paths(parent)
    if HANDOFF not in changed:
        raise HandoffError("Stage a new master checkpoint before refreshing Git context.")
    context = {
        "version": 1,
        "prior_head": parent,
        "recent_commits": repo.recent(parent),
        "changed_paths": changed,
        "project_sha256": repo.manifest_digest(),
        "reviewed_sections_sha256": review_digest(parts, newest),
    }
    block = context_block(context)
    if "Commit context" in parts:
        start, end, _ = parts["Commit context"]
        updated = staged[:start] + block + staged[end:]
    else:
        position = parts.get("Entry template", parts["Entries"])[0]
        updated = staged[:position] + block + staged[position:]
    path.write_text(updated, encoding="utf-8")
    print("Refreshed Git context only. Now git add -- docs/handoff.md, then commit.")


def validate(repo: Repository, revision: str | None = None) -> None:
    """Check the staged snapshot or one committed checkpoint against its parent."""
    parents = repo.parents(revision) if revision else []
    parent = (parents[0] if parents else None) if revision else repo.resolve("HEAD")
    changed = repo.paths(parent, revision)
    document = repo.document(revision or "")
    previous = repo.document(parent) if parent else ""
    if revision and START not in document and not any(START in repo.document(p) for p in parents):
        return  # Historical commits before policy activation.
    if not changed:
        return
    if HANDOFF not in changed:
        raise HandoffError("Project changes require docs/handoff.md in the same commit.")
    if document.count(START) != 1 or document.count(END) != 1:
        raise HandoffError("Master checkpoint Git context is missing, removed or duplicated.")
    parts, newest = review(document, previous)
    body = parts.get("Commit context", (0, 0, ""))[2]
    match = re.fullmatch(
        r".*?" + re.escape(START) + r"\n```json\n(.*?)\n```\n" + re.escape(END) + r"\s*",
        body,
        re.DOTALL,
    )
    if not match:
        raise HandoffError("Commit context must contain its generated JSON block.")
    try:
        context = json.loads(match[1])
    except json.JSONDecodeError as error:
        raise HandoffError("Commit context contains invalid JSON; refresh it.") from error
    keys = {
        "version",
        "prior_head",
        "recent_commits",
        "changed_paths",
        "project_sha256",
        "reviewed_sections_sha256",
    }
    if (
        not isinstance(context, dict)
        or set(context) != keys
        or type(context["version"]) is not int
        or context["version"] != 1
    ):
        raise HandoffError("Unknown or incomplete Commit context schema; refresh it.")
    anchor = context["prior_head"]
    if anchor is not None and (not isinstance(anchor, str) or not OID.fullmatch(anchor)):
        raise HandoffError("Invalid prior HEAD in Commit context.")
    if not revision and anchor != parent:
        raise HandoffError("Commit context predates HEAD; refresh it after the latest commit.")
    available = anchor is None or repo.resolve(anchor) is not None
    if available:
        if context["recent_commits"] != repo.recent(anchor):
            raise HandoffError("Recent commit IDs/subjects do not match Git; refresh context.")
        if context["changed_paths"] != repo.paths(anchor, revision):
            raise HandoffError(
                "Staged/committed paths changed after refresh; refresh context again."
            )
    else:
        # A server squash can retain an authored checkpoint after its source ref is deleted.
        recent = context["recent_commits"]
        if (
            not isinstance(recent, list)
            or not 1 <= len(recent) <= 5
            or any(
                not isinstance(c, dict)
                or set(c) != {"commit", "subject"}
                or not isinstance(c["commit"], str)
                or not OID.fullmatch(c["commit"])
                or not isinstance(c["subject"], str)
                for c in recent
            )
            or recent[0]["commit"] != anchor
        ):
            raise HandoffError("Invalid archived recent commit context.")
        paths = context["changed_paths"]
        if (
            not isinstance(paths, list)
            or not all(isinstance(p, str) for p in paths)
            or paths != sorted(set(paths))
            or HANDOFF not in paths
        ):
            raise HandoffError("Invalid archived changed-path context.")
    if context["project_sha256"] != repo.manifest_digest(revision):
        raise HandoffError("Project snapshot changed after checkpoint refresh.")
    if context["reviewed_sections_sha256"] != review_digest(parts, newest):
        raise HandoffError("Handoff prose changed after refresh; review and refresh context.")


def check_range(repo: Repository, base: str | None, tip: str) -> int:
    """Validate every outgoing commit, including bypassed intermediate commits."""
    resolved = repo.resolve(tip)
    if not resolved:
        raise HandoffError(f"Cannot resolve branch tip {tip}.")
    if START not in repo.document(resolved):
        raise HandoffError("The branch tip has no active master checkpoint.")
    resolved_base = repo.resolve(base) if base else None
    if base and set(base) != {"0"} and not resolved_base:
        raise HandoffError(
            "Fetch the remote/base commit before checking this update; its handoff is unknown."
        )
    if resolved_base:
        old = sections(repo.document(resolved_base)).get("Entries")
        new = sections(repo.document(resolved)).get("Entries")
        if (
            old
            and old[2].lstrip("\n")
            and (not new or not new[2].lstrip("\n").endswith(old[2].lstrip("\n")))
        ):
            raise HandoffError(
                "Branch update drops remote/base handoff history; merge its checkpoint first."
            )
    selection = f"{resolved_base}..{resolved}" if resolved_base else resolved
    commits = repo.git("rev-list", "--reverse", "--topo-order", selection).decode().split()
    for commit in commits:
        try:
            validate(repo, commit)
        except HandoffError as error:
            raise HandoffError(f"Commit {commit[:12]}: {error}") from error
    return len(commits)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True)


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _valid_timestamp(value: object) -> bool:
    if not isinstance(value, str) or not value.endswith("Z"):
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def _filesystem_id() -> str:
    return "fs-" + uuid.uuid4().hex


def _valid_filesystem_id(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"fs-[0-9a-f]{32}", value) is not None


def _valid_sha256(value: object) -> bool:
    return isinstance(value, str) and SHA256.fullmatch(value) is not None


class FilesystemRepository:
    """Snapshot project files and retain one explicit local checkpoint baseline."""

    def __init__(self, root: Path, state_dir: Path) -> None:
        self.root = root.resolve()
        if not self.root.is_dir():
            raise HandoffError(f"Filesystem root is not a directory: {self.root}")
        candidate = state_dir if state_dir.is_absolute() else self.root / state_dir
        self.state_dir = candidate.resolve()
        try:
            self.state_rel = self.state_dir.relative_to(self.root).as_posix()
        except ValueError as error:
            message = "Filesystem state directory must be inside the project root."
            raise HandoffError(message) from error
        if self.state_rel in {"", "."}:
            raise HandoffError("Filesystem state directory cannot be the project root.")
        self.state_path = self.state_dir / FILESYSTEM_STATE_FILE

    @property
    def handoff_path(self) -> Path:
        """Return the canonical master-handoff path in this project."""
        return self.root / HANDOFF

    def handoff(self) -> str:
        """Read the canonical master handoff without using Git."""
        try:
            return self.handoff_path.read_text(encoding="utf-8")
        except FileNotFoundError as error:
            raise HandoffError(f"Filesystem mode requires {HANDOFF}.") from error

    def _matches(self, path: str, pattern: str) -> bool:
        prefix = pattern.removesuffix("/**")
        return fnmatch.fnmatchcase(path, pattern) or (
            pattern.endswith("/**") and (path == prefix or path.startswith(prefix + "/"))
        )

    def _tracked(self, path: str, config: dict[str, object]) -> bool:
        if path == HANDOFF:
            return True
        include = config["include"]
        exclude = config["exclude"]
        assert isinstance(include, list) and isinstance(exclude, list)
        return any(self._matches(path, rule) for rule in include) and not any(
            self._matches(path, rule) for rule in exclude
        )

    def _excluded_directory(self, path: str, config: dict[str, object]) -> bool:
        exclude = config["exclude"]
        assert isinstance(exclude, list)
        return any(self._matches(path, rule) for rule in exclude)

    @staticmethod
    def _file_hash(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as source:
            for block in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()

    @staticmethod
    def _link_hash(path: Path) -> str:
        target = os.readlink(path)
        return hashlib.sha256(b"symlink\0" + os.fsencode(target)).hexdigest()

    def snapshot(self, config: dict[str, object]) -> list[dict[str, str]]:
        """Return a deterministic, configured content snapshot without following links."""
        files: list[dict[str, str]] = []
        for directory, directories, names in os.walk(self.root, followlinks=False):
            base = Path(directory)
            retained_directories: list[str] = []
            for name in sorted(directories):
                path = base / name
                relative = path.relative_to(self.root).as_posix()
                if path.is_symlink():
                    if self._tracked(relative, config):
                        files.append(
                            {"path": relative, "kind": "symlink", "sha256": self._link_hash(path)}
                        )
                elif not self._excluded_directory(relative, config):
                    retained_directories.append(name)
            directories[:] = retained_directories
            for name in sorted(names):
                path = base / name
                relative = path.relative_to(self.root).as_posix()
                if not self._tracked(relative, config):
                    continue
                if path.is_symlink():
                    files.append(
                        {"path": relative, "kind": "symlink", "sha256": self._link_hash(path)}
                    )
                elif path.is_file():
                    files.append(
                        {"path": relative, "kind": "file", "sha256": self._file_hash(path)}
                    )
                else:
                    raise HandoffError(f"Unsupported filesystem entry in checkpoint: {relative}")
        return sorted(files, key=lambda item: item["path"])

    @staticmethod
    def project_digest(files: list[dict[str, str]]) -> str:
        """Hash the configured project snapshot without the self-referential handoff."""
        records = [
            f"{item['kind']} {item['sha256']}\t{item['path']}\0".encode()
            for item in files
            if item["path"] != HANDOFF
        ]
        return hashlib.sha256(b"".join(records)).hexdigest()

    @staticmethod
    def changed_paths(baseline: list[dict[str, str]], current: list[dict[str, str]]) -> list[str]:
        """Return deterministic added, changed and deleted paths."""
        before = {item["path"]: (item["kind"], item["sha256"]) for item in baseline}
        after = {item["path"]: (item["kind"], item["sha256"]) for item in current}
        candidates = set(before) | set(after)
        return sorted(path for path in candidates if before.get(path) != after.get(path))

    def atomic_write(self, path: Path, value: str) -> None:
        """Replace a generated state or context file atomically."""
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as destination:
                destination.write(value)
                destination.flush()
                os.fsync(destination.fileno())
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def write_state(self, state: dict[str, object]) -> None:
        """Persist the complete accepted baseline in one atomic state file."""
        self.atomic_write(self.state_path, json.dumps(state, indent=2, ensure_ascii=True) + "\n")

    def load_state(self) -> dict[str, object]:
        """Read and validate the previously accepted local baseline."""
        try:
            raw = self.state_path.read_text(encoding="utf-8")
        except FileNotFoundError as error:
            raise HandoffError("Filesystem checkpoint baseline is missing or damaged.") from error
        try:
            state = json.loads(raw)
        except json.JSONDecodeError as error:
            raise HandoffError("Filesystem checkpoint baseline is damaged.") from error
        if not isinstance(state, dict) or set(state) != {"version", "mode", "config", "baseline"}:
            raise HandoffError("Filesystem checkpoint baseline has an incompatible schema.")
        if state["version"] != FILESYSTEM_VERSION or state["mode"] != "filesystem":
            raise HandoffError(
                "Filesystem checkpoint baseline has an incompatible version or mode."
            )
        config = state["config"]
        baseline = state["baseline"]
        if not isinstance(config, dict) or set(config) != {"version", "include", "exclude"}:
            raise HandoffError("Filesystem checkpoint configuration is damaged.")
        if config["version"] != FILESYSTEM_VERSION or not all(
            isinstance(value, list) and value and all(isinstance(item, str) for item in value)
            for value in (config["include"], config["exclude"])
        ):
            raise HandoffError("Filesystem checkpoint configuration is invalid.")
        expected_baseline = {
            "checkpoint_id",
            "accepted_at",
            "project_sha256",
            "handoff_sha256",
            "files",
            "handoff",
        }
        if not isinstance(baseline, dict) or set(baseline) != expected_baseline:
            raise HandoffError("Filesystem checkpoint baseline is damaged.")
        if not _valid_filesystem_id(baseline["checkpoint_id"]) or not _valid_timestamp(
            baseline["accepted_at"]
        ):
            raise HandoffError("Filesystem checkpoint baseline identity is invalid.")
        if not _valid_sha256(baseline["project_sha256"]) or not _valid_sha256(
            baseline["handoff_sha256"]
        ):
            raise HandoffError("Filesystem checkpoint baseline digest is invalid.")
        handoff = baseline["handoff"]
        if not isinstance(handoff, str) or _sha256_text(handoff) != baseline["handoff_sha256"]:
            raise HandoffError("Filesystem checkpoint handoff snapshot is damaged.")
        files = baseline["files"]
        if not isinstance(files, list) or not all(isinstance(item, dict) for item in files):
            raise HandoffError("Filesystem checkpoint file snapshot is invalid.")
        if files != sorted(files, key=lambda item: item.get("path", "")):
            raise HandoffError("Filesystem checkpoint file snapshot is invalid.")
        seen: set[str] = set()
        for item in files:
            if (
                not isinstance(item, dict)
                or set(item) != {"path", "kind", "sha256"}
                or not isinstance(item["path"], str)
                or not item["path"]
                or item["path"].startswith("/")
                or ".." in Path(item["path"]).parts
                or item["kind"] not in {"file", "symlink"}
                or not _valid_sha256(item["sha256"])
                or item["path"] in seen
            ):
                raise HandoffError("Filesystem checkpoint file snapshot is invalid.")
            seen.add(item["path"])
        if self.project_digest(files) != baseline["project_sha256"]:
            raise HandoffError("Filesystem checkpoint project digest is inconsistent.")
        return state


def _filesystem_patterns(values: list[str] | None, defaults: tuple[str, ...]) -> list[str]:
    patterns = list(defaults if values is None else values)
    if not patterns:
        raise HandoffError("Filesystem include/exclude rules cannot be empty.")
    normalized: list[str] = []
    for pattern in patterns:
        if not pattern or pattern.startswith("/") or "\\" in pattern or ".." in Path(pattern).parts:
            raise HandoffError(f"Invalid filesystem include/exclude rule: {pattern!r}")
        if pattern not in normalized:
            normalized.append(pattern)
    return normalized


def _filesystem_config(repo: FilesystemRepository, args: argparse.Namespace) -> dict[str, object]:
    include = _filesystem_patterns(args.filesystem_include, ("**",))
    exclude = _filesystem_patterns(args.filesystem_exclude, FILESYSTEM_DEFAULT_EXCLUDES)
    state_rule = repo.state_rel + "/**"
    if state_rule not in exclude:
        exclude.append(state_rule)
    return {"version": FILESYSTEM_VERSION, "include": include, "exclude": exclude}


def _filesystem_config_digest(config: dict[str, object]) -> str:
    return hashlib.sha256(_canonical_json(config).encode("utf-8")).hexdigest()


def _filesystem_context_block(context: dict[str, object]) -> str:
    return (
        f"## {FILESYSTEM_CONTEXT}\n\n"
        "This machine-owned context records a local filesystem checkpoint. It is not "
        "a Git commit, push or CI result. Regenerate it with --filesystem-refresh-context.\n\n"
        + FILESYSTEM_START
        + "\n```json\n"
        + json.dumps(context, indent=2, ensure_ascii=True)
        + "\n```\n"
        + FILESYSTEM_END
        + "\n\n"
    )


def _replace_context(document: str, title: str, block: str) -> str:
    parts = sections(document)
    if title in parts:
        start, end, _ = parts[title]
        return document[:start] + block + document[end:]
    position = parts.get("Entry template", parts["Entries"])[0]
    return document[:position] + block + document[position:]


def _filesystem_context(document: str) -> dict[str, object]:
    parts = sections(document)
    body = parts.get(FILESYSTEM_CONTEXT, (0, 0, ""))[2]
    if body.count(FILESYSTEM_START) != 1 or body.count(FILESYSTEM_END) != 1:
        raise HandoffError("Filesystem checkpoint context is missing, removed or duplicated.")
    match = re.fullmatch(
        r".*?"
        + re.escape(FILESYSTEM_START)
        + r"\n```json\n(.*?)\n```\n"
        + re.escape(FILESYSTEM_END)
        + r"\s*",
        body,
        re.DOTALL,
    )
    if not match:
        raise HandoffError("Filesystem checkpoint context must contain its generated JSON block.")
    try:
        context = json.loads(match[1])
    except json.JSONDecodeError as error:
        raise HandoffError("Filesystem checkpoint context contains invalid JSON.") from error
    expected = {
        "version",
        "mode",
        "checkpoint_id",
        "baseline_id",
        "generated_at",
        "changed_paths",
        "project_sha256",
        "reviewed_sections_sha256",
        "config_sha256",
    }
    if not isinstance(context, dict) or set(context) != expected:
        raise HandoffError("Filesystem checkpoint context has an incomplete schema.")
    return context


def _validate_filesystem_context(
    context: dict[str, object],
    state: dict[str, object],
    snapshot: list[dict[str, str]],
    changes: list[str],
    reviewed: str,
) -> None:
    baseline = state["baseline"]
    config = state["config"]
    assert isinstance(baseline, dict) and isinstance(config, dict)
    if context["version"] != FILESYSTEM_VERSION or context["mode"] != "filesystem":
        raise HandoffError("Filesystem checkpoint context has an incompatible version or mode.")
    if not _valid_filesystem_id(context["checkpoint_id"]) or not _valid_filesystem_id(
        context["baseline_id"]
    ):
        raise HandoffError("Filesystem checkpoint context has an invalid checkpoint identity.")
    if (
        context["checkpoint_id"] == baseline["checkpoint_id"]
        or context["baseline_id"] != baseline["checkpoint_id"]
    ):
        raise HandoffError("Filesystem checkpoint context does not match the accepted baseline.")
    if not _valid_timestamp(context["generated_at"]):
        raise HandoffError("Filesystem checkpoint context has an invalid timestamp.")
    if context["changed_paths"] != changes or not all(
        isinstance(path, str) for path in context["changed_paths"]
    ):
        raise HandoffError(
            "Filesystem checkpoint context is stale; refresh it after project changes."
        )
    if context["project_sha256"] != FilesystemRepository.project_digest(snapshot):
        raise HandoffError("Filesystem project snapshot changed after context refresh.")
    if context["reviewed_sections_sha256"] != reviewed:
        raise HandoffError("Filesystem handoff prose changed after context refresh.")
    if context["config_sha256"] != _filesystem_config_digest(config):
        raise HandoffError("Filesystem checkpoint configuration changed after context refresh.")


def _filesystem_inspect(
    repo: FilesystemRepository,
) -> tuple[dict[str, object], list[dict[str, str]], list[str], str, dict[str, object] | None]:
    state = repo.load_state()
    config = state["config"]
    baseline = state["baseline"]
    assert isinstance(config, dict) and isinstance(baseline, dict)
    snapshot = repo.snapshot(config)
    changes = repo.changed_paths(baseline["files"], snapshot)
    handoff = repo.handoff()
    if not changes:
        return state, snapshot, changes, handoff, None
    if HANDOFF not in changes:
        raise HandoffError(
            "Filesystem project changes require an updated docs/handoff.md checkpoint."
        )
    parts, newest = review(handoff, baseline["handoff"])
    context = _filesystem_context(handoff)
    _validate_filesystem_context(context, state, snapshot, changes, review_digest(parts, newest))
    return state, snapshot, changes, handoff, context


def _filesystem_state(
    config: dict[str, object], snapshot: list[dict[str, str]], handoff: str, checkpoint_id: str
) -> dict[str, object]:
    return {
        "version": FILESYSTEM_VERSION,
        "mode": "filesystem",
        "config": config,
        "baseline": {
            "checkpoint_id": checkpoint_id,
            "accepted_at": _utc_now(),
            "project_sha256": FilesystemRepository.project_digest(snapshot),
            "handoff_sha256": _sha256_text(handoff),
            "files": snapshot,
            "handoff": handoff,
        },
    }


def filesystem_init(
    repo: FilesystemRepository, args: argparse.Namespace, *, recover: bool = False
) -> None:
    """Create a reviewed initial baseline, or explicitly replace damaged state."""
    if repo.state_dir.exists() and not recover:
        raise HandoffError(
            "Filesystem checkpoint state already exists; use --filesystem-check or explicit "
            "recovery."
        )
    handoff = repo.handoff()
    review(handoff)
    config = _filesystem_config(repo, args)
    snapshot = repo.snapshot(config)
    repo.write_state(_filesystem_state(config, snapshot, handoff, _filesystem_id()))
    action = "recovered" if recover else "initialized"
    print(f"Filesystem checkpoint baseline {action}; no Git references were recorded.")


def filesystem_refresh(repo: FilesystemRepository) -> None:
    """Refresh only the generated filesystem context for a pending checkpoint."""
    state = repo.load_state()
    config = state["config"]
    baseline = state["baseline"]
    assert isinstance(config, dict) and isinstance(baseline, dict)
    snapshot = repo.snapshot(config)
    changes = repo.changed_paths(baseline["files"], snapshot)
    if not changes:
        raise HandoffError("No filesystem project changes require a new checkpoint.")
    if HANDOFF not in changes:
        raise HandoffError("Update docs/handoff.md before refreshing filesystem context.")
    handoff = repo.handoff()
    parts, newest = review(handoff, baseline["handoff"])
    context = {
        "version": FILESYSTEM_VERSION,
        "mode": "filesystem",
        "checkpoint_id": _filesystem_id(),
        "baseline_id": baseline["checkpoint_id"],
        "generated_at": _utc_now(),
        "changed_paths": changes,
        "project_sha256": FilesystemRepository.project_digest(snapshot),
        "reviewed_sections_sha256": review_digest(parts, newest),
        "config_sha256": _filesystem_config_digest(config),
    }
    updated = _replace_context(handoff, FILESYSTEM_CONTEXT, _filesystem_context_block(context))
    repo.atomic_write(repo.handoff_path, updated)
    print(
        "Refreshed filesystem context only. Run --filesystem-check, then --filesystem-checkpoint."
    )


def filesystem_check(repo: FilesystemRepository) -> None:
    """Validate the current tree without changing filesystem checkpoint state."""
    _, _, changes, _, _ = _filesystem_inspect(repo)
    if changes:
        print(f"Filesystem handoff check passed ({len(changes)} changed project path(s)).")
    else:
        print("Filesystem handoff check passed (no project changes since the accepted baseline).")


def filesystem_checkpoint(repo: FilesystemRepository) -> None:
    """Accept a fresh, validated filesystem checkpoint as the next baseline."""
    state, snapshot, changes, handoff, context = _filesystem_inspect(repo)
    if not changes or context is None:
        raise HandoffError("No refreshed filesystem checkpoint is pending.")
    latest_snapshot = repo.snapshot(state["config"])
    latest_handoff = repo.handoff()
    if latest_snapshot != snapshot or latest_handoff != handoff:
        raise HandoffError("Project changed while checkpointing; refresh filesystem context again.")
    repo.write_state(
        _filesystem_state(state["config"], snapshot, handoff, context["checkpoint_id"])
    )
    print(f"Accepted filesystem checkpoint {context['checkpoint_id']}; no Git commit was created.")


def main() -> int:
    """Run the repository checkpoint guard or its explicit refresh operation."""
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--staged", action="store_true")
    mode.add_argument("--refresh", action="store_true")
    mode.add_argument("--commit")
    mode.add_argument("--range", nargs=2, metavar=("BASE", "TIP"))
    mode.add_argument("--history", metavar="TIP")
    mode.add_argument("--pre-push", action="store_true")
    mode.add_argument("--filesystem-init", action="store_true")
    mode.add_argument("--filesystem-check", action="store_true")
    mode.add_argument("--filesystem-refresh-context", action="store_true")
    mode.add_argument("--filesystem-checkpoint", action="store_true")
    mode.add_argument("--filesystem-recover", action="store_true")
    parser.add_argument("--filesystem-root", type=Path, default=Path.cwd())
    parser.add_argument("--filesystem-state-dir", type=Path, default=Path(FILESYSTEM_STATE_DIR))
    parser.add_argument("--filesystem-include", action="append")
    parser.add_argument("--filesystem-exclude", action="append")
    parser.add_argument("--confirm-filesystem-recovery", action="store_true")
    args = parser.parse_args()
    filesystem_mode = any(
        (
            args.filesystem_init,
            args.filesystem_check,
            args.filesystem_refresh_context,
            args.filesystem_checkpoint,
            args.filesystem_recover,
        )
    )
    try:
        if filesystem_mode:
            filesystem_repo = FilesystemRepository(args.filesystem_root, args.filesystem_state_dir)
            if (args.filesystem_include or args.filesystem_exclude) and not (
                args.filesystem_init or args.filesystem_recover
            ):
                raise HandoffError(
                    "Set filesystem include/exclude rules only during --filesystem-init or "
                    "recovery."
                )
            if args.filesystem_recover:
                if not args.confirm_filesystem_recovery:
                    raise HandoffError(
                        "Filesystem recovery is explicit; add --confirm-filesystem-recovery."
                    )
                filesystem_init(filesystem_repo, args, recover=True)
            elif args.filesystem_init:
                filesystem_init(filesystem_repo, args)
            elif args.filesystem_check:
                filesystem_check(filesystem_repo)
            elif args.filesystem_refresh_context:
                filesystem_refresh(filesystem_repo)
            else:
                filesystem_checkpoint(filesystem_repo)
            return 0
        if args.confirm_filesystem_recovery or args.filesystem_include or args.filesystem_exclude:
            raise HandoffError("Filesystem options require a --filesystem-* mode.")
        repo = Repository()
        if repo.git("rev-parse", "--is-shallow-repository").strip() == b"true":
            raise HandoffError("Full Git history is required; fetch with git fetch --unshallow.")
        if args.refresh:
            refresh(repo)
            return 0
        if args.pre_push:
            count = 0
            for line in sys.stdin:
                local_ref, local_oid, _, remote_oid = line.split()
                if local_ref.startswith("refs/heads/") and set(local_oid) != {"0"}:
                    count += check_range(repo, remote_oid, local_oid)
            print(f"Master handoff push check passed ({count} commits inspected).")
        elif args.range or args.history:
            base, tip = args.range if args.range else (None, args.history)
            count = check_range(repo, base, tip)
            print(f"Master handoff history check passed ({count} commits inspected).")
        else:
            revision = repo.resolve(args.commit) if args.commit else None
            if args.commit and not revision:
                raise HandoffError(f"Cannot resolve commit {args.commit}.")
            validate(repo, revision)
            print("Master handoff checkpoint passed.")
    except (
        HandoffError,
        OSError,
        UnicodeError,
        subprocess.CalledProcessError,
        ValueError,
    ) as error:
        recovery = FILESYSTEM_RECOVERY if filesystem_mode else RECOVERY
        print(f"Master handoff check failed: {error}\n{recovery}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
