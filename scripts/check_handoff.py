#!/usr/bin/env python3
"""Keep the master project handoff synchronized with staged and committed work."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

HANDOFF = "docs/handoff.md"
START = "<!-- finassert-handoff-checkpoint:v1 -->"
END = "<!-- /finassert-handoff-checkpoint -->"
OID = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
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
    args = parser.parse_args()
    try:
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
        print(f"Master handoff check failed: {error}\n{RECOVERY}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
