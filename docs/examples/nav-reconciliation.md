# NAV reconciliation

`nav_reconciles` checks that the market values of every line in a portfolio add
up to its reported net asset value (NAV), separately for each portfolio:

```text
sum(market_value) = nav
```

```python
from decimal import Decimal

import finassert as fa

rule = fa.nav_reconciles(
    market_value="market_value",
    nav="nav",
    group_by=["portfolio"],
    tolerance=Decimal("0.01"),
)
report = fa.check(holdings, [rule])
```

## Conventions

- **Signs.** Market values are signed. Liabilities and short positions are
  negative rows, so assets minus liabilities is simply the sum. There is no
  separate liabilities column and no sign option.
- **Where the NAV is written.** It may be repeated on every row of a portfolio
  or given on only some rows, but every value given within a portfolio must
  agree, and each portfolio needs at least one.
- **Blanks are never zero.** A blank market value makes its rows fail the check
  (or skip it, with `null_policy: skip`) rather than counting as 0.
- **Currencies are never converted.** Name the `currency` column and each
  currency reconciles separately; omit it only if every portfolio's market
  values and NAV share one currency.
- **Tolerance.** Allowed difference in currency units. Pricing and rounding
  usually justify a few cents; zero demands an exact match.

## Not suitable when

Cash, accruals, or liabilities are not rows in the file, liabilities are stored
as positive numbers, or market values are in local currencies while the NAV is
in a base currency.

## Try it

```bash
finassert init --template nav-reconciliation --output nav-policy.yml
finassert check --config nav-policy.yml --input examples/holdings.csv --html report.html
```

`examples/holdings.csv` reconciles. A failing portfolio is listed with its
total, the reported NAV, the difference, and the row numbers.
