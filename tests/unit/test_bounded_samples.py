from dataclasses import dataclass
from weakref import ref

import pytest

from finassert.rules._diagnostics import Sample


@dataclass
class Observation:
    row: int


@pytest.mark.parametrize("limit", [0, 1, 20])
def test_only_sampled_observations_remain_alive(limit: int) -> None:
    sample: Sample[Observation] = Sample(limit)
    references = []
    for row in range(10_000):
        observation = Observation(row)
        references.append(ref(observation))
        sample.add(observation)
    del observation

    assert sample.count == 10_000
    assert [item.row for item in sample.examples] == list(range(limit))
    assert sum(item() is not None for item in references) == limit
    assert bool(sample) and sample.truncated


@pytest.mark.parametrize("limit", [0, 1, 20])
@pytest.mark.parametrize("count", [0, 1, 20, 21])
def test_empty_exact_and_truncated_populations(limit: int, count: int) -> None:
    sample: Sample[int] = Sample(limit)
    for row in range(count):
        sample.add(row)

    assert sample.count == count
    assert sample.examples == list(range(min(count, limit)))
    assert bool(sample) == (count > 0)
    assert sample.truncated == (count > limit)
