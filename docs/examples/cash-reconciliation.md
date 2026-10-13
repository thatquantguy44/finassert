# Cash reconciliation

`cash_reconciles` checks that cash balances roll forward, separately for each
account (for example each portfolio, currency, and day):

```text
closing = opening + inflows - outflows + cash P&L
```

```python
from decimal import Decimal

import finassert as fa

rule = fa.cash_reconciles(
    outflow_sign="positive",
    opening_cash="opening_balance",
    inflows="inflows",
    outflows="outflows",
    cash_pnl="cash_income",  # optional
    closing_cash="closing_balance",
    group_by=["portfolio", "date"],
    currency="currency",
    tolerance=Decimal("0.01"),
)
```

## Conventions

- **Outflow sign has no default.** `positive` means money paid out appears as
  positive amounts and is subtracted; `negative` means it appears as negative
  amounts and is added. Each result records the equation it checked, so a
  report always says which convention was used.
- **Row layout.** With `grain="summary"` (the default), each group has one row
  holding both balances and the total flows, and repeated rows must agree.
  With `grain="transactions"`, each row is a movement carrying the balance
  before and after it; the opening balance is then the *first* row's and the
  closing balance the *last* row's, which needs `order_by`: a sequence number
  or timestamp that is unique within each account. A plain date works only if
  no two movements share the first or last date.
- **Ordering uses the column, never row order.** `order_by` values must be
  numbers, real dates, or ISO dates (`2026-01-31`); text such as `1/10/2026`
  is rejected because it would sort before `1/9/2026`. Rows that tie on the
  first or last position with different balances fail rather than picking one,
  and `order_by` cannot be used with `grain="summary"`.
- **Blanks are never zero**, and currencies are never converted: name the
  `currency` column so each currency reconciles on its own.

## Not suitable when

Movements are in a different currency from the balances, the file omits some
movement types such as fees or FX, or balances are as of different dates than
the movements.

## Try it

```bash
finassert init --template cash-reconciliation --output cash-policy.yml
finassert check --config cash-policy.yml --input examples/cash.csv --html report.html
```

`examples/cash.csv` has one deliberate break: the Alpha EUR balance is 5,000
short of the expected 455,000. The report lists that group, the difference,
and its row number (3, as shown in a spreadsheet).
