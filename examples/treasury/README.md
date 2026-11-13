# Synthetic treasury fixtures

All amounts are invented, in currency major units. No live market or book data
is used. `cash-forecast.csv` has 208 weekly summary rows across two entities,
two currencies, two scenarios and two forecast vintages. `expected-scope.json`
is independent of the input rows and is explicitly repeated in `policy.yml`.
YAML aliases are not supported. Weeks are seven calendar days with an exclusive
end. Payments are positive magnitudes and exclude financing. No currency
conversion, intercompany netting or business limit inference occurs.

```bash
finassert check --config examples/treasury/policy.yml \
  --input examples/treasury/cash-forecast.csv --html report.html
python examples/treasury/generate.py
```

The first command passes coverage and continuity. The second regenerates these
deterministic files using the installed checkout. `facilities.csv` contains a
matching revolver schedule; its draws equal forecast financing inflows. This
policy does not evaluate facilities or minimum cash buffers.

`failure-cases.json` provides compact variants. Remove selected IDs, duplicate
them with a `-copy` ID suffix, or replace the named fields with exact numeric
values. The integration tests verify all stated outcomes. Cash-shortfall and
facility-overdraw variants intentionally pass schedule/continuity while setting
up the next limit-check slice. Synthetic buffers are examples, not recommended
institutional limits. The within-week cash identity can already be checked by
combining flow columns explicitly and composing `cash_reconciles`.
