"""Human-oriented policy diagnostics."""

from __future__ import annotations

import difflib
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

PolicyPath = tuple[str | int, ...]


@dataclass(frozen=True, slots=True)
class PolicyIssue:
    """One problem in a policy document.

    Args:
        path: Keys and list positions leading to the problem; empty for the
            whole document.
        message: Plain-language description of what is wrong.
        line: One-based source line, when the source format records lines.
        suggestion: Nearest valid spelling, offered but never applied.
    """

    path: PolicyPath
    message: str
    line: int | None = None
    suggestion: str | None = None

    @property
    def location(self) -> str:
        """Return a readable path such as ``rules[2].tolerance``."""
        text = ""
        for part in self.path:
            if isinstance(part, int):
                text += f"[{part + 1}]"
            else:
                text += f".{part}" if text else part
        return text or "policy"

    def __str__(self) -> str:
        prefix = f"line {self.line}, " if self.line is not None else ""
        hint = f" Did you mean {self.suggestion!r}?" if self.suggestion else ""
        return f"{prefix}{self.location}: {self.message}{hint}"

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible description."""
        return {
            "location": self.location,
            "line": self.line,
            "message": self.message,
            "suggestion": self.suggestion,
            "text": str(self),
        }


def closest(value: object, candidates: Iterable[str]) -> str | None:
    """Return the closest candidate to ``value`` or ``None`` when nothing is near."""
    if not isinstance(value, str):
        return None
    options = list(candidates)
    lowered = {option.lower(): option for option in options}
    if value.lower() in lowered:
        return lowered[value.lower()]
    matches = difflib.get_close_matches(value, options, n=1, cutoff=0.6)
    return matches[0] if matches else None


def line_for(path: PolicyPath, lines: Mapping[PolicyPath, int] | None) -> int | None:
    """Return the line of ``path`` or of its nearest recorded ancestor."""
    if not lines:
        return None
    for end in range(len(path), -1, -1):
        line = lines.get(path[:end])
        if line is not None:
            return line
    return None
