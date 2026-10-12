"""Exceptions raised by finassert."""

from __future__ import annotations

import difflib
from collections.abc import Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from finassert.policy.issues import PolicyIssue

_MAX_LISTED_COLUMNS = 20


class FinassertError(Exception):
    """Base class for library-specific exceptions."""


class ColumnNotFoundError(FinassertError, KeyError):
    """Raised when a rule's configured column is absent.

    Args:
        column: Column the rule asked for.
        available: Columns the dataset offers, when known, used to suggest the
            nearest spelling.
    """

    def __init__(self, column: str, available: Sequence[str] | None = None) -> None:
        super().__init__(column)
        self.column = column
        self.available = None if available is None else tuple(available)

    def __str__(self) -> str:
        message = f"column {self.column!r} was not found"
        if self.available is None:
            return message
        shown = ", ".join(repr(name) for name in self.available[:_MAX_LISTED_COLUMNS])
        if len(self.available) > _MAX_LISTED_COLUMNS:
            shown += ", ..."
        message += f"; available columns: {shown or 'none'}"
        lowered = {name.lower(): name for name in self.available}
        match = lowered.get(self.column.lower()) or next(
            iter(difflib.get_close_matches(self.column, self.available, n=1, cutoff=0.6)), None
        )
        if match is not None:
            message += f"; did you mean {match!r}?"
        return message


class InvalidDataError(FinassertError, ValueError):
    """Raised when input cannot be interpreted as tabular data."""


class RuleEvaluationError(FinassertError):
    """Raised in strict mode when a rule cannot be evaluated."""


class GroupAggregationError(FinassertError, ValueError):
    """Raised when values cannot satisfy a configured group aggregation."""


class PolicyError(FinassertError, ValueError):
    """Raised when a validation policy cannot be loaded or resolved.

    Attributes:
        issues: Every problem found, in document order.
    """

    def __init__(self, issues: tuple[PolicyIssue, ...]) -> None:
        self.issues = issues
        lines = "\n".join(f"- {issue}" for issue in issues)
        super().__init__(f"Policy has {len(issues)} problem(s):\n{lines}")
