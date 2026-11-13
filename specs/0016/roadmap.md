# 0016 — Excel add-in validation workflow: roadmap

## Current milestone

Proposed Mac-first validate → navigate → correct → stale → rerun → export loop.
E-01 is in progress: regression reproductions, stable API audit and a read-only
host diagnostic are delivered on feature/excel-host-baseline. Native pane loading
is unresolved; complete the real Mac baseline in [tasks.md](tasks.md) before E-02.

## Next milestone

Complete E-01–E-06, retain the acceptance evidence and review the implementation.
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
