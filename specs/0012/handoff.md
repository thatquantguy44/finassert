# 0012 — Handoff

## Current state

Cash continuity, weekly coverage and minimum available-cash buffer are implemented.
PR #21 slices 4–5 are verified, including facility continuity/maturity and
public exports/catalog. All six slices and full repository/distribution checks pass. External PR review and downstream work remain pending.
Consumer integration remains proposed.

## Entries

### 2026-11-13 — Cash/funding pack acceptance and immutable handoff

Full suite: 3,624 passed; lint, formatting, types, strict docs, browser/Excel
builds and isolated installed-package checks passed. Clean source f0b9667 bundle
records exact Python/artifact/capability/pack identity; [receipt](../0015/artifacts/README.md).
U-01–07 and U-10 are delivered upstream; PR #21 remains draft for review.
U-08 paired forecast accuracy and U-09 debt/issuance are next. No consumer,
release/tag or publishing action was taken.

### 2026-11-13 — Slice 6 versioned cash/funding pack

Added treasury.cash-funding v1 manifest, two immutable templates and generated
cash/facility policies. Explicit Decimal preparation preserves original IDs/flows
and refuses missing or invalid components. Required-check inventory, assumptions
and applicability appear in CLI/MCP discovery and release capabilities. Cash
row_key catalog support and expected-scope key adaptation preserve mapping parity.
MCP adds canonical bounded diagnostics/tolerances; Python/CLI/JSON/HTML/XLSX and
real MCP stdio checks pass. 139 affected interface/release tests and 76 focused
pack/template tests passed. Full branch/distribution checks are next; draft PR #21.

### 2026-11-13 — Slice 5b facility continuity and maturity

Promoted public immutable facility_capacity factory, exports and strict catalog
parameters. Adjacent balances name current/prior rows and respect isolated facility
and currency scopes. Invalid/intraperiod maturity errors; matured draws/closing
principal fail, final-end maturity does not infer a later period. Bounded headroom
remains unclamped. Added generated schedules/localized breaks. 236 focused tests,
Ruff and mypy passed; draft PR #21. Next is the versioned policy pack.

### 2026-11-13 — Slice 5a facility principal and headroom

Added internal facility principal identity and effective-capacity checks, strict
nonnegative components and complete-schedule prerequisites. Headroom remains
negative on an overdraw. All-row balances and violations use bounded samples.
73 focused facility/buffer tests, Ruff and mypy passed. No public factory/catalog
promotion yet: continuity, maturity and full acceptance are the next commit.

### 2026-11-13 — Slice 4 available-cash buffer

Shipped immutable public factory/catalog/policy support, explicit currency-isolated
weekly coverage, required close/restricted/minimum columns and zero default
materiality. Invalid numeric values fail; missing/duplicate schedules error.
All actual shortfalls, even tolerated ones, retain complete totals and bounded
samples. Local Decimal context preserves a 0.01 shortfall against 1e40 balances.
162 focused tests, Ruff and mypy passed. Draft PR #21; no downstream change.

### 2026-11-13 — Preserve current main and normalize layout

Moved the existing main spec into the numbered workspace; retained its requirements and existing plan/task ledger. No downstream integration or deployment was performed. Consult [tasks.md](tasks.md) before new work.
