# 0020 — P-02 design decisions

P-02 reviews the existing policy, rule, row-identity, tolerance, and report
contracts before implementation. These decisions guide the proposed first
milestone; public behavior remains **Proposed** until implemented and accepted.

## User-confirmed decisions — 2026-11-20

- Keep coverage, input validation, strategy tie-out, and benchmark tie-out in
  one composite audit rule and one policy entry.
- Export every explicitly configured rule parameter and the complete effective
  parameter set used for evaluation, including resolved defaults. Preserve
  exact Decimal values as text so the report identifies the policy that was
  actually configured and tested.

## Policy and audit shape

- Keep human-readable `assumptions` for explanation. Do not encode computational
  settings as prose.
- Use explicit rule parameters for the inclusive month-end window, column
  mappings, periodic and reported return units, absolute tolerance, strategy and
  benchmark identifiers, base currency, valuation convention, and each series'
  fee treatment. Require these fields; do not infer them from values or Excel
  formatting.
- Use one composite `monthly_performance_audit` rule for the first
  workflow. It shares one declared comparison across date/return preflight and
  reported cumulative tie-outs. Its bounded diagnostics distinguish coverage,
  invalid-input, strategy-tie-out, and benchmark-tie-out findings. This avoids
  repeating shared comparison settings across separate policy rules. The
  reference calculator remains callable without reported cumulative columns.
- The existing policy digest continues to identify the canonical configured
  policy. Export both `parameters` (values explicitly present in the policy)
  and `effective_parameters` (the complete typed values used after applying
  registered defaults and schema normalization). Preserve exact Decimal values
  as text. Include these fields when a configured rule passes, fails, skips, or
  errors. This is additive under artifact schema 1; existing version-1 policy
  documents and digest semantics remain valid. Do not add a generic opaque
  metadata field. Policy parameters are report-visible; credentials do not
  belong in policy documents.
- Preserve the adapter's original row label through chronological ordering. The
  fixtures use an explicit `source_row_id` as `row_key`; require an explicit key
  when native row labels are not unique or stable. Diagnostics retain both the
  period key and original source identity. Reordering the in-memory series must
  never reorder or rewrite source rows.

The Python calculator is `monthly_performance_reference(data, *,
period_end, strategy_return, benchmark_return, window_start, window_end,
return_unit, row_key=None)`. It returns per-month active and cumulative values
plus the summary measures. The registered factory is
`monthly_performance_audit(...)`, with the same input mappings and window,
reported cumulative mappings, the required comparison declarations, absolute
return tolerance, severity, and diagnostic cap. P-04 finalized the factory
name, `performance.monthly_performance_audit` rule ID, `ValidationResult` type,
and exact parameter spellings.

Audit parameters are:

| Parameter | Contract |
|---|---|
| `period_end`, `strategy_return`, `benchmark_return` | Required source-column mappings. |
| `reported_strategy_cumulative`, `reported_benchmark_cumulative` | Required source-column mappings for audit; omitted from the reference-only calculator. |
| `window_start`, `window_end` | Required ISO calendar month-end dates, inclusive. |
| `periodic_return_unit`, `reported_return_unit` | Required `fraction` or `percent`, independently declared. |
| `strategy_id`, `benchmark_id`, `base_currency` | Required comparison identifiers; currency uses the existing 0008 syntax contract. |
| `valuation_convention`, `strategy_fee_treatment`, `benchmark_fee_treatment` | Required nonempty declarations, retained verbatim as analyst-supplied methodology metadata. |
| `tolerance` | Required absolute tolerance in decimal-return fractions; relative tolerance is zero. |
| `row_key` | Optional source column when the adapter's native row label is not stable and unique. |
| `severity`, `max_violations` | Existing shared failure and diagnostic-cap settings. |

P-02 proposed the catalog reference `monthly_performance_audit` and rule ID
`performance.monthly_performance_audit`; P-04 finalized both.

## Implementation review — 2026-11-21

P-03 acceptance verified the calculator against AC-01/AC-02. P-04 freezes the
factory name and rule ID above and returns the existing `ValidationResult`.
The `monthly-performance-audit` starter policy uses the synthetic out-of-order
2024 fixture and preserves the seeded June failure for correction demonstrations.
Configured and effective parameters are exported through artifact schema 1 and
the JSON, HTML and XLSX report views. The user guide now includes the factory,
starter policy and fixture workflow. AC-04 and the Excel portion of AC-05 remain
open for P-05/P-06; see the [P-04 handoff](handoff.md).

## Numeric contract proposal

- Convert supported finite numeric inputs through their shortest decimal text
  and normalize percent inputs by exact decimal division by 100. Keep working
  returns as decimal fractions.
- Use a local Decimal context with 50 significant digits and `ROUND_HALF_EVEN`
  for compounded and annualized outputs, square roots, and tracking error. Do
  not round values to display precision before checks. Serialize calculated
  Decimal values as text; workbook number formats affect display only.
- Use the existing inclusive `Tolerance` equation with a required absolute
  allowance in decimal-return fractions and relative tolerance set to zero.
  For example, `0.0001` is one basis point. Keep this financial allowance
  separate from the proposed Excel/Python parity bound of `1e-12` in return
  fractions.
- Do not compare rounded percentages. For the exact boundary, a difference equal
  to the configured allowance passes; the next larger Decimal value fails.

## Independent fixtures

The fixture set under [artifacts/fixtures](artifacts/fixtures/) is synthetic.
The complete 2024 source rows are deliberately out of order, use leap-February
month end, and carry one seeded June strategy cumulative error. Expected series
are compounded only from periodic return inputs; the seeded report is never used
as a calculation input. A three-month hand case provides independently derived
active returns, cumulative values, and tracking error. Separate percent and
fraction files establish unit equivalence; a 13-month file exercises the
non-integer annualization exponent. Coverage and numeric boundary mutations are
listed separately so implementation checks can assert a specific reason and
source identity without changing the canonical fixture.

| Case | Independent expected value |
|---|---:|
| Three-month strategy cumulative | `0.0098` |
| Three-month benchmark cumulative | `0.0302` |
| Three-month cumulative difference | `-0.0204` |
| Three-month annualized geometric returns | Unavailable, fewer than 12 months |
| Three-month annualized tracking error | `sqrt(247 / 2500)` = `0.31432467291003421960436773978256…` |
| Twelve-month 1% strategy cumulative and annualized return | `0.126825030131969720661201` |
| Twelve-month 0.5% benchmark cumulative and annualized return | `0.061677811864499568789707617431640625` |
| Twelve-month tracking error | `0` |
| Thirteen-month steady 1% strategy annualized geometric return | `0.126825030131969720661201` using exponent `12/13` |
| Thirteen-month steady 0.5% benchmark annualized geometric return | `0.061677811864499568789707617431640625` using exponent `12/13` |
| Seeded June strategy cumulative finding | Expected `0.061520150601`; observed `0.071520150601`; difference `0.01`; one-basis-point allowance fails |

The hand case uses strategy returns `0.10, -0.10, 0.02` and benchmark returns
`0.02, 0, 0.01`. Its active returns are `0.08, -0.10, 0.01`. The sample
variance of active return is `247/30000`; multiplying the sample standard
deviation by `sqrt(12)` gives `sqrt(247/2500)`. Annualized geometric returns
are unavailable for this three-month window.

## Implementation gate

P-03 may implement the reference calculator and shared preflight against these
fixtures. The user-confirmed composite-rule and parameter-export decisions are
now recorded in the amended contracts for specifications 0005 and 0007. P-04
implements those contracts alongside the registered audit rule. The P-02
precision and fixture values are the independent benchmark for that prototype.
