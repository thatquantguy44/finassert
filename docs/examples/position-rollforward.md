# Position roll-forward

`position_rolls_forward` checks that each position's quantity rolls from its
opening to its closing value:

```text
closing = opening + buys - sells + adjustments
```

```bash
finassert init --template position-rollforward --output rollforward-policy.yml
finassert check --config rollforward-policy.yml --input examples/positions-rollforward.csv --html report.html
```

`examples/positions-rollforward.csv` has one deliberate break: Beta's AAPL
closes at 310 although 250 + 50 - 0 = 300, so a trade is missing or booked twice,
or the closing quantity is stale. The report names the position (`portfolio` and
`ticker`), the observed and expected quantities, and the difference.

```python
import finassert as fa

rule = fa.position_rolls_forward(
    sell_sign="positive",  # required: there is no default
    opening_quantity="opening_quantity",
    buys="buys",
    sells="sells",
    closing_quantity="closing_quantity",
    adjustments="splits",  # optional: signed, added
    group_by=["portfolio", "ticker"],
)
```

## Conventions

- **The sell sign is required.** `positive` means quantities sold appear as
  positive numbers and are subtracted; `negative` means they appear as negative
  numbers and are added. A wrong guess would hide real breaks, so there is no
  default, and each result records the equation it checked.
- **One row per position.** Name the columns that identify a position
  (`group_by`, for example portfolio and ticker); a file is not one position.
  Rows of the same position must agree on every quantity, or the position fails
  as inconsistent. If your file lists each trade on its own row, add them up
  first.
- **Splits, transfers, and corporate actions** go in an optional `adjustments`
  column that is added to the opening quantity. Without it they appear as breaks,
  which is usually what you want to see.
- **Tolerance** is in units of the security: leave it at 0 for whole shares, and
  set it for fractional ones.
- **Blanks are never zero.** A blank quantity fails the position (or skips the
  check with `null_policy: skip`); `ignore` is not allowed, because leaving a
  trade out changes the answer.

## Not suitable when

Trades are listed on several rows with a running quantity, quantities are in
different units on different rows, or movements such as splits and transfers are
neither in the file nor in the adjustments column.
