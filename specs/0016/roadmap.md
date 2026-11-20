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
verified. The small 1900 correction/Stale/reread/pass/export/CLI loop now also
passes. Native 1904 correction/export/CLI parity also passed on 2026-11-20.
Table/hidden/failure/race/keyboard cases keep the full host gate open.
The Home-ribbon validation/settings launcher is schema-validated; native visibility
and both launch routes were observed on 2026-11-20.
See [tasks.md](tasks.md) and
[native evidence](artifacts/README.md#e-02-source-and-date-evidence).

## Next milestone

Complete table/hidden/failure/race/keyboard cases after the verified 1900/1904
small workflows; follow the
[immediate pickup](acceptance.md#ac-07-immediate-pickup).
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
4. Custom ribbon, distribution and central rollout after workflow and host support are proven.

These are sequencing proposals, not implementation commitments in 0016.

## Deferred scope

See [explicit deferred work](spec.md#explicit-deferred-work). Project priorities
are maintained in the [project roadmap](../../docs/roadmap.md); treasury U-08/U-09
remain separate later engineering work.

The named Validation/Settings host panes and first headings are now verified
on the recorded Mac build. Human failure-action wording is verified in the saved
native demo, with canonical severity/outcomes unchanged. Full E-06 remains the
next priority under the master handoff; this UI delivery does not close that gate.
