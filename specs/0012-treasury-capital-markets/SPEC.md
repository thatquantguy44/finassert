# 0012 — Treasury and capital markets validation

**Status:** R-02 cash continuity and R-03 weekly coverage implemented (initial)
on this branch; the remaining rules, consumer service and update automation
remain proposed. Proposal issue: [#13](https://github.com/thatquantguy44/finassert/issues/13).
**Updated:** 2026-10-17
**Implementation plan:** [PLAN.md](PLAN.md)
**Progress ledger:** [TASKS.md](TASKS.md)
**Deferred consumer design:** [QuantMeridian integration](quantmeridian/SPEC.md)

## Problem and intended outcome

Treasury forecasts and financing schedules can contain plausible balances while
omitting periods, mixing currencies, double-counting financing, or exceeding
available funding. Extend finassert with deterministic checks for these errors,
starting with a supplied 13-week cash forecast. Preserve the existing model:
immutable rules, caller-owned inputs, explicit assumptions, bounded diagnostics,
and a dependency-free core.

QuantMeridian is the intended first consumer. Its integration design is staged
here because its repository has active concurrent work. Implementation of the
integration and all deployment automation belong in QuantMeridian later. This
proposal makes no changes to either QuantMeridian repository.

## Inspected baseline and ownership

Source review, not an execution or production-readiness assessment:

| Source | Reviewed revision | Relevant finding |
| --- | --- | --- |
| finassert | `19be7eda7400412b2d46bf3e5cd6c4bfc8f537c5` | Python >=3.11; metadata version 0.1.0; README says pre-alpha and no claimed PyPI release |
| QuantMeridian | `66b218a030ebc0b2922fc6657aa92dad92e79eeb` | Vite/React/TypeScript with Node API registry and Python companion services |
| QuantMeridian-Core | README reviewed on 2026-10-17 | Generated subset; direct edits may be overwritten |

Existing finassert capabilities include `accounting.cash_reconciles`, grouped
cash identities with explicit outflow signs, required fields, duplicate checks,
ranges, exposure checks, Decimal-aware tolerances, policy catalogs, and JSON/HTML
reports. These are reused, not reimplemented. Treasury continuity, explicit
forecast coverage, funding capacity, and forecast-error rules below are proposed.

Ownership:

- finassert owns generally applicable equations, rule factories, catalog entries,
  policy support, tests, examples, and distribution artifacts.
- QuantMeridian owns input mapping, application policies, UI, authorization,
  service hosting, deployment, dependency-update automation, and operational use.
- Neither project supplies live bank balances, institution-specific limits,
  legal interpretations, or FX rates through this work.

Specifications [0002](../0002-financial-invariants.md),
[0003](../0003-numerical-tolerances.md),
[0004](../0004-dataframe-adapters.md),
[0005](../0005-reporting-and-diagnostics.md),
[0007](../0007-cli-and-pipeline-integration.md), and
[0011](../0011-non-technical-interfaces.md) remain authoritative. This adds the
`treasury` rule family. Collateral and securities-financing rules retain the
families reserved by 0002. Typed money and FX under 0008 remain proposed; v1
requires caller-declared units and separate currency groups without conversion.

## Scope and user workflows

### First delivery: supplied cash forecast

1. Load a synthetic example or an explicitly mapped user export.
2. Declare expected entities, currencies, scenarios, forecast vintage, first
   week, 13-week horizon, signs, units, and materiality.
3. Check identity, continuity, coverage, liquidity buffers, and funding capacity.
4. Inspect exceptions with row/group identity, equation, observed/expected
   values, tolerance, and the number of omitted diagnostics.
5. Export the policy and report; obtain equivalent outcomes through Python and
   CLI. Forecast-versus-actual evaluation is a subsequent slice of the pack.

The pack validates a forecast supplied by the caller. Forecast generation,
statistical training, optimization, transactions, bank connectivity, and
regulatory compliance certification are outside scope. Optional diagnostic
calculations must not silently replace missing input balances.

### Following delivery: financing schedules

Debt principal schedules and issuance-proceeds checks come next. Fixed-rate
interest, haircut-adjusted collateral, repo, and FX settlement checks are later
bounded extensions, with their own conventions and tests before implementation.
No full derivatives pricing, day-count library, holiday calendar, covenant
interpretation, or LCR/NSFR compliance calculation is introduced.

## Canonical example contracts

Rules accept configured columns through existing adapter contracts. The names
below describe example files, not mandatory names for every caller.

### Cash forecast

One row represents one weekly summary for:
`(forecast_as_of, entity_id, currency, scenario_id, period_start)`.

| Field | Contract |
| --- | --- |
| `row_id` | Nonempty stable diagnostic identifier, unique within the input |
| `forecast_as_of` | ISO date identifying the forecast vintage |
| `entity_id`, `scenario_id` | Nonempty caller-owned identifiers |
| `currency` | Explicit uppercase currency code; no inference or conversion |
| `period_start`, `period_end` | ISO dates; end is exclusive and start + 7 calendar days |
| `opening_cash`, `closing_cash` | Finite amounts in currency major units; negative balances allowed |
| `receipts`, `payments` | Finite amounts; receipts nonnegative; payment sign explicitly configured |
| `financing_inflows`, `financing_outflows` | Explicit draw/proceeds and principal-repayment totals; same payment sign contract |
| `cash_adjustments` | Signed finite cash adjustment, separate from receipts/payments |
| `restricted_cash`, `minimum_buffer` | Nonnegative amounts in the row's currency; buffer supplied by caller |

Missing values are never interpreted as zero. The example includes explicit
zeroes for optional business components so its policy can require every field.
Generic rule factories may omit an optional component only through explicit
configuration, recorded in diagnostics. Invalid numeric strings, booleans, NaN,
infinities, and mismatched units cannot produce a passing check.

`closing_cash` includes restricted cash. `restricted_cash` is an earmarked
nonnegative amount and may exceed a negative or depleted closing balance; the
liquidity shortfall remains visible. The available-cash measure is therefore
`closing_cash - restricted_cash`. Facilities are not added to this measure.
Receipts/payments exclude financing flows. Intercompany transfers are not netted
across entities, and projected drawings cannot also be counted as undrawn funds.

The expected scope is supplied independently of the file as explicit
`(forecast_as_of, entity_id, currency, scenario_id)` tuples. Do not derive it
only from observed rows: an entirely missing entity must be detectable.

### Facility schedule

One row represents
`(forecast_as_of, entity_id, currency, scenario_id, facility_id, period_start)`
and carries `period_end`, `opening_drawn`, `draws`, `repayments`,
`closing_drawn`, `commitment`, `unavailable_amount`, and `maturity_date`.
Amounts are nonnegative; repayment magnitudes are positive. Facility dimensions
must match the cash forecast. `commitment` is that period's effective contractual
cap; `unavailable_amount` is a disjoint caller-supplied reduction for conditions,
reserves, or other limitations, excluding drawn amounts. Require
`unavailable_amount <= commitment`.

Cross-file linkage belongs to the consumer mapping layer: aggregate facility
draws/repayments by the cash key and reconcile to forecast financing totals.
The adapter must report unmatched keys, never perform a silent inner join.

## Rule inventory and semantics

R-02 and R-03 are public exports; the other new names below remain proposed IDs. Each rule must
state its input mapping, applicable grain, units, signs, null/empty behavior,
tolerance basis, and inappropriate uses in its catalog entry before shipping.

### R-01: cash identity — reuse `accounting.cash_reconciles`

For each complete cash row key:

```text
closing = opening + receipts - payments
          + financing_inflows - financing_outflows + cash_adjustments
```

For negative-signed outflows add those outflows instead. The example adapter
constructs explicit combined inflow/outflow columns using Decimal; records the
source mappings; then calls the existing cash rule with `grain="summary"`, the
complete non-currency group key, `currency`, `row_key`, and explicit outflow sign.
Duplicate keys are checked separately before evaluation; `require_unique`
aggregation alone does not prove there is exactly one input row. Do not group
all weeks together: offsetting weekly errors must remain visible.

### R-02: `treasury.cash_continuity`

Within each expected vintage/entity/currency/scenario series, sort by unique
period start and compare `opening[t]` with `closing[t-1]` using 0003 tolerance.
No comparison crosses vintages, entities, currencies, or scenarios. Coverage
R-03 is a prerequisite: missing or duplicate periods block continuity rather
than comparing across the gap. The first period requires no prior-period match;
a separate actual-opening tie-out needs a supplied actual balance. This rule is
inappropriate across a caller-declared account perimeter or currency change.

### R-03: `treasury.forecast_coverage`

Require exactly one row for every expected scope tuple and weekly bucket in the
configured horizon, and no unexpected tuples or buckets. The first date is an
explicit week anchor, not an inferred Monday or business day. Each interval is
`[start, start + 7 days)`; duplicates, overlaps, gaps, invalid bounds, and missing
entire series produce diagnostics. Input order does not affect the result.
Calendar membership has no monetary tolerance. Daily/business-day schedules
require a separate explicit period contract and are deferred.

### R-04: `treasury.minimum_cash_buffer`

For each cash row, `available_cash = closing_cash - restricted_cash` and require
`available_cash >= minimum_buffer`. Equality passes. The default tolerance is
zero; an explicitly configured 0003 tolerance permits a shortfall only if
`Tolerance.is_close(available_cash, minimum_buffer)`. Report the actual shortfall
even when it is within materiality. Do not treat restricted cash as transferable
or count undrawn facilities as cash. Policy adequacy is caller-owned.

### R-05: `treasury.facility_capacity`

For each facility period:

```text
closing_drawn = opening_drawn + draws - repayments
available_commitment = commitment - unavailable_amount
headroom = available_commitment - closing_drawn
```

Require the principal identity within 0003 tolerance, nonnegative components,
`unavailable_amount <= commitment`, and `closing_drawn <= available_commitment`.
Prior closing drawn must match next opening drawn across complete facility
periods. Limits are inclusive; amount tolerances are explicit and default zero.
If `maturity_date <= period_start`, require no draws and zero closing drawn.
If `period_start < maturity_date < period_end`, report unsupported intraperiod
maturity as an evaluation error: a weekly closing balance cannot establish
repayment on the maturity date. Maturity exactly at period end is assessed at
the next period start. This does not validate conditional draw eligibility,
legal availability, intraperiod peak usage, or a borrowing base from documents.

### R-06: `treasury.forecast_error_within_limit`

Evaluate matched forecast/actual pairs for one explicitly selected metric,
vintage, horizon, entity, currency, scenario, and period. Generic matching stays
outside the single-table core: the caller supplies paired columns and a match
status; no silent dropping, summing, or many-to-many matching is permitted.
Actuals include a known-as-of timestamp; forecast vintage must precede the
measured period and actuals must have been available by the evaluation cutoff.

```text
signed_error = forecast - actual
absolute_error = abs(signed_error)
relative_error = absolute_error / abs(actual)    # only if actual != 0
```

Configure an absolute limit, a fractional relative limit, or both. If both are
configured, explicitly choose `all` or `any` for limit combination; the example
uses `all`. Boundaries are inclusive with zero additional tolerance, avoiding
two layers of error allowance. For `actual == 0`, relative error is undefined;
require explicit `zero_actual="absolute_only"` with an absolute limit, or
`zero_actual="error"`. Never substitute an epsilon or emit infinity. Report
missing actuals as incomplete evaluation, not zero error. No MAPE aggregation
or claim of predictive quality follows from identity checks alone.

### Following rule set

| ID | Equation and scope | Required conventions and limits |
| --- | --- | --- |
| R-07 `securities_financing.debt_principal_reconciles` | Closing principal = opening + issuance/draws - repayments + signed noncash principal adjustments, per instrument/currency/period; continuity checked separately | Positive repayment magnitudes; instrument lifecycle and noncash adjustments explicit; no inference of amortized cost or legal debt capacity |
| R-08 `securities_financing.issuance_proceeds_reconcile` | Gross proceeds = face amount × issue price fraction; net proceeds = gross - positive fees + signed cash adjustments, per issuance/currency/settlement | Quote unit must explicitly be fraction or percent of par; issue discount is embedded in price and is not subtracted twice; accrued interest belongs in an explicitly identified adjustment |
| R-09 `securities_financing.interest_reconciles` | Simple interest = principal × annual fractional rate × supplied year fraction, per constant-principal/rate accrual segment | Caller supplies day-count convention, accrual bounds, and year fraction; no implied calendar, compounding, floating reset, or negative-rate floor |
| R-10 `collateral.coverage_within_limit` | Sum of eligible collateral value × (1 - haircut) >= required collateral within each explicitly permitted netting set and currency | Haircut fraction in [0,1]; required collateral includes caller-specified margin; nonnegative eligible value; no inferred eligibility, FX, reuse rights, or legal netting |
| R-11 FX settlement pair validation | Quote amount = base amount × supplied quote-per-base rate; both currency legs and settlement dates match declared trade terms | Positive finite supplied rate and provenance; direction and signed-leg convention explicit; no fetched rates or assumed spot-date calendar |

R-07–R-10 require the same amount-tolerance and diagnostic contracts as R-01–R-05.
R-11 remains a design candidate without a reserved public ID until 0008's
provenance and leg contract are amended. Repo lifecycle is a later composition
of cash, principal, interest, and collateral checks, not a new pricing engine.

## Common API and result requirements

Factories remain keyword-only immutable configurations and evaluate through
`check`. New rules use existing `ValidationResult`/`ValidationReport` and outcome
enums. No new core report status is introduced. Initial public factory shape:

```python
# expected_scope is supplied independently of the observed file.
cash_continuity(
    opening_cash="opening_cash",
    closing_cash="closing_cash",
    period_start="period_start",
    period_end="period_end",
    group_by=["forecast_as_of", "entity_id", "scenario_id"],
    currency="currency",
    expected_scope=[
        {
            "forecast_as_of": "2026-10-01",
            "entity_id": "Alpha",
            "scenario_id": "base",
            "currency": "USD",
        }
    ],
    first_period="2026-10-05",
    row_key="row_id",
    tolerance=Tolerance(absolute=Decimal("0.01")),
)
```

The shared weekly arguments are now finalized: `period_start`, `period_end`,
`group_by`, `currency`, `expected_scope`, and `first_period` are required.
`expected_scope` is a nonempty sequence of text mappings naming exactly the
physical group and currency columns; it is copied into immutable tuples.
`periods=13`, `row_key=None`, `severity="error"`, and `max_violations=20` are
optional. Currency is mandatory and uses explicit uppercase three-letter codes.
Dates are ISO YYYY-MM-DD text, including the first anchor. The expected schedule
is capped at 100,000 rows. Explicit row IDs must be unique nonempty text.

`forecast_coverage` takes those shared arguments. `cash_continuity` additionally
requires `opening_cash` and `closing_cash`, with `tolerance=0` and
`null_policy="fail"` (only `fail`/`skip` supported). It validates coverage
independently rather than relying on a prior engine result. All cash cells,
including first opening and last closing, require finite numeric values.
Other rule signatures remain proposed. Policy kinds `text` and `records` are
additive; records round-trip through YAML/JSON and the browser editor.

- Valid, complete inputs breaching a financial limit produce `failed`.
- Invalid mappings/configuration are rejected before evaluation. Missing
  columns, ambiguous prerequisite data, unsupported units/grains, and unusable
  pairing produce evaluation errors. Missing observed values follow an explicit
  documented null policy; the shipped treasury pack uses `fail`.
- Empty expected scope is invalid configuration; a nonempty expected scope with
  zero rows fails coverage. Dependent checks cannot then pass vacuously.
- Core skip behavior is unchanged. The consumer must label a run incomplete
  when any required check is skipped, absent, or errored, even if core
  `report.passed` is true. Warning failures remain visible and are evaluated
  against the consumer's explicit severity threshold.
- Results retain stable rule ID, severity, equation, signs, units, group key,
  current/prior row IDs where applicable, observed, expected, difference,
  tolerance, violation count, and diagnostic truncation. Missing whole groups
  have expected key/period identity even without a row ID.
- Decimal values serialize as strings. No implicit scaling, global rounding,
  mutation, FX conversion, date coercion, or float conversion of money.
- Each rule caps reported violations while evaluating the entire bounded input.
  A cap affects examples shown, never the outcome or total violation count.

## Acceptance criteria

| ID | Required evidence |
| --- | --- |
| AC-01 | Existing cash rule checks each period independently, explicit signs work, and offsetting weekly breaks both remain visible |
| AC-02 | Continuity catches a changed opening balance with current/prior identities; shuffled input produces equivalent findings |
| AC-03 | Coverage catches a missing whole entity, missing week, duplicate, overlap, extra bucket, and mixed vintage without silently repairing input |
| AC-04 | Buffer exact boundary passes; Decimal shortfall and restricted-cash deficit are correctly diagnosed; currencies never offset |
| AC-05 | Facility identity/capacity/continuity and maturity boundaries pass/fail as specified; intraperiod maturity errors explicitly |
| AC-06 | Forecast error handles positive/negative/zero actuals, `all`/`any`, missing pairs, duplicate pairing, and no look-ahead |
| AC-07 | Null, empty, boolean, non-finite, precision, large value, sign, and exact tolerance boundaries are covered without changing prior rule behavior |
| AC-08 | Every new shipped rule has catalog metadata, YAML policy support, synthetic passing/failing examples, and Python/CLI report parity |
| AC-09 | Core imports gain no mandatory dependency; existing tests, typing, formatting, docs, package-build and distribution verification pass |
| AC-10 | Debt and issuance examples catch noncash-principal omissions and double-subtracted discounts; later interest/collateral rules document their narrower applicability |
| AC-11 | Consumer contract prevents empty/skipped/partial evaluation being shown as validated; engine/policy/contract identities are retained |
| AC-12 | Updating the consumer pin produces one reviewable tested PR and rollback restores the previous compatible artifact bundle |
| AC-13 | No QuantMeridian code or workflow is changed by this specification delivery; deferred documents have an explicit move plan |

## Delivery and dependencies

Ship R-01–R-05 first, R-06 next, then R-07–R-08. R-09–R-11 require focused
follow-up design before implementation. Do not present proposed rules as
available in catalogs or templates until their acceptance evidence exists.
Consumer integration has a bootstrap stage with existing rules and a separate
treasury-pack stage gated on the upstream release/commit supplying R-02–R-05.

Before substantial API/financial-semantics implementation, open the proposal
issue required by CONTRIBUTING.md and link it to this specification. This
documentation branch itself changes no API. There is no requirement to pause
routine implementation solely because this document is labelled Proposed;
implementation authority and production rollout remain separate decisions.
