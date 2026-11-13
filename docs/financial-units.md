# Financial units and explicit FX

Use `finassert.units` when amounts need currency and dimensional checks before
running numeric rules. Existing numeric inputs keep their behavior.

```python
from datetime import UTC, datetime, timedelta
from finassert.units import BasisPoints, FxRate, Money, MoneySource
import finassert as fa

as_of = datetime(2026, 11, 13, 12, tzinfo=UTC)
rate = FxRate("EUR", "USD", "1.08", as_of, source="approved-close", identifier="close-1")
converted = rate.convert(Money("50.00", "EUR"), at=as_of, max_age=timedelta(hours=24))
assert converted == Money("54.0000", "USD")
assert Money("100", "USD").scale(BasisPoints(50)) == Money("0.5", "USD")

source = MoneySource({"value": [converted]}, columns=["value"], currency="USD")
report = fa.check(source, [fa.non_negative(column="value")])
print(report.results[0].metadata["financial_units"])
```

`Money`, `Price`, and `Notional` are distinct immutable dimensions. Addition and
subtraction require the same dimension and currency. `BasisPoints(50)` means
0.5%, while `Percentage(50)` means 50%; `Return("0.05")` means a 5% fractional
return. Named conversions make these distinctions explicit. Amounts remain
Decimal, and materiality tolerances remain separate from currency rounding.

Currency strings normalize to three uppercase letters. The initial module checks
syntax rather than maintaining a current assignment registry. Caller-owned fund
units use an explicit namespace, such as `UNIT:MY_FUND`.

Rates are supplied by the caller; no rate provider or conversion path is selected.
A rate states how many quote units one base unit buys. `convert` requires a
valuation timestamp and maximum age, rejecting future, stale, nonpositive, or
directionally incompatible rates. `inverse()` is explicit and retains source,
as-of time, and identifier. Same-currency rates must equal one.

`MoneySource` exposes declared Money columns as Decimal values after checking the
currency. Convert mixed currencies explicitly before adapting them. Other columns
and native row labels remain intact. Each result's `financial_units` metadata
contains the used columns, currency, and distinct FX records; JSON and Excel
reports retain this provenance. A source with more than 100 distinct rates errors
instead of truncating rate evidence. Null cells still follow the selected rule's
policy. Price and Notional are standalone quantities; the initial adapter accepts
Money columns only.
