from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pandas as pd
import pytest

import finassert as fa
from finassert.adapters import _column
from finassert.core.engine import _check
from finassert.core.exceptions import RuleEvaluationError
from finassert.rules.arithmetic import NonNegativeRule
from finassert.units import FxRate, Money, MoneySource


def calls(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    recorded: list[str] = []
    original = _column._extract_uncached

    def read(data: Any, name: str) -> tuple[list[Any], list[Any]]:
        recorded.append(name)
        return original(data, name)

    monkeypatch.setattr(_column, "_extract_uncached", read)
    return recorded


@pytest.mark.parametrize("adapter", ["mapping", "pandas"])
def test_repeated_column_is_materialized_once_and_discarded_between_calls(
    monkeypatch: pytest.MonkeyPatch, adapter: str
) -> None:
    recorded = calls(monkeypatch)
    data: Any = {"v": [Decimal("0.4"), Decimal("0.6")]}
    if adapter == "pandas":
        data = pd.DataFrame(data, index=[("book", 1), ("book", 1)])
    rules = [fa.non_negative(column="v"), fa.in_range(column="v", maximum=1)] * 25
    scalar = _check(data, rules, share_columns=False).to_dict()
    assert len(recorded) == 50
    recorded.clear()
    assert fa.check(data, rules).to_dict() == scalar
    assert recorded == ["v"]
    if adapter == "mapping":
        data["v"][0] = Decimal("-1")
    else:
        data.iloc[0, 0] = Decimal("-1")
    assert not fa.check(data, rules).passed
    assert recorded == ["v", "v"]


def test_cache_retains_one_column_instead_of_all_policy_columns(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    recorded = calls(monkeypatch)
    rules = [fa.non_negative(column=name) for name in ("a", "a", "b", "b", "a")]
    data = {"a": [1], "b": [2]}
    assert fa.check(data, rules).to_dict() == _check(data, rules, share_columns=False).to_dict()
    assert recorded[:3] == ["a", "b", "a"]
    assert len(recorded) == 8


@pytest.mark.parametrize("replace", [False, True])
def test_custom_rule_mutation_invalidates_shared_values(replace: bool) -> None:
    data = {"v": [1]}

    def mutate(raw: Any) -> bool:
        if replace:
            raw["v"] = [-1]
        else:
            raw["v"][0] = -1
        return True

    rules = [
        fa.non_negative(column="v"),
        fa.custom_rule("change", "Change", mutate),
        fa.non_negative(column="v"),
    ]
    report = fa.check(data, rules)
    assert [item.outcome for item in report.results] == [
        fa.Outcome.PASSED,
        fa.Outcome.PASSED,
        fa.Outcome.FAILED,
    ]


def test_builtin_subclasses_are_custom_rule_boundaries() -> None:
    class MutatingRule(NonNegativeRule):
        def evaluate(self, data: Any) -> fa.ValidationResult:
            data["v"][0] = -1
            return super().evaluate(data)

    rules = [fa.non_negative(column="v"), MutatingRule(column="v"), fa.non_negative(column="v")]
    assert [item.observed for item in fa.check({"v": [1]}, rules).results] == [0, 1, 1]


def test_lazy_rule_iterable_can_mutate_input_between_yields() -> None:
    data = {"v": [1]}

    def rules() -> Iterator[Any]:
        yield fa.non_negative(column="v")
        data["v"][0] = -1
        yield fa.non_negative(column="v")

    report = fa.check(data, rules())
    assert [item.observed for item in report.results] == [0, 1]


def test_one_shot_column_and_dynamic_column_source_keep_scalar_behavior() -> None:
    rules = [fa.non_negative(column="v")] * 2
    report = fa.check({"v": iter([1])}, rules)
    assert [item.metadata["checked_count"] for item in report.results] == [1, 0]

    class Source:
        count = 0

        def column(self, name: str) -> tuple[list[Any], list[Any]]:
            self.count += 1
            return [1 if self.count == 1 else -1], ["same"]

    source = Source()
    assert [item.observed for item in fa.check(source, rules).results] == [0, 1]
    assert source.count == 2


@pytest.mark.parametrize("policy", ["fail", "ignore", "skip"])
def test_decimal_labels_nulls_limits_and_errors_match_scalar(policy: str) -> None:
    frame = pd.DataFrame(
        {
            "v": [Decimal("-0.010000000000000000001"), None, Decimal("1.01"), "bad"],
            "key": [("id", 2), ("id", 2), ("id", 1), ("id", 0)],
        },
        index=[("book", Decimal("1.20")), ("book", Decimal("1.20")), float("nan"), "last"],
    )
    rules = [
        fa.non_negative(
            column="v", tolerance=Decimal("0.01"), null_policy=policy, max_violations=0
        ),
        fa.in_range(
            column="v",
            minimum=0,
            maximum=1,
            tolerance=Decimal("0.01"),
            null_policy=policy,
            row_key="key",
            max_violations=1,
        ),
        fa.non_negative(column="absent"),
        fa.weights_sum_to_one(column="v", null_policy=policy),
        fa.non_negative(column="v", null_policy=policy),
    ]
    before = frame.copy(deep=True)
    assert fa.check(frame, rules).to_dict() == _check(frame, rules, share_columns=False).to_dict()
    pd.testing.assert_frame_equal(frame, before)


def test_money_and_fx_provenance_is_scoped_to_each_rule_and_each_call() -> None:
    now = datetime(2026, 11, 13, tzinfo=UTC)
    rate = FxRate("EUR", "USD", Decimal("1.1"), now, source="synthetic")
    source = MoneySource(
        {
            "a": [rate.convert(Money(1, "EUR"), at=now, max_age=timedelta(0))],
            "b": [Money(1, "USD")],
        },
        columns=["a", "b"],
        currency="USD",
    )
    rules = [
        fa.non_negative(column="a"),
        fa.non_negative(column="b"),
        fa.in_range(column="a", maximum=2),
    ]
    scalar = _check(source, rules, share_columns=False).to_dict()
    report = fa.check(source, rules)
    assert report.to_dict() == scalar
    contexts = [item.metadata["financial_units"] for item in report.results]
    assert [item["columns"] for item in contexts] == [
        {"a": "Money"},
        {"b": "Money"},
        {"a": "Money"},
    ]
    assert [item["fx_rates"] for item in contexts] == [[rate.to_dict()], [], [rate.to_dict()]]
    assert fa.check(source, rules).to_dict() == scalar


def test_nested_checks_and_strict_exceptions_do_not_leak_cache() -> None:
    def nested(raw: Any) -> bool:
        assert not fa.check({"v": [-1]}, [fa.non_negative(column="v")] * 2).passed
        raw["v"][0] = -1
        return True

    rules = [
        fa.non_negative(column="v"),
        fa.custom_rule("nested", "Nested", nested),
        fa.non_negative(column="v"),
    ]
    assert fa.check({"v": [1]}, rules).results[-1].outcome is fa.Outcome.FAILED
    with pytest.raises(RuleEvaluationError):
        fa.check(
            {"v": [1]},
            [fa.non_negative(column="v"), fa.non_negative(column="missing")],
            raise_on_error=True,
        )
    assert not fa.check({"v": [-1]}, [fa.non_negative(column="v")] * 2).passed


def test_validation_context_hooks_cannot_reuse_pre_reset_values() -> None:
    frame = pd.DataFrame({"v": [1]})
    resets = []

    def reset() -> None:
        resets.append(True)
        frame.iloc[0, 0] = 1 if len(resets) == 1 else -1

    object.__setattr__(frame, "reset_validation_context", reset)
    object.__setattr__(frame, "validation_context", {"source": "custom hook"})
    report = fa.check(frame, [fa.non_negative(column="v")] * 2)
    assert [item.observed for item in report.results] == [0, 1]


def test_concurrent_checks_do_not_share_source_values(monkeypatch: pytest.MonkeyPatch) -> None:
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    barrier = Barrier(2)
    original = _column._extract_uncached

    def read(data: Any, name: str) -> tuple[list[Any], list[Any]]:
        barrier.wait(timeout=10)
        return original(data, name)

    monkeypatch.setattr(_column, "_extract_uncached", read)
    rules = [fa.non_negative(column="v")] * 2
    with ThreadPoolExecutor(max_workers=2) as pool:
        passed = pool.submit(fa.check, {"v": [1]}, rules)
        failed = pool.submit(fa.check, {"v": [-1]}, rules)
        assert passed.result().passed
        assert [item.observed for item in failed.result().results] == [1, 1]


def test_custom_tolerance_callbacks_are_scalar_boundaries() -> None:
    data = {"v": [1]}

    class CustomTolerance(fa.Tolerance):
        def is_close(self, observed: Any, expected: Any) -> bool:
            data["v"][0] = -1
            return super().is_close(observed, expected)

    rules = [
        fa.weights_sum_to_one(column="v", tolerance=CustomTolerance()),
        fa.non_negative(column="v"),
    ]
    assert [item.observed for item in fa.check(data, rules).results] == [1, 1]


def test_overloaded_cells_cannot_hide_input_mutation() -> None:
    data: Any = {"v": []}

    class MutatingInt(int):
        def __lt__(self, other: Any) -> bool:
            data["v"] = [-1]
            return super().__lt__(other)

    data["v"] = [MutatingInt(1)]
    rules = [fa.non_negative(column="v")] * 2
    assert [item.observed for item in fa.check(data, rules).results] == [0, 1]
