# 0020 — Performance and backtest integrity handoff

## Current state

- **Status** Proposed pending P-05 workbook/example delivery and P-06 Excel parity.
- **Completed** P-03 AC-01/AC-02 acceptance and P-04 runtime implementation.
- **Branch** `spec/0020-quant-model-assurance`, based on `origin/main` at `8f14c66`.
- **Design** The user confirmed one composite rule and complete policy parameter
  traceability. Specifications 0005 and 0007 now define the additive artifact
  contract; the [decisions](decisions.md) record the implemented API.
- **Next spec task** P-05: author the worked Excel workbook and Python/CLI
  example against the [independent fixtures](artifacts/fixtures/expected.json).
  P-06 will qualify native Excel parity. The
  [master handoff](../../docs/handoff.md#next-up) owns project order.

## Entries

### 2026-11-21 — Verify P-03 and implement P-04

- **Done** Verified P-03 coverage, row-order normalization, units, hand-derived
  calculations, annualization, tracking error and bounded issue counts against
  the independent fixtures. Implemented `monthly_performance_audit` as one
  composite rule with required comparison declarations, reason-coded bounded
  diagnostics, and a fixture-matched starter policy.
- **Traceability** Policy artifacts now include explicitly configured
  `parameters` and complete normalized `effective_parameters`, including
  defaults and exact Decimal text. JSON, HTML and XLSX views expose the policy
  values; policy version-1 input and digest semantics remain unchanged. The
  XLSX `Policy` sheet follows specification 0013. Tracking issue:
  [#31](https://github.com/thatquantguy44/finassert/issues/31).
- **Guide** Updated the user guide walkthrough and generated appendix. The
  rebuilt 51-page PDF and identity sidecar list 21 rules and 11 templates; all
  pages were rendered and visually reviewed.
- **Verified** Full suite: 3,785 passed, 111 skipped because the bundled Excel
  browser job was unavailable. Ruff, formatting, mypy (67 source files), strict
  MkDocs, guide asset/API tests and focused P-03/P-04 assertions pass.
- **Boundary** AC-04 and the Excel portion of AC-05 remain open for P-05/P-06;
  no native Excel acceptance, commit, push or CI run is claimed.
- **Next** Build the worked workbook and Python/CLI replay in P-05. The project
  priority remains E-06 in the master handoff.

### 2026-11-20 — Record composite audit and policy traceability decisions

- **Decisions** Keep coverage, input validation, strategy tie-out, and benchmark
  tie-out in one composite check. Export the exact configured values and all
  effective parameter values used after defaults and schema normalization.
- **Contract** Amended 0005 and 0007 to include explicit `parameters` and complete
  `effective_parameters` under additive artifact schema 1. Policy digest and
  version-1 input semantics remain unchanged. Credentials are not policy fields.
- **Verified** Strict MkDocs build, 136 local/repository links across 19 changed
  Markdown files, and `git diff --check` pass. Runtime acceptance checks were not
  run.
- **Next** Verify P-03 against AC-01/AC-02, then implement P-04. E-06 remains the
  overall project priority.

### 2026-11-20 — Implement P-03 monthly reference prototype

- **Done** Added a dependency-free reference calculator with inclusive month-end
  coverage, row-order normalization, explicit fraction/percent conversion,
  reason-coded preflight issues, bounded examples with complete counts, linked
  monthly values, geometric annualization, and annualized sample tracking error.
- **API** Added immutable reference/period/summary/issue records and exported
  `monthly_performance_reference` from the package root. Added the usage and
  failure contract to the canonical spec.
- **Verified** Full Ruff lint, Ruff formatting, and mypy checks pass. Runtime
  acceptance checks were not run, so AC-01/AC-02 verification remains pending.
- **Next** Run the fixture-based runtime checks before P-04. The overall project
  priority remains E-06.

### 2026-11-20 — Complete P-02 policy, precision, and fixture design

- **Done** Reviewed policy/catalog, source row identity, tolerance, and artifact
  contracts. Recorded the proposed calculator and composite audit shape, 50-digit
  Decimal behavior, financial and parity tolerances, and additive policy/report
  parameter export requirement.
- **Fixtures** Added an out-of-order 2024 monthly audit with a seeded June error,
  independent expected series, a hand-derived three-month case, a zero-tracking-
  error case, and coverage/numeric boundary mutations.
- **Verified** The 12-month expected cumulative series was independently
  recomputed from periodic inputs with Decimal arithmetic; all 12 strategy and
  benchmark rows match the manifest. The seeded June difference is exactly
  `0.01`; the three-month tracking error matches `sqrt(247/2500)` and the
  two-month zero-error case has identical active returns. The 13-month
  annualized values match the 50-digit expected values within `1e-12`, and the
  percent fixture normalizes exactly to the fraction fixture. All fixture JSON
  parses. The strict docs build and 58 local links/anchors pass; `git diff --check`
  is clean.
- **Next** P-03 prototype the reference API and implement preflight/calculations;
  E-06 remains the project-wide first priority.

### 2026-11-20 — Scope the quant modeling workflow

- **Done** Defined the monthly performance workbook, reference calculation and
  audit paths, worked example, and acceptance criteria. Sequenced point-in-time
  backtest evidence and minimum-variance validation plus reference implementation.
- **Decisions** Use one monthly strategy and benchmark pair and the existing
  one-source Excel workflow for the first milestone. Carry the declared window,
  methodology, units, and original rows into the report.
- **Verified** Seven required files, 46 local links and anchors, exact decimal
  arithmetic for the worked return example, strict documentation build, and
  whitespace checks.
- **Next** Resolve P-02 and retain independent expected values before runtime work.
