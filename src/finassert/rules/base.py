"""Shared rule configuration."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from finassert.core.models import Severity


class NullPolicy(StrEnum):
    """How a rule handles missing observations."""

    FAIL = "fail"
    IGNORE = "ignore"
    SKIP = "skip"


@dataclass(frozen=True, slots=True)
class BaseRule:
    """Common identity and severity fields for built-in rules."""

    rule_id: str
    name: str
    severity: Severity = Severity.ERROR
