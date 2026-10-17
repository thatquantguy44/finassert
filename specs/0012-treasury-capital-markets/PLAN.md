# Implementation plan — treasury and capital markets

**Status:** Proposed; no implementation started.
**Updated:** 2026-10-17
**Requirements:** [SPEC.md](SPEC.md)
**Ledger:** [TASKS.md](TASKS.md)

## Repository boundaries

All current changes are documentation in finassert. General financial checks
belong in this repository. The [QuantMeridian staging document](quantmeridian/SPEC.md)
describes future consumer work and must not introduce FastAPI, Node, hosted
services, application authorization, or deployment credentials into finassert.
This preserves 0011's exclusion of hosted services from its interface scope.

## Slice A — freeze contracts and examples

1. Open the API/financial-semantics proposal issue specified in CONTRIBUTING.md.
2. Agree proposed `treasury` family IDs, keyword factories, prerequisite outcome
   behavior, coverage configuration, and metadata limits. Reuse 0003 mathematics.
3. Add one source-controlled synthetic fixture set: a passing 13-week cash
   forecast, expected scope, facility schedule, and explicit policy assumptions.
   Include two entities, two currencies, base/downside scenarios, and separate
   forecast vintages to prove isolation. No business limit is a default.
4. Create focused failing variants, including equal-and-opposite weekly breaks,
   entirely absent series, a duplicate row, and a facility overdraw. Preserve
   stable row IDs so tests can assert economically meaningful diagnostics.

## Slice B — upstream cash and funding pack

- Add the new immutable rule implementations in `src/finassert/rules/treasury.py`
  using existing adapters/grouping helpers where their contracts fit. Extract a
  small shared period-validation helper only when it has real reuse; do not
  expand every existing rule's contract.
- R-03 coverage builds a bounded expected-key/bucket set from explicit caller
  configuration. Complexity should be proportional to observed plus expected
  rows; do not materialize an unbounded dimension cross product. Validate
  configuration bounds and report absent groups with expected identities.
- R-02 continuity operates only on unique complete weekly series, independent
  of input ordering. Invalid prerequisite series generate an error diagnostic
  and cannot yield passing continuity through skipped comparisons.
- R-04 validates amounts/units and computes the buffer comparison with Decimal.
- R-05 validates facility schedules, then checks principal identity, period
  continuity, effective capacity, and maturity. Do not clamp negative headroom.
- R-01 uses existing `cash_reconciles` with explicit derived inflow/outflow
  columns in the example/consumer adapter, keeping financial derivations
  inspectable. Document financing inclusion and retain original row identities.
- Add exports, catalog metadata, policy parameter decoding, synthetic examples,
  and API documentation together with each shipped rule. Treasury policies use
  strict required fields and duplicate/coverage checks before dependent rules.
- Catalog/templates must declare required versus optional checks and unit/sign
  assumptions in a versioned pack manifest. Consumers may add strict coverage
  semantics without changing core report outcomes.

## Slice C — forecast accuracy

R-06 consumes one paired table. A documented caller adapter joins forecast to
actuals using validated unique keys, left-preserves all expected forecast rows,
and records unmatched/ambiguous keys and actual availability timestamps. It
selects the forecast vintage before looking at outcomes. Test metric selection,
zero denominators, negative actuals, two limit-combination modes, missing
actuals, actual revisions, and known-as-of cutoff handling. No new pandas
dependency enters the core and no MAPE summary is implied.

## Slice D — capital markets

Implement debt principal and issuance proceeds as separate bounded rules in the
existing `securities_financing` family. Amend 0002 with their final equations
and applicability. Synthetic issue-price examples cover price quoted as 98
percent and 0.98 fraction producing identical gross proceeds, with discount
not subtracted again. Debt examples distinguish cash repayments from noncash
principal changes. Interest, collateral, and FX require focused amendments and
their own acceptance fixtures before becoming implementation tasks.

## Slice E — distribution and consumer handoff

1. Run repository checks for each implementation slice, including the commands
   in CONTRIBUTING.md and relevant browser/policy regressions.
2. Build and verify wheel/sdist. Record the immutable source commit, package
   version, rule/pack manifest and artifact hash; metadata version alone does
   not identify unreleased source builds.
3. Move the deferred consumer document into QuantMeridian using its next free
   spec number at that time. Do not assume `spec011` is available later.
4. Bootstrap the consumer with existing cash checks. Enable the treasury pack
   only after R-02–R-05 exist at its pinned revision and compatibility tests pass.
5. Consumer update automation comes after the first manual pin/integration is
   proven. Run against synthetic fixtures and retain the old artifact bundle
   for rollback; do not fetch repository code at service startup.

## Validation plan

Tests must distinguish arithmetic correctness from completeness and policy
adequacy. Assert rule identities, affected groups/rows, totals, truncation,
outcomes, severity, unchanged inputs, and Decimal serialization. Property tests
may generate complete schedules and introduce a single known break. Reordering
rows must not change financial results; diagnostic ordering must be stable.

Run the appropriate checks already defined by the repository:

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy src/finassert
uv run mkdocs build --strict
uv build
uv run python scripts/verify_dist.py dist
```

For this specification-only delivery, check local Markdown links, requirement
and task coverage, synthetic arithmetic stated in documents, whitespace, and
remote changed-file scope. Runtime tests are not evidence for unimplemented
capabilities and need not be added for this documentation change.

## Risks and treatment

| Risk | Treatment |
| --- | --- |
| Combined balances hide entity/currency shortages | Explicit expected scope; never aggregate across currencies or assume transfers |
| Closing facility usage conceals an intraperiod peak | State period-end-only scope; intraperiod capacity requires finer-grain input |
| Changing APIs under the same pre-alpha version | Pin source commit plus immutable artifact digest and test contracts |
| New rules become visible but are not mapped or enabled | Versioned pack allowlist; separate engine upgrade from policy adoption |
| Actual revisions create misleading forecast scores | Preserve vintage, actual availability/cutoff, and matching policy |
| Active QuantMeridian development diverges from this design | Rebase/reinspect at migration; preserve decisions, revise paths and schemas |

## Working decisions

Weekly summaries with an explicit anchor are the initial grain. All operational
limits are supplied by users. Forecast generation and live feeds remain outside
scope. Upstream and consumer work use separate future PRs. Consumer automation
opens PRs but does not auto-merge or deploy by default; changing that policy
requires a deliberate repository configuration change, not a runtime flag in
finassert. These are documented defaults, not unresolved blockers to writing
the specification.
