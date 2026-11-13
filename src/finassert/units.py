"""Explicit financial dimensions, direct FX, and a homogeneous-money adapter."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation, localcontext
from typing import Any, ClassVar, Self, TypeAlias, TypeVar

from finassert.adapters._column import extract_column, is_missing
from finassert.core.exceptions import InvalidDataError

Scalar: TypeAlias = Decimal | int | float | str


def _decimal(value: Scalar) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, Decimal | int | float | str):
        raise TypeError("amounts must be Decimal, integer, float, or decimal text")
    try:
        amount = value if isinstance(value, Decimal) else Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("amount must be decimal numeric text") from exc
    if not amount.is_finite():
        raise ValueError("amount must be finite")
    return amount


def _currency(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("currency must be text")
    code = value.strip().upper()
    if not re.fullmatch(r"[A-Z]{3}|UNIT:[A-Z0-9][A-Z0-9_.-]{0,31}", code):
        raise ValueError("use a three-letter currency code or an explicit UNIT:identifier")
    return code


def _calculate(a: Decimal, b: Decimal, operation: str) -> Decimal:
    # Reserve enough digits for exact addition/multiplication and useful inverses.
    precision = max(50, len(a.as_tuple().digits) + len(b.as_tuple().digits) + 2)
    if operation in {"add", "subtract"}:
        precision = max(
            precision,
            max(a.adjusted(), b.adjusted())
            - min(int(a.as_tuple().exponent), int(b.as_tuple().exponent))
            + 3,
        )
    with localcontext() as context:
        context.prec = precision
        if operation == "add":
            return a + b
        if operation == "subtract":
            return a - b
        if operation == "multiply":
            return a * b
        return a / b


def _utc(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware")
    return value.astimezone(UTC)


@dataclass(frozen=True, slots=True, init=False)
class _Quantity:
    _finassert_serializable: ClassVar[bool] = True
    amount: Decimal
    currency: str
    provenance: tuple[FxRate, ...] = field(default=(), compare=False)

    def __init__(
        self, amount: Scalar, currency: str, *, provenance: tuple[FxRate, ...] = ()
    ) -> None:
        object.__setattr__(self, "amount", _decimal(amount))
        object.__setattr__(self, "currency", _currency(currency))
        if not isinstance(provenance, tuple) or any(
            not isinstance(rate, FxRate) for rate in provenance
        ):
            raise TypeError("provenance must be a tuple of FxRate records")
        object.__setattr__(self, "provenance", tuple(dict.fromkeys(provenance)))

    def _compatible(self, other: object) -> Self:
        if type(other) is not type(self):
            raise TypeError("financial dimensions must match")
        assert isinstance(other, _Quantity)
        if self.currency != other.currency:
            raise ValueError("currencies must match; convert explicitly first")
        return other

    def __add__(self, other: object) -> Self:
        other = self._compatible(other)
        return type(self)(
            _calculate(self.amount, other.amount, "add"),
            self.currency,
            provenance=(*self.provenance, *other.provenance),
        )

    def __sub__(self, other: object) -> Self:
        other = self._compatible(other)
        return type(self)(
            _calculate(self.amount, other.amount, "subtract"),
            self.currency,
            provenance=(*self.provenance, *other.provenance),
        )

    def scale(self, factor: Scalar | _Ratio) -> Self:
        """Multiply by an explicit scalar or ratio fraction, preserving provenance."""
        amount = factor.fraction if isinstance(factor, _Ratio) else _decimal(factor)
        return type(self)(
            _calculate(self.amount, amount, "multiply"), self.currency, provenance=self.provenance
        )

    def to_dict(self) -> dict[str, Any]:
        """Return amount, dimension, currency, and every retained FX record."""
        return {
            "unit": type(self).__name__,
            "amount": str(self.amount),
            "currency": self.currency,
            "fx_rates": [rate.to_dict() for rate in self.provenance],
        }


class Money(_Quantity):
    """An immutable monetary amount in a declared currency or fund unit."""

    __slots__ = ()


class Price(_Quantity):
    """A currency-denominated price, distinct from money and notional."""

    __slots__ = ()


class Notional(_Quantity):
    """A currency-denominated notional, distinct from money and price."""

    __slots__ = ()


@dataclass(frozen=True, slots=True, init=False)
class _Ratio:
    _finassert_serializable: ClassVar[bool] = True
    value: Decimal
    denominator: ClassVar[Decimal] = Decimal(1)

    def __init__(self, value: Scalar) -> None:
        object.__setattr__(self, "value", _decimal(value))

    @property
    def fraction(self) -> Decimal:
        """Return this ratio expressed as a fraction of one."""
        return _calculate(self.value, self.denominator, "divide")

    def __add__(self, other: object) -> Self:
        if type(other) is not type(self):
            raise TypeError("ratio units must match; convert explicitly")
        assert isinstance(other, _Ratio)
        return type(self)(_calculate(self.value, other.value, "add"))

    def __sub__(self, other: object) -> Self:
        if type(other) is not type(self):
            raise TypeError("ratio units must match; convert explicitly")
        assert isinstance(other, _Ratio)
        return type(self)(_calculate(self.value, other.value, "subtract"))

    def to_return(self) -> Return:
        """Convert explicitly to a fractional return."""
        return Return(self.fraction)

    def to_percentage(self) -> Percentage:
        """Convert explicitly to percentage points."""
        return Percentage(_calculate(self.fraction, Decimal(100), "multiply"))

    def to_basis_points(self) -> BasisPoints:
        """Convert explicitly to basis points."""
        return BasisPoints(_calculate(self.fraction, Decimal(10000), "multiply"))

    def to_dict(self) -> dict[str, str]:
        """Return the explicit ratio unit and exact value text."""
        return {"unit": type(self).__name__, "value": str(self.value)}


class BasisPoints(_Ratio):
    """Basis points: 1 bp is a fraction of 0.0001."""

    __slots__ = ()
    denominator = Decimal(10000)


class Percentage(_Ratio):
    """Percentage points: 1 percent is a fraction of 0.01."""

    __slots__ = ()
    denominator = Decimal(100)


class Return(_Ratio):
    """A return already expressed as a fraction of one."""

    __slots__ = ()


Q = TypeVar("Q", bound=_Quantity)


@dataclass(frozen=True, slots=True, init=False)
class FxRate:
    """A positive direct rate: one base unit equals ``rate`` quote units."""

    _finassert_serializable: ClassVar[bool] = True
    base: str
    quote: str
    rate: Decimal
    as_of: datetime
    source: str
    identifier: str | None

    def __init__(
        self,
        base: str,
        quote: str,
        rate: Scalar,
        as_of: datetime,
        *,
        source: str,
        identifier: str | None = None,
    ) -> None:
        base, quote, amount = _currency(base), _currency(quote), _decimal(rate)
        if amount <= 0 or (base == quote and amount != 1):
            raise ValueError("FX rate must be positive; same-currency rates must equal one")
        if not isinstance(source, str) or not source.strip():
            raise ValueError("FX source must be nonempty")
        if identifier is not None and (not isinstance(identifier, str) or not identifier.strip()):
            raise ValueError("FX identifier must be nonempty when supplied")
        for key, value in {
            "base": base,
            "quote": quote,
            "rate": amount,
            "as_of": _utc(as_of),
            "source": source,
            "identifier": identifier,
        }.items():
            object.__setattr__(self, key, value)

    def convert(self, quantity: Q, *, at: datetime, max_age: timedelta) -> Q:
        """Convert in the declared direction after checking explicit valuation age."""
        if not isinstance(quantity, _Quantity):
            raise TypeError("FX conversion requires a currency-denominated quantity")
        if quantity.currency != self.base:
            raise ValueError("FX direction does not match the quantity currency")
        if not isinstance(max_age, timedelta) or max_age < timedelta(0):
            raise ValueError("max_age must be a nonnegative timedelta")
        age = _utc(at) - self.as_of
        if age < timedelta(0):
            raise ValueError("FX rate is from the future relative to valuation time")
        if age > max_age:
            raise ValueError("FX rate is stale")
        return type(quantity)(
            _calculate(quantity.amount, self.rate, "multiply"),
            self.quote,
            provenance=(*quantity.provenance, self),
        )

    def inverse(self) -> FxRate:
        """Return an explicit inverse retaining source, timestamp, and identifier."""
        return FxRate(
            self.quote,
            self.base,
            _calculate(Decimal(1), self.rate, "divide"),
            self.as_of,
            source=self.source,
            identifier=self.identifier,
        )

    def to_dict(self) -> dict[str, Any]:
        """Return complete direct-rate provenance with an aware UTC timestamp."""
        return {
            "base": self.base,
            "quote": self.quote,
            "rate": str(self.rate),
            "as_of": self.as_of.isoformat().replace("+00:00", "Z"),
            "source": self.source,
            "identifier": self.identifier,
        }


class MoneySource:
    """Expose declared homogeneous Money columns as Decimal inputs for rules.

    Other columns retain their values and native row labels. Requested monetary
    cells must be Money in ``currency`` or missing; no conversion is inferred.
    """

    def __init__(self, data: Any, *, columns: Sequence[str], currency: str) -> None:
        if (
            not isinstance(columns, Sequence)
            or isinstance(columns, str)
            or not columns
            or any(not isinstance(name, str) or not name for name in columns)
        ):
            raise ValueError("columns must be a nonempty sequence of column names")
        if len(set(columns)) != len(columns):
            raise ValueError("monetary columns must be unique")
        self._data = data
        self._columns = tuple(columns)
        self.currency = _currency(currency)
        self._used: dict[str, str] = {}
        self._rates: dict[FxRate, None] = {}

    def column(self, name: str) -> tuple[list[Any], list[Any]]:
        """Read one column, checking its monetary dimension before unwrapping."""
        values, labels = extract_column(self._data, name)
        if name not in self._columns:
            return values, labels
        result = []
        rates: dict[FxRate, None] = {}
        for label, value in zip(labels, values, strict=True):
            if is_missing(value):
                result.append(value)
                continue
            if type(value) is not Money or value.currency != self.currency:
                raise InvalidDataError(
                    f"column {name!r}, row {label!r} requires Money in {self.currency}"
                )
            result.append(value.amount)
            rates.update(dict.fromkeys(value.provenance))
        if len(self._rates.keys() | rates.keys()) > 100:
            raise InvalidDataError(
                "MoneySource exceeds 100 distinct FX records; split the validation population"
            )
        self._rates.update(rates)
        self._used[name] = "Money"
        return result, labels

    @property
    def validation_context(self) -> dict[str, Any]:
        """Return declared units and all FX provenance used by requested columns."""
        return {
            "currency": self.currency,
            "columns": dict(self._used),
            "fx_rates": [rate.to_dict() for rate in self._rates],
        }

    def reset_validation_context(self) -> None:
        """Begin one rule's provenance scope without retaining earlier reads."""
        self._used.clear()
        self._rates.clear()
