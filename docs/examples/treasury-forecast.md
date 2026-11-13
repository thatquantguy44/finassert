# Weekly treasury forecast coverage and continuity

`forecast_coverage` requires every expected series and calendar week.
`cash_continuity` compares opening cash with prior closing cash only on a
complete, unique schedule. Explicit expected scope detects an entirely missing
entity, currency, scenario or forecast vintage. Neither rule generates forecasts
or establishes that liquidity is sufficient.

The synthetic example contains 208 rows: thirteen weeks for sixteen independent
vintage/entity/currency/scenario tuples. Run it from the checkout root:

```bash
finassert check --config examples/treasury/policy.yml \
  --input examples/treasury/cash-forecast.csv --html report.html
```

The policy passes both checks. `examples/treasury/failure-cases.json` describes
small reproducible mutations: missing week, missing whole series, duplicate
week, disconnected cash, and liquidity/capacity failures. The integration
tests apply these recipes. The matching `facilities.csv` is checked by the separate
`facility-pack.yml`; the legacy two-check policy does not evaluate it. Regenerate the files
with `python examples/treasury/generate.py` after installing this checkout.

## Python API

```python
from decimal import Decimal
import finassert as fa

schedule = dict(
    period_start="start",
    period_end="end",
    group_by=["entity"],
    currency="currency",
    expected_scope=[{"entity": "Alpha", "currency": "USD"}],
    first_period="2026-10-05",
    periods=2,
    row_key="id",
)
rows = [
    dict(
        id="w1",
        entity="Alpha",
        currency="USD",
        start="2026-10-05",
        end="2026-10-12",
        opening=Decimal("100"),
        closing=Decimal("90"),
    ),
    dict(
        id="w2",
        entity="Alpha",
        currency="USD",
        start="2026-10-12",
        end="2026-10-19",
        opening=Decimal("89"),
        closing=Decimal("80"),
    ),
]
report = fa.check(
    rows,
    [
        fa.forecast_coverage(**schedule),
        fa.cash_continuity(
            opening_cash="opening", closing_cash="closing", tolerance=Decimal("0.01"), **schedule
        ),
    ],
)
print(report.summary())
```

Coverage passes. Continuity fails: `w2` opens at 89 instead of prior row `w1`'s
closing 90, with difference -1. Diagnostics retain exact Decimal strings. Amount
tolerances follow the inclusive absolute/relative mathematics of the core.
Negative balances are valid; currencies are never converted or offset.

## Schedule and failure contract

- Name the currency column explicitly. Scope mappings name exactly that column
  and the `group_by` columns, with nonempty text values. Currency codes are
  explicit three-letter uppercase codes. Configuration is copied immutably.
- Dates must be ISO `YYYY-MM-DD` text. Quote `first_period` in YAML. Each week
  is `[start, end)`, exactly seven calendar days, anchored to the supplied date.
  Input order does not matter. Expected schedules are capped at 100,000 rows.
- With `row_key`, labels must be unique nonempty text; otherwise native labels
  are used. Diagnostic caps limit examples, never evaluation or total counts.
- Missing/duplicate/extra/invalid weeks fail coverage and produce a continuity
  evaluation error. Empty input fails coverage and errors continuity. Missing
  columns are evaluation errors. No gap is silently bridged.
- Blank cash fails by default; explicit `null_policy="skip"` can skip continuity
  for blanks, but `ignore` is rejected. Other unusable amounts fail. The first
  opening and last closing still require finite numeric amounts. A one-week
  series has zero adjacent comparisons after validating all inputs.

These checks do not validate within-week `opening + flows = closing`. Compose
the existing [cash reconciliation](cash-reconciliation.md) rule, grouping each
week independently. The first opening is not automatically tied to actuals.
Account-perimeter changes and nonweekly calendars require different contracts.

A skipped required check is incomplete evaluation even though the default core
report can pass skips. Applications must enforce their required check coverage.
Liquidity buffers, facility-capacity rules, accuracy measures and QuantMeridian
integration remain deferred.

## Available-cash buffer

Add `fa.minimum_cash_buffer(closing_cash="closing", restricted_cash="restricted",
minimum_buffer="minimum", **schedule)` to require closing less restricted cash
to meet a caller-supplied nonnegative per-row minimum. The three amount columns
are required; negative closing cash is allowed. Equality passes. Default tolerance
is zero; configured amount tolerance may permit a shortfall, which remains visible
in the `cash_shortfalls` diagnostics. Missing or duplicate periods error. Currency
scopes never offset; undrawn facilities are excluded. A passing result checks the
configured threshold and does not establish its business adequacy.

## Facility controls

`fa.facility_capacity` requires `facility_id`, `opening_drawn`, `draws`, `repayments`,
`closing_drawn`, `commitment`, `unavailable_amount` and `maturity_date` column names,
plus the weekly schedule arguments. Include facility identity in `expected_scope`;
keep it separate from `group_by`. All monetary components are nonnegative and in
currency major units. Repayments use positive magnitudes.

The rule checks principal identity, available commitment less closing principal,
and prior-closing/current-opening continuity. Each facility/currency stays separate.
Missing/duplicate periods error. Maturity at/before the period start requires zero
draws and closing drawn within configured tolerance; maturity strictly inside the
week errors. Maturity at period end is assessed at the next start, if supplied.
Diagnostics preserve negative headroom and both row identities for a discontinuity.
This checks period-end capacity; intraperiod peaks and legal eligibility need their
own inputs and review.

## Versioned cash/funding pack

Use `examples/treasury/cash-pack.yml` with `cash-forecast.csv` and
`examples/treasury/facility-pack.yml` with `facilities.csv`. Both pass. Cash checks
include required fields, unique IDs/weekly keys, positive operating/financing
flows, coverage, within-week cash identity, continuity and minimum available cash.
The facility policy checks required fields, unique IDs/weekly keys, explicit
coverage, principal, effective capacity, continuity and maturity.

```bash
finassert init --template treasury-cash-forecast --output my-cash-policy.yml
finassert templates --json
finassert check --config examples/treasury/cash-pack.yml \
  --input examples/treasury/cash-forecast.csv --html cash.html --xlsx cash.xlsx
finassert check --config examples/treasury/facility-pack.yml \
  --input examples/treasury/facilities.csv --html facilities.html
```

Templates contain synthetic scope/date placeholders, require caller-supplied
minimum/commitment columns and use zero default amount tolerance. Replace the
placeholders and review the full resolved policy before relying on it.
`examples/treasury/prepare.py` copies input rows and explicitly constructs
`total_inflows = receipts + financing_inflows` and
`total_outflows = payments + financing_outflows` with Decimal. Original IDs and
flow columns remain visible; no absent values become zero. Policy checks assume
these declared derivations are correct. Consumer mapping owns cross-file facility
flow linkage and initial-opening actual tie-outs.

`finassert.policy.treasury_pack_manifest()` exposes pack `treasury.cash-funding`
version 1 with required rule inventory, no optional checks, and unit/sign and
applicability assumptions. CLI `templates --json`, MCP template discovery and
release capability sidecars expose the same manifest. Required checks must be
present and evaluated; skipped/error/absent checks mean incomplete coverage.
Core outcome and severity semantics stay unchanged. MCP summaries retain the
canonical bounded diagnostics and tolerance; JSON, HTML and Excel render the same
results. These checks do not establish forecast accuracy or policy adequacy.
