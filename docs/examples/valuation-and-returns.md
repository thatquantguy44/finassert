# Market values and returns

Two row-by-row checks catch numbers that disagree with their own inputs.

## Market value equals quantity times price

```text
market_value = quantity * price * multiplier
```

```bash
finassert init --template position-valuation --output valuation-policy.yml
finassert check --config valuation-policy.yml --input examples/valuation.csv --html report.html
```

`examples/valuation.csv` has one deliberate break: TSLA is reported at 72,000
although 300 shares at 240.10 are worth 72,030, a stale price. Add the
`multiplier` column name for futures and options, and `row_key: ticker` to name
rows by ticker in the report. Shorts are negative quantities. The tolerance is
in the market value's own units; a relative part also covers prices that were
rounded before multiplying.

Not suitable when prices are quoted per 100 of par or as a percentage, when the
price and market value are in different currencies, or when the market value
includes accrued interest that the price does not.

## Reported return follows from the values

```text
return = (ending_value - beginning_value - net_flows) / beginning_value
```

```bash
finassert init --template return-reconciliation --output returns-policy.yml
finassert check --config returns-policy.yml --input examples/returns.csv --html report.html
```

`examples/returns.csv` has one deliberate break: Beta's values give a 3.0%
return but the file reports 3.5%. `return_unit` has no default, because a file
that writes 5% as `5` rather than `0.05` would otherwise be off by a factor of
100: choose `fraction` or `percent`. The tolerance is in the return's own unit.

This is the simple one-period return, so any `net_flows` are assumed to happen
at the end of the period. It does not match a time-weighted or Modified Dietz
return when money moves in or out during the period, and it does not
reconcile compounded multi-period returns. A beginning value of zero has no
return and fails rather than dividing.

In both checks a blank cell fails the row (or skips the whole check with
`null_policy: skip`); it is never read as zero.
