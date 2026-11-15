# 0011 — Handoff

## Current state

Initial policy, CLI, HTML, browser, assistant, and Excel add-in implementations exist on main.
Live-workbook [0016](../0016/spec.md) now has verified E-01/E-02 native baseline
and explicit source/date binding plus configurable E-03 freshness/capture.
E-04 now adds bounded diagnostic navigation and focused native F8 evidence.
E-05/E-06 and full Mac acceptance remain pending; follow the master ordering.

## Entries

### 2026-11-15 — E-04 live diagnostic navigation

Private live-range results now include bounded navigation metadata resolved from
native canonical samples and the effective rule mapping before JSON conversion.
The Excel pane renders text/buttons, checks currentness/source bounds and selects
only a source cell or row rectangle. File/browser outputs, policy and artifacts
remain compatible. Identity/browser/native evidence is recorded in
[0016 artifacts](../0016/artifacts/README.md#e-04-diagnostic-navigation).
Follow the master pickup for E-05; full Mac acceptance remains E-06.

### 2026-11-14 — E-03 shared application lifecycle

Separate candidate evaluation from publication for live runs, clear stale file
results on input/policy edits, and keep live historical banners/export controls
separate from core outcomes. Live exports use capture preflight and invalid live
loads cannot fall through the file-export path. Session-only monitoring/capture
controls and native/browser verification belong to [0016](../0016/artifacts/README.md).
Python, financial/policy and artifact contracts stay compatible; full provenance,
navigation/output ownership and Mac acceptance remain pending there.

### 2026-11-13 — E-02 live source/date compatibility migration

Implemented the explicit table/fixed-range and required 1900/1904 choices under
0016. Run rereads host IDs/bounds; source/date changes clear previous snapshots.
Native Mac and browser evidence is retained in [0016 artifacts](../0016/artifacts/README.md).
Python/file/policy/financial contracts stay compatible; full freshness, navigation
and safe evidence output remain proposed. See [compatibility notes](contracts.md).

### 2026-11-13 — Next live-workbook milestone scoped as 0016

Prepared the proposed source binding/freshness/navigation/date/export workflow
and real Mac acceptance gate in a separate numbered workspace. The current
prototype and existing financial/interface contracts remain unchanged. Project
priority now follows [0016 E-01](../0016/tasks.md); no host pilot was executed.

### 2026-11-13 — Preserve current main and normalize layout

Moved the existing main spec into the numbered workspace; retained its requirements and existing plan/task ledger. No downstream integration or deployment was performed. Consult [tasks.md](tasks.md) before new work.
