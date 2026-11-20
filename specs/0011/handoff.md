# 0011 — Handoff

## Current state

Initial policy, CLI, HTML, browser, assistant, and Excel add-in implementations exist on main.
Live-workbook [0016](../0016/spec.md) now has verified E-01/E-02 native baseline
and explicit source/date binding plus configurable E-03 freshness/capture.
E-04 now adds bounded diagnostic navigation and focused native F8 evidence.
E-05 adds verified provenance, canonical outputs, unique names, saved ownership and
write-error recovery. Full E-06 acceptance remains pending; follow the master ordering.
Spec [0019](../0019/spec.md) adds the complete PDF guide, local download API
and explicit Excel-pane link; source/examples/downloads are verified.
The optional 0018 local QuantSmith reference is implemented for the Excel pane;
it does not change workbook validation or the offline file/browser application.
The shared pane shell now uses a workbook-first visual hierarchy in Excel, while
the browser keeps its file-input flow. Spec 0016 owns the new Home-ribbon launcher:
validation opens the normal workflow and Settings opens a focused in-pane view that
returns without discarding the session. Native acceptance remains pending there.

## Entries

### 2026-11-20 — Clear pane identity and configured failure actions

Spec 0016 supplies distinct native Validation/Settings tab titles and first
headings; both are observed after the approved Excel restart. The human-facing
results sheet now uses **If check fails** with **Block validation**, **Show warning**
and **Show information**. HTML cards, diagnostic explanations and policy editor
option labels match. Outcome/result labels and policy/JSON option values remain
canonical; technical CLI XLSX output stays compatible. The saved native demo has
three passed rows with Block validation and unchanged expected source cells.
Full 3,743 runtime/111 browser tests and all smoke/quality/docs/package checks pass.
The user requested committing and pushing all current-branch changes. E-06 stays next.

### 2026-11-20 — Full Validation Report navigation

Renamed the shared report disclosure to **Open Full Validation Report** and placed
**View Full Validation Report** directly beneath the run outcome banner. The link
opens the report, moves focus to its summary and scrolls there; it respects reduced
motion and is hidden with absent results. Historical results remain inspectable
with their export guards intact. The canonical interface requirement is in spec.md.

Verified actual pointer/Enter activation, report content and scroll position at
390 × 700, including reduced motion, no extra workbook reads/writes or changed
artifact, historical export guards and hiding on result invalidation. Reviewed
the resulting pane screenshot. The ad-hoc QA harness was adjusted for the page's
CSP and ordinary end-of-document scroll clamping; production behavior did not
require a workaround. The 39 affected unit and 28 existing browser regressions,
browser/file smoke and bundled Excel smoke pass; lint/format, docs/links and diff
checks pass. No new financial/public artifact contract or offline request changed.

Updated the currently served pane atomically with unchanged manifest, runtime and
PDF assets. Native clicking is not newly claimed; E-06 remains the master pickup.
No workbook edits, staging, commit, push or CI were performed by this UI task.

### 2026-11-20 — Complete user guide and explicit PDF download

Spec [0019](../0019/spec.md) supplies the comprehensive source/PDF guide and
GET/HEAD metadata/download routes on the existing local server. The Excel pane
exposes an explicit download link, verified with exact bytes in Playwright and
live HTTPS. All 3,742 runtime and 111 browser tests pass. Downloading does not
read cells; the standalone file/browser app remains offline after its normal
startup. No financial policy/report contract or private-reader boundary changed.
Native pane-link acceptance and full E-06 are not claimed; follow the master.

### 2026-11-19 — Distinct session-settings view

The shared Excel pane now renders Settings as a focused view rather than an expanded
section of validation. It hides the validation, policy and run workflow, keeps its
session-only settings in memory when returning, and changes no policy, financial,
artifact or file/browser contract. Spec 0016 retains the generated-manifest and
browser-route evidence; native ribbon launch observation remains pending.

### 2026-11-19 — Workbook-first pane presentation and ribbon launcher

The shared static UI now separates browser file input from the live Excel source
flow, makes freshness/currentness and export actions easier to scan, and keeps
advanced controls collapsible. No policy, rule, artifact or file/browser outcome
contract changed. Spec 0016 adds the manifest's additive Home-ribbon Open
validation/Settings commands; static validation and controlled browser coverage
pass, while real Excel visibility/launch remains pending there.

### 2026-11-15 — Optional pinned QuantSmith reader

The Excel pane now offers an on-demand text reader for allowlisted documents
from a pinned local QuantSmith checkout. The local server's same-origin API
is opt-in; no private content enters the add-in build. Synthetic Git/API and
browser evidence is under [0018](../0018/handoff.md). This does not complete
0016 E-06 Mac acceptance or change the browser/file app's offline contract.

### 2026-11-15 — E-05 verified exports and owned destinations

Live exports now include scalar input.excel source provenance and use canonical
retained samples/counts in HTML and results sheets. New outputs are uniquely named;
replacement checks explicit saved worksheet IDs and never clears a bound source.
Policy save/load is independent of freshness/capture settings. Failed/cancelled
writes remain incomplete where the host permits recovery. Native saved ownership
and exact quoted-address/source integrity were checked; 3,697 runtime and 106
browser cases plus shared browser/file smoke pass. Full E-06 remains next.

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
