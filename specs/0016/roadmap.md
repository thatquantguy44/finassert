# 0016 — Excel add-in validation workflow: roadmap

## Current milestone

The Mac-first validate → navigate → correct → stale → rerun → export loop remains
partially proposed. E-01's native baseline and E-02's explicit source/date binding
are verified on feature/excel-source-binding-dates. E-03 adds configurable session
monitoring/stable captures, calculation guards and current-result preflight.
E-04 adds bounded diagnostic navigation with native F8 selection evidence on
feature/excel-diagnostic-navigation; canonical artifacts remain unchanged.
See [tasks.md](tasks.md) and
[native evidence](artifacts/README.md#e-02-source-and-date-evidence).

## Next milestone

Implement E-05 provenance/safe output, then E-06; retain the
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
