"""Bounded diagnostic samples with complete population counts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(slots=True)
class Sample(Generic[T]):
    """Count every observation and retain its first ``limit`` examples in order.

    Truth reflects the full population, including when the limit is zero.
    Callers must still perform all validation and numerical work after filling
    the sample; dropping examples must never hide a failure or evaluation error.
    """

    limit: int
    count: int = field(default=0, init=False)
    examples: list[T] = field(default_factory=list, init=False)

    def add(self, observation: T) -> None:
        """Count an observation, retaining it only while the sample has room."""
        self.count += 1
        if len(self.examples) < self.limit:
            self.examples.append(observation)

    def __bool__(self) -> bool:
        return self.count > 0

    @property
    def truncated(self) -> bool:
        """Return whether any counted observations were omitted."""
        return self.count > len(self.examples)
