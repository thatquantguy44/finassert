# 0020 — Performance and backtest integrity

**Status:** Proposed. The first milestone specifies a performance workbook,
reference calculations, and validation. Later milestones cover point-in-time
backtest evidence and portfolio optimization.

## Problem statement

An analyst can report a plausible return while omitting a month, compounding the
wrong benchmark, or mixing percentages with fractions. A backtest can reconcile
arithmetically even when it relies on data published after a decision. A solver
can return weights that violate the constraints the analyst intended to enforce.
Each problem needs its own evidence and a correction the analyst can make.

## Motivation and use cases

The first user is a portfolio or research analyst working in Excel. They can build
a performance report from supplied periodic returns, audit an existing report,
correct a discrepancy at its source, and reproduce the check in Python or CI.
The same workflow also applies to returns exported by a backtest. The first
milestone assesses the return series and its reporting math. Coverage of the
backtest's decision inputs begins in the second milestone.

## Goals

- **R-01 — Declare the comparison.** Require a strategy, a benchmark, a shared
  currency, a window, return units, valuation conventions, and documented fee
  treatment. Show these alongside results.
- **R-02 — Verify coverage.** Check both series against the declared monthly
  window. Identify duplicate, missing, unexpected, or invalid periods and
  blank returns before calculating linked or annualized figures.
- **R-03 — Calculate reference performance.** From valid inputs, independently
  compute monthly active return, cumulative strategy and benchmark returns,
  their cumulative difference, annualized geometric returns, and annualized
  tracking error according to the [calculation contract](#calculations).
- **R-04 — Check reported results.** Tie reported cumulative strategy and
  benchmark returns to the reference calculations by month. Retain observed
  and expected values, the difference, applied tolerance, and source row.
  A discrepancy in an early month must never seed later calculations.
- **R-05 — Deliver a reproducible workflow.** Provide a worked Excel workbook,
  a matching starter policy, and a Python/CLI example using the same fixture.
  Export the declared assumptions, policy and source identity, and bounded
  diagnostics. Each blocking issue explains what to inspect or correct.

## Non-goals

The first milestone begins with supplied periodic total returns. Cash-flow and
NAV reconstruction, instrument-level attribution, model fitting, live market
data, and trade execution are outside its scope. Geometric linking of supplied
returns is distinct from deriving cash-flow-adjusted returns. A later method
proposal must specify valuation timing and flow evidence for time-weighted
return or Modified Dietz. [CFA Institute's GIPS Standards Handbook for Firms](https://www.gipsstandards.org/standards/gips-standards-for-firms/gips-standards-handbook-for-firms/)

## Proposed architecture

The calculation path preflights the inputs and returns a reference series plus
summary measures. The audit path also accepts the reported cumulative columns
and evaluates them with registered rules. A blank report can use the calculation
path to populate a separate reference output. An audit needs a candidate report
from the user or demo fixture, with expected values calculated from period
returns alone. The engine shares the preflight and linking logic across both
paths and never changes source cells.

Use the existing policy catalog, CLI validation command, report formats,
workbook source binding, and navigation when they fit the contract. The first
Excel workbook uses one table that can be bound by the existing add-in. The
initial Excel calculation example uses visible formulas, with independent
Python reference calculations and an add-in validation run for comparison.

## Public API design

The proposed Python interface takes the mapped return series and declared
comparison settings and returns structured reference rows and summary measures.
P-02 proposes `monthly_performance_reference(...)` for calculation and one
composite `monthly_performance_audit(...)` rule for coverage, input validation,
and reported cumulative tie-outs. The composite rule keeps the comparison
settings in one policy entry and reports reason-coded, bounded diagnostics.
The user confirmed that these checks remain one composite rule in one policy
entry. The existing CLI runs the audit policy on CSV or XLSX. The factory
identifier is `monthly_performance_audit`, its stable rule ID is
`performance.monthly_performance_audit`, and it returns the existing
`ValidationResult` type. Its required and optional parameter spellings are
defined in the registered catalog factory. P-03 acceptance verified the
reference calculator; P-04 implemented and registered the composite rule,
starter policy, and report parameter export. Workbook and native Excel parity
remain in P-05/P-06.
The Python example covers reference calculation and export. A dedicated CLI
calculator command is deferred.

The P-03 reference calculator is:

```python
from finassert import monthly_performance_reference

reference = monthly_performance_reference(
    data,
    period_end="period_end",
    strategy_return="strategy_return",
    benchmark_return="benchmark_return",
    window_start="2024-01-31",
    window_end="2024-12-31",
    return_unit="fraction",
    row_key="source_row_id",
)
```

It returns a `MonthlyPerformanceReference` with the declared window and column
mapping, chronological `MonthlyPerformancePeriod` rows, a
`MonthlyPerformanceSummary`, and bounded reason-coded
`MonthlyPerformanceIssue` examples with complete counts by issue code. The
`max_violations` argument defaults to 20. When any input or coverage issue
blocks the window, `summary` is `None`, no partial reference rows are returned,
and the issue counts still cover the complete input scan. Result types provide
`to_dict()` methods that preserve Decimal values as text.

The version-1 policy format already stores and hashes typed rule parameters.
Human-readable `assumptions` remain explanatory prose. The user requires full
parameter traceability. Artifacts therefore expose `policy.rules[*].parameters`
for values explicitly configured and `policy.rules[*].effective_parameters`
for the complete typed set used after catalog defaults and schema normalization.
Include mapping, window, unit, tolerance, comparison, severity, diagnostic-cap,
and other accepted rule parameters, including when a rule skips or errors.
Preserve Decimal values as exact text. `policy.digest` keeps its existing
meaning as the digest of the configured version-1 policy; artifact schema 1 is
extended additively. Specifications 0005 and 0007 own this serialization
contract, and P-04 implements it. Credentials must not be stored in policy
parameters.

## Data contracts

The first release supports one strategy and one benchmark per input table.
One row represents a calendar month. A reporting window names its first and
last month inclusively, using canonical month-end keys. The expected month
set comes from that window, including both endpoints. Source row order is
arbitrary. Join separate source exports by month with a coverage-preserving
merge that makes missing sides visible before audit.

| Canonical field | Meaning |
|---|---|
| `period_end` | An ISO date or an Excel date that resolves to the last calendar day of the month. Source valuation may follow a declared month-end convention. |
| `strategy_return` | Supplied simple periodic total return for the strategy. |
| `benchmark_return` | Supplied simple periodic total return for the declared benchmark for the same period. |
| `reported_strategy_cumulative` | Optional for calculation and required for audit. Linked strategy return from the declared first month through this row. |
| `reported_benchmark_cumulative` | Optional for calculation and required for audit. Linked benchmark return over the same window. |

The effective policy or required run settings record strategy and benchmark IDs,
window, base currency, valuation convention, fee disclosure for each series,
and input units. Units are explicitly selected as fraction or percent, once for
the periodic columns and once for the reported columns. The analyst supplies the
benchmark and fee disclosures. The return columns alone cannot verify currency
or fee metadata. A stable source row identity survives chronological
sorting and is retained in diagnostics. The implementation must prove that
required metadata survives export and replay before calling the template ready.

### Calculations

The reference uses decimal fractions internally. `s_i` and `b_i` denote the
strategy and benchmark simple returns for month `i`.

| Measure | Defined calculation |
|---|---|
| Monthly active return | `s_i - b_i`. |
| Cumulative return | `product(1 + r_i) - 1` for each series, starting from wealth of 1 immediately before the first month. |
| Cumulative return difference | Strategy cumulative return minus benchmark cumulative return. |
| Annualized geometric return | `(1 + cumulative_return)^(12/n) - 1` for each series, reported over at least 12 complete months. |
| Annualized tracking error | Sample standard deviation of the paired monthly active returns (`n - 1` denominator), multiplied by `sqrt(12)`, available over at least two complete months. This is a descriptive scaling convention for monthly observations. |

For example, strategy returns of `10%`, `-10%`, and `2%` link to `0.98%`.
Benchmark returns of `2%`, `0%`, and `1%` link to `3.02%`. The cumulative
return difference is `-2.04` percentage points. Annualized geometric returns
are unavailable for that three-month window.

## Financial and numerical edge cases

- Treat zero returns as observations. Block blanks, non-finite values,
  malformed dates, non-month-end keys, and returns at or below `-100%` in this
  positive-wealth workflow. A total-loss series requires explicit lifecycle rules.
- Use exact calendar keys for period matching and the existing explicit Excel
  date-system interpretation. Never silently shift a row to another month,
  impute a missing side, or change return units based on magnitude.
- Convert supported finite inputs through their shortest decimal text. Normalize
  percent inputs to decimal fractions by exact division by 100. For new
  calculations use a local Decimal context of 50 significant digits with
  `ROUND_HALF_EVEN`, including annualized geometric returns and tracking error.
  Keep full calculated precision in results and exports; spreadsheet display
  formats do not affect calculation or comparison.
- Apply existing inclusive finassert tolerance semantics using a required
  absolute allowance in fractional-return units and relative tolerance zero.
  For example, `0.0001` is one basis point. Exact equality at the allowance
  passes; any larger difference fails. Compare normalized fractions, never
  display-rounded percentages.
- Use a separate absolute Decimal bound of `1e-12` in return fractions for
  Excel/Python parity evidence. This numeric parity bound does not replace or
  alter the analyst-selected financial allowance.
- Zero tracking error is valid for identical active returns across two or more
  periods. Insufficient history produces an unavailable metric with its reason
  and does not prevent cumulative checks on otherwise complete inputs.

## Failure semantics

- Reject invalid settings or mappings before evaluation. Invalid, duplicate,
  outside-window, or missing observations produce blocking findings. Dependent
  full-window calculations are unavailable when coverage or returns are invalid.
- A reported cumulative value outside the configured tolerance fails the audit
  even when reference calculations succeed. Missing or malformed report values
  are blocking audit findings. Reference-only runs do not evaluate report tie-outs.
- Report execution errors through the existing engine outcome, distinct from a
  financial mismatch. Keep report caps, total violation counts, source identity,
  and Excel freshness/revalidation behavior in sync with existing contracts.

## Implementation milestones

1. **Performance workbook and audit.** Deliver R-01 through R-05, with Excel
   navigation and CLI parity on a synthetic fixture. The [plan](plan.md),
   [tasks](tasks.md), and [roadmap](roadmap.md) give implementation order.
2. **Point-in-time backtest evidence.** Proposed. Audit a supplied decision log
   using versioned source IDs, UTC data-availability and decision times, and an
   independently provided universe for each rebalance. Separate observation date
   from availability. Flag inputs or revisions available only after a decision,
   absent required universe data, and training labels whose horizons extend into
   evaluation. Missing evidence leaves the corresponding assurance incomplete.
   Add a worked walk-forward example that records training and evaluation dates.
3. **Optimization assurance and reference implementation.** Proposed. Start
   with long-only, fully invested minimum variance using a caller-supplied
   asset universe, covariance and bounds. Validate asset alignment, units,
   symmetry, positive semidefiniteness, candidate constraint residuals and
   independently recomputed `wᵀΣw`. Include a two-asset analytical example and
   an infeasible set of bounds. Distinguish a feasible candidate, certified
   optimality evidence where available, and solver failure or infeasibility.
   Then provide a small reproducible Python example that produces candidate
   weights and runs the same independent checks. Add expected-return targets,
   turnover, transaction costs, and exposure controls after their methodology
   and constraints are specified. [CVX portfolio optimization example](https://www.cvxgrp.org/cvx_short_course/docs/applications/notebooks/portfolio_optimization.html)

## Open questions

- P-03 AC-01/AC-02 fixture verification and the P-04 rule/API review are complete;
  see the [implementation handoff](handoff.md) and
  [acceptance tests](../../tests/unit/test_performance.py).
- Complete the P-05 worked workbook and Python/CLI example, then qualify
  workbook formulas, mapping and native Excel parity under P-06. Record the
  supported host scope at acceptance.
- Solver choice, optional dependency packaging, and optimality certificate
  checks belong to the optimization milestone review.

## Acceptance criteria

| ID | Evidence required for milestone 1 |
|---|---|
| AC-01 | Valid out-of-order rows normalize and align against the declared window. Missing months at either boundary or inside it, duplicates, extra months, and blanks block full-window metrics with specific evidence. |
| AC-02 | Hand-derived cases reproduce active and linked returns, annualized outputs at their sample thresholds, and zero tracking error. Percent and fractional representations agree within documented numeric bounds. |
| AC-03 | A tampered cumulative strategy or benchmark cell fails at the expected row. Later reference values stay identical to the untampered calculation. Exact tolerance boundaries, invalid types, and non-finite values are covered. |
| AC-04 | The worked Excel workbook exposes assumptions, formulas, and an independently supplied audit case. The add-in detects the seeded error, navigates to its source, and passes after the user corrects and reruns the case. Retain actual host observations. |
| AC-05 | Excel and CLI produce equivalent normalized findings and evidence over the same audit fixture and effective policy. Exports identify the checked scope, methodology, strategy and benchmark IDs, source snapshot, and window. |

## Testing requirements

Use synthetic fixtures with hand-derived values and a reference Excel workbook.
Cover date-system handling, leap February, missing benchmark observations,
permuted rows, short history, 12-month and 13-month annualization, return units,
precision boundaries, and capped diagnostics. Verify policy round-trip, Excel
correction and export, and CLI equivalence. Keep verification outcomes and
observed host coverage in the [handoff](handoff.md).

## Dependencies on other specifications

- [0002](../0002/spec.md) owns financial invariants. Reuse its existing NAV,
  simple-return, weights and turnover checks when their contracts fit. Amend it
  before promoting new public financial rules.
- [0003](../0003/spec.md), [0004](../0004/spec.md), and [0008](../0008/spec.md)
  own tolerance, row identity and financial units.
- [0005](../0005/spec.md), [0006](../0006/spec.md), and [0007](../0007/spec.md)
  govern diagnostics, the rule catalog, and policy/CLI compatibility.
- [0011](../0011/spec.md) and [0016](../0016/spec.md) govern the template and
  the Excel workflow. Use E-06 evidence to qualify the native workflow.
- [0015](../0015/spec.md) governs release capability metadata. Refresh the
  generated [0019](../0019/spec.md) guide if the shipped catalog changes.

## Explicit deferred work

Intramonth valuations and flows, daily or irregular calendars, multi-currency
translation, point-in-time market-data acquisition, full backtest execution,
portfolio attribution, and richer risk measures remain deferred. Solver-backed
workbook execution, derivatives, leverage and discrete trade sizing require
separate contracts. External data acquisition and trade execution are outside
this specification.
