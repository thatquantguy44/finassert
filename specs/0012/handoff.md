# 0012 — Handoff

## Current state

Cash continuity, weekly coverage and minimum available-cash buffer are implemented.
PR #21 slice 4 is verified; next is facility identity/capacity, then continuity/maturity.
Consumer integration remains proposed.

## Entries

### 2026-11-13 — Slice 4 available-cash buffer

Shipped immutable public factory/catalog/policy support, explicit currency-isolated
weekly coverage, required close/restricted/minimum columns and zero default
materiality. Invalid numeric values fail; missing/duplicate schedules error.
All actual shortfalls, even tolerated ones, retain complete totals and bounded
samples. Local Decimal context preserves a 0.01 shortfall against 1e40 balances.
162 focused tests, Ruff and mypy passed. Draft PR #21; no downstream change.

### 2026-11-13 — Preserve current main and normalize layout

Moved the existing main spec into the numbered workspace; retained its requirements and existing plan/task ledger. No downstream integration or deployment was performed. Consult [tasks.md](tasks.md) before new work.
