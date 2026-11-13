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
matching revolver schedule; its draws equal forecast financing inflows. The legacy
policy.yml remains a two-check coverage/continuity example. Use cash-pack.yml
and facility-pack.yml below for complete cash/funding checks.

`failure-cases.json` provides compact variants. Remove selected IDs, duplicate
them with a `-copy` ID suffix, or replace the named fields with exact numeric
values. The integration tests verify all stated outcomes. Cash-shortfall and
facility-overdraw variants pass schedule/continuity and fail the corresponding
shipped cash-buffer or facility-capacity check. Synthetic buffers are examples, not recommended
institutional limits. The within-week cash identity can already be checked by
combining flow columns explicitly and composing `cash_reconciles`.

## Cash/funding pack v1

```bash
finassert check --config examples/treasury/cash-pack.yml \
  --input examples/treasury/cash-forecast.csv --html cash.html --xlsx cash.xlsx
finassert check --config examples/treasury/facility-pack.yml \
  --input examples/treasury/facilities.csv --html facilities.html
finassert templates --json
```

`pack-manifest.json` identifies `treasury.cash-funding` version 1, required checks,
unit/sign assumptions and applicability. `prepare.py` is the inspectable mapping:
it copies rows, retains row_id, and derives total_inflows from receipts plus
financing_inflows and total_outflows from payments plus financing_outflows using
Decimal. It rejects missing/invalid or negative components; it never fills a
missing value with zero. The generated CSV retains original flow components.
Re-run preparation on user inputs before running the cash policy; checks assume
the declared combined-flow derivations are correct.

Replace every synthetic scope/date/limit/term before using the starter templates.
Review independently approved scope and the resolved policy digest, not just a
list of rule IDs. Both datasets are required for the pack; core report.passed
retains ordinary semantics. Required checks must be present and evaluated;
skipped, errored or absent checks mean incomplete coverage. Cross-file draws and
repayments must be tied to cash financing flows in the consumer mapping layer.
No forecast accuracy, debt issuance, deployment or downstream integration is added.
