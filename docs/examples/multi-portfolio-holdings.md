# Holdings of several portfolios

Files from custodians and order systems usually hold many portfolios at once.
Four checks cover the common mistakes, each reported per portfolio:

| Check | Catches |
|---|---|
| `required_fields` | A blank portfolio, ticker, weight, or market value, usually an incomplete export. |
| `no_duplicates` | The same security twice in one portfolio, usually a pasted or doubled row. |
| `weights_sum_to_one` with `group_by` | A portfolio whose weights do not add up to 1. |
| `nav_reconciles` | A portfolio whose holdings do not add up to its NAV. |

```bash
finassert init --template multi-portfolio-holdings --output holdings-policy.yml
finassert check --config holdings-policy.yml --input examples/holdings.csv --html report.html
```

`examples/holdings.csv` has one deliberate break: portfolio Beta's weights add
up to 0.8 because they were not refreshed after prices moved, although its
market values do add up to its NAV. Append a second `Alpha,MSFT` row to see
`no_duplicates` fail, or blank a ticker to see `required_fields` fail.

## Assumptions to confirm

The template lists these in the policy file itself: each row is one position of
one portfolio, including cash and liabilities; a security appears once per
portfolio (combine tax lots first); weights are fractions of NAV; market values
and NAV are in each portfolio's base currency; liabilities and short positions
are negative.

Weights are checked without assuming a long-only mandate. Add a `non_negative`
check on the weight column if your portfolios are long-only.
