"""Private, bounded read sharing for consecutive trusted scalar rules."""

from __future__ import annotations

from contextvars import ContextVar, Token
from decimal import Decimal
from sys import modules
from types import TracebackType
from typing import Any, Self


def _plain(value: Any) -> bool:
    # Identity comparisons avoid invoking arbitrary numeric/label overloads.
    kind = type(value)
    return (
        kind is int
        or kind is float
        or kind is Decimal
        or kind is str
        or kind is bool
        or value is None
    )


def _plain_label(value: Any) -> bool:
    return _plain(value) or (type(value) is tuple and all(_plain(item) for item in value))


def _trusted_rule(rule: Any) -> bool:
    # Import lazily: core is initialized before the built-in rule package.
    from finassert.numerical import Tolerance
    from finassert.rules.arithmetic import InRangeRule, NonNegativeRule
    from finassert.rules.portfolio import WeightsSumToOneRule

    if type(rule) not in (NonNegativeRule, InRangeRule, WeightsSumToOneRule):
        return False
    if (
        type(rule.tolerance) is not Tolerance
        or not _plain(rule.tolerance.absolute)
        or not _plain(rule.tolerance.relative)
        or type(rule.column) is not str
        or type(rule.max_violations) is not int
    ):
        return False
    if type(rule) is InRangeRule:
        return (
            _plain(rule.minimum)
            and _plain(rule.maximum)
            and (rule.row_key is None or type(rule.row_key) is str)
        )
    if type(rule) is WeightsSumToOneRule:
        return type(rule.group_by) is tuple and all(type(name) is str for name in rule.group_by)
    return True


class _ReadSession:
    """Retain at most one materialized column during one check call.

    Custom sources (including MoneySource), custom rules/subclasses and lazy
    rule iterables retain their original observable read and mutation behavior.
    A context-local session isolates nested and concurrent checks. No numeric
    classification, aggregate or financial-unit context is cached.
    """

    def __init__(self, data: Any, rules: Any, *, enabled: bool) -> None:
        self.data = data
        pandas = modules.get("pandas")
        native_frame = pandas is not None and type(data) is getattr(pandas, "DataFrame", None)
        self.enabled = (
            enabled
            and type(rules) in (list, tuple)
            and len(rules) > 1
            and (type(data) is dict or native_frame)
        )
        self.name: str | None = None
        self.column: tuple[list[Any], list[Any]] | None = None
        self._token: Token[_ReadSession | None] | None = None

    def __enter__(self) -> Self:
        self._token = _ACTIVE.set(None)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.clear()
        assert self._token is not None
        _ACTIVE.reset(self._token)

    def select(self, rule: Any) -> None:
        """Enable sharing only for an exact trusted rule, clearing at barriers."""
        if self.enabled and _trusted_rule(rule):
            _ACTIVE.set(self)
        else:
            self.clear()
            _ACTIVE.set(None)

    def accepts(self, data: Any, name: str) -> bool:
        """Exclude one-shot or custom column iterables from reuse."""
        return data is self.data and (
            type(data) is not dict or type(data.get(name)) in (list, tuple)
        )

    def remember(self, name: str, column: tuple[list[Any], list[Any]]) -> None:
        """Share ordinary scalars; overloaded cells/labels keep observable reads."""
        values, labels = column
        if all(_plain(value) for value in values) and all(_plain_label(label) for label in labels):
            self.name, self.column = name, column
        else:
            # Scan at most once before falling back for the rest of this call.
            self.enabled = False
            self.clear()
            _ACTIVE.set(None)

    def clear(self) -> None:
        """Release the retained column before another read or rule boundary."""
        self.name = None
        self.column = None


_ACTIVE: ContextVar[_ReadSession | None] = ContextVar("finassert_shared_reads", default=None)
