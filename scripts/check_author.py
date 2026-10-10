#!/usr/bin/env python3
"""Enforce the repository's configurable Git author identity policy."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class Author:
    """A Git author identity."""

    name: str
    email: str
    commit: str | None = None

    @property
    def display(self) -> str:
        """Return the conventional Git identity representation."""
        return f"{self.name} <{self.email}>"


@dataclass(frozen=True, slots=True)
class Policy:
    """Allowed identities and prohibited identity patterns."""

    allowed_authors: frozenset[tuple[str, str]]
    blocked_patterns: tuple[re.Pattern[str], ...]


def load_policy(path: Path) -> Policy:
    """Load and validate an author policy from TOML."""
    try:
        raw: dict[str, Any] = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise ValueError(f"could not read policy {path}: {exc}") from exc

    raw_authors = raw.get("allowed_authors")
    raw_patterns = raw.get("blocked_identity_patterns")
    if not isinstance(raw_authors, list) or not raw_authors:
        raise ValueError("allowed_authors must be a non-empty array of author tables")
    if not isinstance(raw_patterns, list) or not raw_patterns:
        raise ValueError("blocked_identity_patterns must be a non-empty array of strings")

    allowed: set[tuple[str, str]] = set()
    for item in raw_authors:
        if not isinstance(item, dict):
            raise ValueError("each allowed author must be a table with name and email")
        name = item.get("name")
        email = item.get("email")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("each allowed author requires a non-empty name")
        if not isinstance(email, str) or not email.strip():
            raise ValueError("each allowed author requires a non-empty email")
        allowed.add((name, email.casefold()))

    patterns: list[re.Pattern[str]] = []
    for pattern in raw_patterns:
        if not isinstance(pattern, str) or not pattern:
            raise ValueError("blocked identity patterns must be non-empty strings")
        try:
            patterns.append(re.compile(pattern, re.IGNORECASE))
        except re.error as exc:
            raise ValueError(f"invalid blocked identity pattern {pattern!r}: {exc}") from exc
    return Policy(frozenset(allowed), tuple(patterns))


def current_author() -> Author:
    """Read the effective author Git would use for a new commit."""
    identity = _git("var", "GIT_AUTHOR_IDENT").strip()
    match = re.fullmatch(r"(.*) <([^<>]+)> \d+ [+-]\d{4}", identity)
    if match is None:
        raise ValueError(f"could not parse Git author identity: {identity!r}")
    return Author(name=match.group(1), email=match.group(2))


def history_authors(revision: str) -> list[Author]:
    """Read authors for all commits reachable from ``revision``."""
    output = _git("log", revision, "--format=%H%x00%an%x00%ae")
    authors: list[Author] = []
    for line in output.splitlines():
        commit, name, email = line.split("\0", maxsplit=2)
        authors.append(Author(name=name, email=email, commit=commit))
    if not authors:
        raise ValueError(f"no commits are reachable from {revision!r}")
    return authors


def violations(authors: list[Author], policy: Policy) -> list[str]:
    """Return human-readable policy violations."""
    failures: list[str] = []
    for author in authors:
        location = f"commit {author.commit}" if author.commit else "configured author"
        blocked = next(
            (
                pattern.pattern
                for pattern in policy.blocked_patterns
                if pattern.search(author.display)
            ),
            None,
        )
        if blocked is not None:
            failures.append(f"{location}: {author.display} matches blocked pattern {blocked!r}")
        if (author.name, author.email.casefold()) not in policy.allowed_authors:
            failures.append(f"{location}: {author.display} is not in allowed_authors")
    return failures


def _git(*arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout


def main() -> int:
    """Validate either the effective local author or committed history."""
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--current", action="store_true", help="check the effective local author")
    mode.add_argument(
        "--history", metavar="REVISION", help="check history reachable from a revision"
    )
    parser.add_argument("--policy", type=Path, default=Path(".author-policy.toml"))
    arguments = parser.parse_args()

    try:
        policy = load_policy(arguments.policy)
        authors = history_authors(arguments.history) if arguments.history else [current_author()]
        failures = violations(authors, policy)
    except (ValueError, subprocess.CalledProcessError) as exc:
        print(f"author policy error: {exc}", file=sys.stderr)
        return 2

    if failures:
        print("Git author policy failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        print(f"Configure allowed identities in {arguments.policy}.", file=sys.stderr)
        return 1
    print(f"Git author policy passed for {len(authors)} author record(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
