# 0016 — Excel add-in validation workflow: roadmap

## Current milestone

The Mac-first validate → navigate → correct → stale → rerun → export loop remains
partially proposed. E-01's native baseline and E-02's explicit source/date binding
are verified on feature/excel-source-binding-dates. E-03 adds configurable session
monitoring/stable captures, calculation guards and current-result preflight.
E-04 adds bounded diagnostic navigation with native F8 selection evidence on
feature/excel-diagnostic-navigation; canonical artifacts remain unchanged.
E-05 on that same branch adds optional source provenance and verified safe output
with unique names, saved ownership and partial-write recovery.
Those implementations are merged into main. E-06 now has reproducible fixtures,
an export/CLI verifier and current Mac automated preflight. Native 50,000-row
diagnostics, stable capture, retained exports/CLI parity and integrity are now
verified. Small correction/date and failure/race cases keep the full host gate open.
See [tasks.md](tasks.md) and
[native evidence](artifacts/README.md#e-02-source-and-date-evidence).

## Next milestone

Inspect the live small source/date-format setup after the native timeout;
follow the [current pickup](acceptance.md#current-pickup-and-retained-native-files).
Complete E-06 full Mac workflow/scale/CLI acceptance; retain the
acceptance evidence and review the implementation.
Only then describe the tested Mac build as supported. Add Windows/web acceptance
when those platforms become explicit delivery targets.

## Later milestones

1. Saved workbook source/check configurations, with schema migration and reopened
   workbook identity handling.
2. Guided portfolio and treasury workflows that use existing policies and expose
   assumptions, required coverage and currency scope.
3. Interruptible worker execution and measured large-workbook responsiveness.
4. Distribution/ribbon/central rollout after workflow and host support are proven.

These are sequencing proposals, not implementation commitments in 0016.

## Deferred scope

See [explicit deferred work](spec.md#explicit-deferred-work). Project priorities
are maintained in the [project roadmap](../../docs/roadmap.md); treasury U-08/U-09
remain separate later engineering work.
