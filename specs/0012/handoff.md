# 0012 — Handoff

## Current state

Cash continuity, weekly coverage and minimum available-cash buffer are implemented.
PR #21 slices 4–5 are verified, including facility continuity/maturity and
public exports/catalog. Next: slice 6, versioned treasury pack and interface parity.
Consumer integration remains proposed.

## Entries

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
