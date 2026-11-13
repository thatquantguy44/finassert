# Weights, targets, and turnover

Four checks cover a rebalancing file with one row per position. Three of them
work per portfolio, so name the column that identifies each portfolio.

| Check | Catches |
|---|---|
| `in_range` | A value outside a range, such as a cash weight of 140%. Limits are inclusive, set a lowest, a highest, or both. |
| `weights_match_market_values` | Stale weights: each weight must equal its market value divided by the portfolio's NAV (or by its total market value if there is no NAV column). |
| `drift_within_band` | A weight that has drifted from its target by more than a band, and optionally total drift above a limit. **Warns by default.** |
| `turnover_within_limit` | A portfolio that traded more than its limit since the previous weights. |

```yaml
  - rule: drift_within_band
    weight: weight
    target_weight: target_weight
    band: "0.03"            # three percentage points; inclusive
    group_by: [portfolio]
    row_key: ticker
  - rule: turnover_within_limit
    weight: weight
    previous_weight: previous_weight
    sides: one_way           # no default: one_way or two_way
    maximum: "0.10"
    group_by: [portfolio]
```

`examples/rebalance-policy.yml` applies these to `examples/rebalance.csv`:

```bash
finassert check --config examples/rebalance-policy.yml --input examples/rebalance.csv --html report.html
```

Alpha has drifted from its targets by five points on two positions, which is a
**warning**: the report lists it, but the run does not fail because of it.
Beta traded 20% one way against a 10% limit, which is an **error**, so the run
fails (exit code 1) and the summary says the drift only warned.

## Conventions

- **Limits are yours.** There are no templates for them: a band, a turnover
  budget, or a range belongs to your mandate, not to the definition of a file.
  They are fractions (`0.02` is two percentage points) and inclusive.
- **Severity is configurable.** Drift defaults to `warning` because it more often
  asks for a rebalance than it signals bad data; set `severity: error` to make it
  fail the run. Every other check here defaults to `error`. A warning is always
  reported in full, and `finassert check --fail-on warning` makes warnings fail a
  pipeline without editing the policy.
- **Turnover must say what it counts.** `one_way` is half the sum of absolute
  weight changes (each unit sold funds a unit bought); `two_way` is the full sum.
  They differ by a factor of two, so there is no default.
- **Previous weights are never guessed.** A position that was not held before
  needs a previous weight of `0`, not a blank, and a position that was sold
  completely still needs its row, with a weight of `0`. A blank fails the row (or
  skips the check with `null_policy: skip`).
- **`weights_match_market_values` and NAV.** With a NAV column the base is the
  NAV, which may be on every row or some rows of a portfolio but must agree and be
  positive. Without one the base is the portfolio's total market value, so cash
  and liabilities must be rows of the file. A zero or negative base fails the
  portfolio instead of dividing.
- **Drift is absolute.** One band applies to every position, so a 2-point band is
  loose for a 1% position and tight for a 40% one. `total_limit` bounds the sum of
  absolute drifts in a portfolio.
- Blank cells are never zero, currencies are never converted, and non-numeric
  values fail even when `null_policy` is `skip`.

## Not suitable when

Weights are measured against something other than NAV or total market value
(such as gross exposure), targets are not set for every position, drift should be
measured in risk or market value, or the previous weights come from a different
date or NAV than the current ones.
