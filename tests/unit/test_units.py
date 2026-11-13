from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

import finassert as fa
from finassert.reporting import artifact_to_json, build_artifact
from finassert.units import (
    BasisPoints,
    FxRate,
    Money,
    MoneySource,
    Notional,
    Percentage,
    Price,
    Return,
)

AS_OF = datetime(2026, 11, 13, 12, tzinfo=UTC)
AGE = timedelta(days=1)


def rate(value: str = "1.08", **kwargs: object) -> FxRate:
    return FxRate(
        "eur", "usd", value, AS_OF, source="approved-close", identifier="close-1", **kwargs
    )  # type: ignore[arg-type]


@pytest.mark.parametrize("quantity", [Money, Price, Notional])
def test_quantity_precision_currency_and_immutability(quantity: type[Money]) -> None:
    value = quantity("12345678901234567890.123456789", " usd ")
    added = value + quantity("0.000000001", "USD")
    assert added.amount == Decimal("12345678901234567890.123456790")
    assert value.currency == "USD"
    with pytest.raises((FrozenInstanceError, AttributeError)):
        value.amount = Decimal(0)
    with pytest.raises(ValueError, match="currencies must match"):
        value + quantity(1, "EUR")


@pytest.mark.parametrize(
    "bad", [True, False, "NaN", "Infinity", float("nan"), float("inf"), "1,000", "40%"]
)
def test_invalid_amounts_cannot_be_quantities(bad: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        Money(bad, "USD")  # type: ignore[arg-type]


def test_dimensions_and_ratio_conversions_are_explicit() -> None:
    assert BasisPoints(50).fraction == Decimal("0.005")
    assert BasisPoints(50).to_percentage() == Percentage("0.5")
    assert Percentage(50).fraction == Decimal("0.5")
    assert Return("0.05").to_basis_points() == BasisPoints(500)
    assert Money(100, "USD").scale(BasisPoints(50)) == Money("0.5", "USD")
    with pytest.raises(TypeError):
        Money(1, "USD") + Price(1, "USD")
    with pytest.raises(TypeError):
        BasisPoints(50) + Percentage(50)
    with pytest.raises(TypeError):
        Money(1, "USD").scale(True)
    assert Money(1, "UNIT:fund-1").currency == "UNIT:FUND-1"
    with pytest.raises(ValueError):
        Money(1, "fund-1")


def test_direct_conversion_records_rate_and_preserves_provenance_in_arithmetic() -> None:
    fx = rate()
    converted = fx.convert(Money("50.00", "EUR"), at=AS_OF + AGE, max_age=AGE)
    assert converted.amount == Decimal("54.0000") and converted.currency == "USD"
    assert (converted + Money(1, "USD")).provenance == (fx,)
    assert converted.scale(2).provenance == (fx,)
    assert converted.to_dict()["fx_rates"] == [
        {
            "base": "EUR",
            "quote": "USD",
            "rate": "1.08",
            "as_of": "2026-11-13T12:00:00Z",
            "source": "approved-close",
            "identifier": "close-1",
        }
    ]
    assert fx.convert(Price(1, "EUR"), at=AS_OF, max_age=AGE) == Price("1.08", "USD")


def test_stale_future_naive_and_incompatible_fx_are_rejected() -> None:
    fx = rate()
    for at, age, message in [
        (AS_OF + AGE + timedelta(microseconds=1), AGE, "stale"),
        (AS_OF - timedelta(microseconds=1), AGE, "future"),
        (AS_OF, -AGE, "nonnegative"),
    ]:
        with pytest.raises(ValueError, match=message):
            fx.convert(Money(1, "EUR"), at=at, max_age=age)
    with pytest.raises(ValueError, match="direction"):
        fx.convert(Money(1, "GBP"), at=AS_OF, max_age=AGE)
    with pytest.raises(ValueError, match="timezone-aware"):
        fx.convert(Money(1, "EUR"), at=datetime(2026, 11, 13), max_age=AGE)
    with pytest.raises(ValueError, match="timezone-aware"):
        FxRate("EUR", "USD", 1, datetime(2026, 11, 13), source="x")
    with pytest.raises(ValueError):
        FxRate("EUR", "USD", 0, AS_OF, source="x")
    with pytest.raises(ValueError):
        FxRate("EUR", "USD", 1, AS_OF, source=" ")
    with pytest.raises(ValueError):
        FxRate("USD", "USD", 2, AS_OF, source="x")
    identity = FxRate("USD", "USD", 1, AS_OF, source="identity")
    assert identity.convert(Money(-1, "USD"), at=AS_OF, max_age=timedelta(0)) == Money(-1, "USD")


def test_aware_rate_timestamps_normalize_to_utc() -> None:
    fx = FxRate(
        "EUR",
        "USD",
        1,
        datetime(2026, 11, 13, 7, tzinfo=timezone(timedelta(hours=-5))),
        source="close",
    )
    assert fx.as_of == AS_OF
    assert fx.to_dict()["as_of"] == "2026-11-13T12:00:00Z"


def test_money_adapter_reconciliation_and_artifact_provenance() -> None:
    fx = rate()
    converted = fx.convert(Money(10, "EUR"), at=AS_OF, max_age=AGE)
    data = {
        "id": ["cash-1"],
        "open": [Money(100, "USD")],
        "in": [converted],
        "out": [Money(5, "USD")],
        "close": [Money("105.8", "USD")],
    }
    source = MoneySource(data, columns=["open", "in", "out", "close"], currency="USD")
    rule = fa.cash_reconciles(
        outflow_sign="positive",
        opening_cash="open",
        inflows="in",
        outflows="out",
        closing_cash="close",
        row_key="id",
    )
    report = fa.check(source, [rule])
    assert report.passed
    context = report.results[0].metadata["financial_units"]
    assert context["currency"] == "USD" and context["fx_rates"] == [fx.to_dict()]
    artifact = artifact_to_json(build_artifact(report, generated_at=AS_OF))
    assert '"approved-close"' in artifact and '"close-1"' in artifact
    assert data["in"] == [converted]


@pytest.mark.parametrize("bad", [Money(1, "EUR"), Price(1, "USD"), 1])
def test_money_adapter_cannot_silently_strip_incompatible_units(bad: object) -> None:
    source = MoneySource({"v": [bad]}, columns=["v"], currency="USD")
    result = fa.check(source, [fa.non_negative(column="v", severity="warning")]).results[0]
    assert result.outcome is fa.Outcome.ERROR and result.blocking


def test_adapter_provenance_is_scoped_to_each_rule_and_repeated_run() -> None:
    fx = rate()
    source = MoneySource(
        {"a": [fx.convert(Money(1, "EUR"), at=AS_OF, max_age=AGE)], "b": [Money(1, "USD")]},
        columns=["a", "b"],
        currency="USD",
    )
    report = fa.check(source, [fa.non_negative(column="a"), fa.non_negative(column="b")])
    assert report.results[0].metadata["financial_units"]["fx_rates"] == [fx.to_dict()]
    assert report.results[1].metadata["financial_units"] == {
        "currency": "USD",
        "columns": {"b": "Money"},
        "fx_rates": [],
    }
    assert (
        fa.check(source, [fa.non_negative(column="b")])
        .results[0]
        .metadata["financial_units"]["fx_rates"]
        == []
    )


def test_typed_values_serialize_with_dimension_and_provenance() -> None:
    money = rate().convert(Money(1, "EUR"), at=AS_OF, max_age=AGE)
    result = fa.ValidationResult(
        "test.units",
        "Units",
        fa.Outcome.PASSED,
        fa.Severity.INFO,
        "ok",
        observed=money,
        expected=Percentage(5),
    )
    assert result.to_dict()["observed"] == money.to_dict()
    assert result.to_dict()["expected"] == {"unit": "Percentage", "value": "5"}


def test_missing_money_uses_rule_policy_and_rate_provenance_is_never_truncated() -> None:
    source = MoneySource({"v": [None, Money(1, "USD")]}, columns=["v"], currency="USD")
    assert fa.check(source, [fa.non_negative(column="v", null_policy="ignore")]).passed
    converted = [
        FxRate("USD", "USD", 1, AS_OF, source="synthetic", identifier=str(i)).convert(
            Money(1, "USD"), at=AS_OF, max_age=timedelta(0)
        )
        for i in range(101)
    ]
    source = MoneySource({"v": converted}, columns=["v"], currency="USD")
    result = fa.check(source, [fa.non_negative(column="v")]).results[0]
    assert result.outcome is fa.Outcome.ERROR
    assert "100 distinct FX records" in result.message


@given(
    st.decimals(min_value=-10000, max_value=10000, places=4, allow_nan=False, allow_infinity=False),
    st.decimals(min_value="0.1", max_value="5", places=4, allow_nan=False, allow_infinity=False),
)
def test_explicit_fx_inverse_roundtrip_preserves_amount_with_declared_tolerance(
    amount: Decimal, value: Decimal
) -> None:
    fx = rate(str(value))
    converted = fx.convert(Money(amount, "EUR"), at=AS_OF, max_age=AGE)
    restored = fx.inverse().convert(converted, at=AS_OF, max_age=AGE)
    assert restored.currency == "EUR"
    assert fa.Tolerance(absolute=Decimal("1e-36")).is_close(restored.amount, amount)


@given(
    st.decimals(min_value=-1000, max_value=1000, places=6, allow_nan=False, allow_infinity=False)
)
def test_ratio_roundtrips_are_exact(value: Decimal) -> None:
    assert BasisPoints(value).to_percentage().to_basis_points() == BasisPoints(value)
    assert Percentage(value).to_return().to_percentage() == Percentage(value)
