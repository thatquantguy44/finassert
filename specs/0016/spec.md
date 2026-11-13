# 0016 — Excel add-in validation workflow

**Status:** Proposed; scoped, implementation not started.
**Updated:** 2026-11-13
**Owner:** finassert. Mac desktop is the first real-host acceptance target.

## Problem statement

The initial task pane reads selected cells into a snapshot and runs the ordinary
engine. Users can edit the workbook or policy while the previous result remains
available. Row findings do not navigate to their source, and the live reader does
not pass an explicit workbook date system. These gaps prevent a reliable daily
validation workflow even when the financial rules are correct.

Inspected baseline: ab24d76, the six-slice delivery in now-merged PR #21. In
[excel.js](../../web/excel.js), readSelection captures values, formats and types;
writeToSheet uses the stored result. In [app.js](../../web/app.js), refresh only
updates run-button availability. The live payload omits date1904, although
[read_range](../../src/finassert/excel.py) supports it. Existing CI uses an Office
stand-in; no real Mac acceptance is claimed by this specification.

## Motivation and use cases

An analyst binds a holdings table, runs approved checks, selects a reported
negative market value, corrects it in Excel, sees the old result become stale,
reruns and exports evidence of the new run. The selected source and interpretation
remain visible throughout. Existing policy import, templates and save/load work
with the same engine and policy digest as Python and the CLI.

## Goals

- Bind one explicit table or rectangular range in the current workbook session.
- Run against a newly read, stable snapshot and distinguish freshness from outcome.
- Navigate bounded findings to valid source locations without editing input cells.
- Resolve the 1900/1904 date system explicitly and retain source/run provenance.
- Verify the complete workflow in real Excel on Mac and in automated regressions.

## Non-goals

New financial rules, automatic fixes, cell highlighting/comments, automatic
validation on every edit, custom worksheet functions, ribbon/AppSource work,
central deployment, hosted services, account systems, LLM policy generation,
multi-table execution and cross-workbook orchestration are outside this slice.
Saved source configurations across sessions and a Web Worker for interruptible
Python execution are later work. Windows/web compatibility remains a regression
goal; platform support is declared only with real-host evidence.

## Proposed architecture

Keep the Office adapter in web/excel.js and the shared application in web/app.js.
Extract small private modules if lifecycle tests need them. Office calls handle
binding, reading, change notifications and selection. Python handles parsing,
policy validation, evaluation and reports through the existing web bridge and
ordinary check path. JavaScript never implements a financial invariant.

A session owns one source binding, one active operation and an increasing
generation number. Changes invalidate the relevant generation; late completions
cannot replace newer data or results. Each completed result retains its own
source snapshot, effective policy digest and date interpretation. Dispose event
handlers and obsolete navigation maps on rebind or pane shutdown.

### R-01: Explicit source binding

Offer a workbook table picker and a Use selected range action. Show worksheet,
table name where applicable, resolved address, header row, data-row count and
column count before running. Binding is session-only; a file name is a display
label, never the identity or a file-access permission.

- Table mode uses the actual header and data body, excluding its totals row.
  Resolve the current table by host identity on every run. Resize or sort makes
  existing results stale; header changes require column-mapping review.
- Range mode binds one fixed rectangle, including a single header row. It never
  expands silently to the used range. A single-cell selection must lead to an
  explicit table choice or a request for a larger range.
- Structural edits that make a fixed range's meaning uncertain invalidate its
  binding and require reselection. Deleted/recreated sheets or tables cannot be
  rebound merely because their display names match.
- Hidden and filtered data rows are included; state this in the source summary.
  Visible-only validation is deferred. Spec 0013's file-reader hidden options
  remain a separate API; do not imply they are implemented in the live adapter.
- Reject disjoint selections, merged headers, duplicate/blank headers and empty
  data regions before evaluation. Explicit range bounds own totals exclusion.
- Preserve the existing 5,000,000-cell ceiling, checking dimensions before
  fetching cells. Read in bounded requests, reducing rows per request for wide
  tables. Payload-limit/read errors must never publish a partial result.

### R-02: Freshness and run lifecycle

Freshness is interface state, separate from passed/failed/error/skipped. Use
Unbound, Ready, Reading, Checking, Current, Stale and Blocked as explanatory UI
states; do not add core Outcome members. Current means the result matched its
bound input at its last successful verification time, not a workbook lock or a
claim that remote edits can never occur afterward.

Every Run rereads the bound source. Register stable Office events for cell edits
and completed calculations; invalidate on relevant value, formula, format,
structure, source, effective-policy or date-system changes. Do not require Run
merely because the selection moved or an unrelated worksheet cell was edited.
Worksheet-wide calculation invalidation may be conservative. Resolve supported
events/requirement sets during E-01; no preview dependency is allowed.

Before accepting a run, compare captures bracketing evaluation, including source
identity/dimensions, values/types/formats, date interpretation and generation.
Require settled calculation; detect changes during chunked reads and evaluation.
On mismatch discard the candidate and request a rerun; no unbounded retry loop.
This is a stability check, not a transactional or atomic Excel snapshot.

The initial supported-host baseline is ExcelApi 1.9 for calculation-state reads,
subject to E-01's full API audit. A missing mandatory capability blocks the live
workflow with an actionable message. In manual calculation mode, show that state
and require the user to calculate in Excel before validating formula results;
never change application calculation settings or invoke recalculation silently.

Disable overlapping run/read/export actions. A failed load, invalid policy,
interrupted operation or superseded job cannot restore the last passing banner.
Old results may remain visible as historical/stale, with their timestamp and
reason; current-result export and source navigation remain disabled until rerun.
Read cancellation, if offered, takes effect between host requests; do not claim
that synchronous Python evaluation is interruptible.

Events are notifications, not the sole integrity check. Before navigation or
current-result export, revalidate source identity, contents, policy and generation
against the result. An unavailable source or mismatch makes it stale/blocked.
Ignore changes caused solely by owned-output writes outside the source; do not
globally disable events and hide unrelated edits.

### R-03: Diagnostic navigation

Render canonical bounded diagnostic collections with complete count, example cap
and truncation. A retained row example can select its physical source row; a cell
is selected only when the diagnostic's column is unambiguous. Group findings keep
their group identity and retained row examples. Missing groups/periods with no
observed row display No source row, never a fabricated cell.

Build navigation from the captured source and effective column/row-key mapping.
Never treat a business row key as an Excel row number. If a key resolves to
multiple rows or loses type distinctions during serialization, display ambiguity
and require an explicit choice or rerun. Do not guess. No uncapped diagnostic
population is reconstructed. Keep navigation metadata in memory, bounded by the
selected input and diagnostic caps; no full source records enter an artifact.

Validate targets against the bound sheet and rectangle. Quote/resolve host sheet
names safely, including spaces and apostrophes; never construct executable
formulas or external links from diagnostic text. Navigation changes selection
and active sheet only. Sorting, resizing or deleting the source invalidates old
targets. Keyboard users must have the same navigation action and status feedback.

### R-04: Explicit date interpretation

The live adapter passes date1904 explicitly and records whether it came from a
verified stable host API or a user choice. Baseline fallback is a required
1900/1904 selector with no preselected assumption. Automatic detection is allowed
only after its stable API and supported-host behavior are demonstrated in E-01;
no full-workbook download or preview API is required by this slice.

Changing the setting invalidates the snapshot/result. Preserve number formats,
percent fractions, Decimal/string handling, error markers and physical row
labels under the existing read_range contract. Never write dates or workbook
date-system settings. The public read_range default remains compatible; this
requirement applies to payloads produced by the add-in.

### R-05: Evidence and safe output

Only a verified Current result can write a current-results sheet or download its
JSON/HTML report. Recheck immediately before the action; a failure produces a
stale/blocked message. An exported report always identifies the captured snapshot
and time, never promises continuing freshness after export. Later edits make
previous in-workbook evidence historical; do not rewrite it silently.

Retain policy digest, finassert version, run timestamp and source address. Add the
versioned source context described below without changing financial results.
Policy YAML export/save remains available when the current policy is valid; it
does not imply a current validation result. Existing policy save/load is retained.

Protect source cells and unrelated sheets, including collisions with finassert
output names. Default to a new uniquely named results sheet on collision. A
Replace results action must identify the owned destination explicitly and never
clear a bound source sheet. Apply the same source-overlap guard to policy-sheet
writes. Do not adopt arbitrary existing sheets as owned merely by their name.
Stage output data before writes; a failed host write reports an export error and
never marks an incomplete sheet as completed evidence. Excel writes are not
claimed atomic. Preserve literal text and formula-injection protections.

### R-06: Real-host acceptance

Mac desktop with a recorded Excel version is mandatory. E-01 establishes an
early install/read/run baseline; E-06 repeats the completed workflow using
synthetic inputs and retains the evidence in acceptance.md and artifacts/.
Existing stand-in/CDN/bundled-runtime CI remains mandatory and cannot substitute
for the Mac run. No production support claim follows from a passing stub test.

## Public API design

No new public financial factory, policy version, CLI command or stable Python
evaluation API is proposed. Private app/Office bridge methods may accept a source
descriptor and result generation. An additive optional input.excel artifact field
is proposed under artifact schema 1; file/CLI artifacts that do not supply it stay
unchanged. Final typed plumbing belongs in E-03/E-05, with contract regressions.

## Data contracts

The proposed input.excel object has source schema_version 1:

| Field | Meaning |
| --- | --- |
| kind | table or range |
| worksheet_name / worksheet_id | Display name and source identity at capture |
| table_name / table_id | Present for a table; resolved again at use |
| address / header_row | Exact captured rectangle and 1-based worksheet header |
| data_row_count / column_count | Parsed data-row count and source width, excluding table totals |
| hidden_rows | include_all; filters do not reduce the validated population |
| date_system / date_system_source | String enum 1900 or 1904; host or user |
| captured_at / verified_at | UTC snapshot and last comparison timestamps |
| snapshot_sha256 | Digest of the versioned canonical evaluated payload |

E-03 must define one canonical digest encoding for ordered typed values, formats,
value types, resolved source geometry and date interpretation, with fixed vectors.
Include effective policy digest separately; it already belongs in the artifact.
The digest covers evaluated values, not the formula source or external workbook
dependencies. It is snapshot identity, not a signature or a completeness proof.
Ephemeral session/generation tokens and full navigation maps are not exported.

The source summary distinguishes physical body rows from parsed data rows when
the existing reader drops wholly blank rows. The capture digest retains the full
selected geometry; gaps never renumber surviving worksheet rows.

Row labels remain physical 1-based worksheet rows unless a rule explicitly uses
row_key. Canonical financial results, totals, truncation, severity and tolerance
are preserved. Input context and timestamps can differ across surfaces; identical
normalized input, policy and row labels must yield identical report results.

## Financial and numerical edge cases

Test offsets such as C7:H20; tables with totals/filters/hidden rows; blank interior
rows; reordered rows; duplicated business keys; missing entire treasury series;
negative market values; exact Decimal tolerances; numeric text and booleans;
formula errors and recalculation; both date systems and percentage formatting.
Use the existing rules' explicit units, signs, currency scope, null and skip
contracts. This interface does not infer financial meaning or repair user data.
Every selected region must contain data; do not present an empty check set or an
unreadable source as a successful validation workflow. Core vacuous-pass behavior
is unchanged; the live UI requires a valid source and at least one resolved rule.

## Failure semantics

Financial invariant failures retain the ordinary failed outcome. An engine error
retains error; skips and warning failures remain visibly distinct. Source/read,
capability, unsettled calculation and policy errors block running and do not
fabricate core results. Staleness does not turn a previous failed/error result
into a pass. Navigation/export failures do not change the recorded financial
outcome. Recovery is explicit: reselect, correct policy/date choice, calculate or
rerun as appropriate. Display messages, not raw host objects or workbook data.

## Implementation milestones

E-01 host baseline and regressions; E-02 binding/date interpretation; E-03 stable
capture and invalidation; E-04 bounded navigation; E-05 current-result export;
E-06 Mac acceptance and distribution regression. See [plan](plan.md),
[tasks](tasks.md), [roadmap](roadmap.md) and [acceptance checklist](acceptance.md).

Planning estimate: 8–12 engineering days for one engineer plus access to real
Excel, refined after E-01. This is a scope estimate, not a delivery date.

## Open questions

E-01 must record the available Mac Excel version, verify the complete stable API
matrix and determine whether reliable host date detection is available. The
defined user-choice fallback avoids making automatic detection a dependency.
Exact read widths and performance targets are measured there, then recorded
before claiming support. Further pilot platforms are optional until selected.
No unanswered product preference blocks the initial scoped implementation.

### Tradeoffs and risks

- Repeated captures and action preflights add Office I/O. Measure that overhead
  on the actual Mac build before setting responsiveness budgets; do not trade
  away source verification to satisfy an unmeasured target.
- Excel provides no transaction covering this entire workflow. Record the checked
  snapshot/time and reject detected changes; continuous, concurrent editing may
  require the user to pause edits before a stable run can complete.
- Excel numeric cells already have finite storage precision. Decimal conversion
  preserves the values received; it cannot recover digits Excel discarded.
- Host capabilities, certificate trust and deployment policy vary. E-01 records
  an actual supported baseline; new platforms and rollout routes need evidence.

## Acceptance criteria

| ID | Observable completion criterion | Owner |
| --- | --- | --- |
| AC-01 | Explicit table/range binding displays correct source geometry; totals excluded, hidden/filtered rows included, invalid/empty/oversized regions rejected before evaluation | E-02 |
| AC-02 | Every Run reads again; edit/recalc/policy/date/structure changes invalidate results; unrelated selection movement does not change the binding | E-03 |
| AC-03 | Edit during read/check and overlapping operations never publish stale or partial candidates; pre-action verification catches delayed/missing events | E-03, E-05 |
| AC-04 | Retained row/cell findings navigate correctly with offsets, custom IDs and quoted sheet names; ambiguous/missing targets are explained without invented addresses | E-04 |
| AC-05 | 1900 and 1904 fixtures yield the same intended dates with recorded interpretation; unknown date system blocks the live run | E-02 |
| AC-06 | JSON/HTML/results sheet preserve canonical outcomes, Decimal evidence, complete diagnostic counts, caps and policy/source identity; source/unrelated cells remain untouched | E-04, E-05 |
| AC-07 | Real Mac negative-value → navigate → correct → stale → reread → pass → export workflow succeeds and agrees with Python/CLI on the same normalized fixture | E-06 |
| AC-08 | Unsupported capabilities, formula errors, pending/manual calculation, read-only/protected destinations and failed writes have explicit nonpassing workflow states and recovery | E-01, E-03, E-05 |
| AC-09 | Existing Python/CLI/browser/file-reader and CDN/bundled-runtime smoke tests pass; no new core dependency or post-load data transmission | E-06 |
| AC-10 | Fifty-thousand-row/five-column synthetic run retains exact planted findings, bounded diagnostics and input integrity; timings and host limits recorded | E-06 |

## Testing requirements

Add meaningful tests of binding/lifecycle/operation ordering and navigation maps,
with simulated edits, calculation, delayed events, sort/resize/delete and host
errors. Extend the Office stand-in with controllable events and real selection
tracking; merely returning supported=true is insufficient capability coverage.
Golden vectors verify capture/digest/date/row alignment. Browser tests exercise
actual pane controls and report currentness, including shared-app invalidation.
Regression-test the file/browser paths when touching shared app or bridge code.
Real-host evidence remains pending until executed; use [acceptance.md](acceptance.md).

## Dependencies on other specifications

[0011](../0011/spec.md) owns the existing task pane and interface principles;
this spec proposes its next live-workbook milestone. [0013](../0013/spec.md)
continues to own workbook-file APIs. [0004](../0004/spec.md) owns row identity,
[0005](../0005/spec.md) diagnostics/artifacts, [0007](../0007/spec.md) policy/CLI
contracts and [0003](../0003/spec.md) tolerance mathematics. [0012](../0012/spec.md)
supplies optional treasury fixtures, not new equations here. [0015](../0015/spec.md)
provides build identity; release publication is not required for local acceptance.

## Explicit deferred work

Persisted multi-source workbook configurations, automatic/debounced validation,
interruptible worker execution, visible-only input, automatic fixes/highlights,
collaborative policy approvals, ribbon commands/UDFs, AppSource/central rollout,
signed installer automation and new financial workflows each need later scope.
