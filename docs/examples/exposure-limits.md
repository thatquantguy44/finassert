# Exposure and position limits

Mandates and risk policies set limits that a data file can be checked against.
Three checks cover the common ones, each measured per portfolio (or per
portfolio and sector) and, if you give a base column such as the NAV, as a
fraction of that base:

| Check | Catches |
|---|---|
| `gross_within_limit` | Leverage above (or below) the mandate. Longs and shorts both add exposure: `sum(abs(value)) / base`. |
| `net_within_limit` | Directional exposure outside the mandate. Shorts offset longs: `sum(value) / base`. |
| `position_within_limit` | One position larger than allowed: `abs(value) / base` for each row. |

```yaml
version: 1
rules:
  - rule: gross_within_limit
    value: market_value
    base: nav
    maximum: "1.3"            # 130% of NAV
    group_by: [portfolio]
  - rule: position_within_limit
    value: market_value
    base: nav
    maximum: "0.1"            # no position above 10% of NAV
    group_by: [portfolio]
    row_key: ticker           # name rows by ticker in the report
```

`examples/limits-policy.yml` applies these to `examples/holdings.csv`:

```bash
finassert check --config examples/limits-policy.yml --input examples/holdings.csv --html report.html
```

Portfolio Beta fails: its JNJ line is 62.5% of NAV against a limit of 60%.
Alpha's AAPL line is exactly 60%, which passes because limits are inclusive.

## Conventions

- **Limits are yours.** There is no template for them: a limit belongs to your
  mandate, not to the definition of a holdings file. Write a limit, a minimum,
  or both; a limit is a fraction (`1.3` is 130%).
- **With a base column, exposure is a ratio of the group's base.** The base
  (such as the NAV) may be on every row or only some rows of a group, but all
  values given in a group must agree, and it must be positive. Without a base
  column the values are taken to be weights already.
- **Sector or issuer limits** are a gross check grouped by that column too:
  `group_by: [portfolio, sector]` with `base: nav`.
- **Net limits may be negative**, for a book that must be net short.
- **Blanks are never zero**, and currencies are never converted: name the
  `currency` column so each currency is checked on its own.

## Not suitable when

Derivatives are listed at market value but the limit applies to notional,
values are in several currencies without a currency column, the base is in a
different currency from the values, or the same security appears on several
rows and the limit applies to the security as a whole (combine the rows first).
