# 0016 — Excel add-in validation workflow: contracts

[spec.md](spec.md) is normative. This file indexes review and compatibility; it
does not define another version of the workflow.

- [Source binding](spec.md#r-01-explicit-source-binding)
- [Freshness and lifecycle](spec.md#r-02-freshness-and-run-lifecycle)
- [Diagnostic navigation](spec.md#r-03-diagnostic-navigation)
- [Date interpretation](spec.md#r-04-explicit-date-interpretation)
- [Evidence and output](spec.md#r-05-evidence-and-safe-output)
- [Real-host acceptance](spec.md#r-06-real-host-acceptance)
- [Home-ribbon entry points](spec.md#r-07-home-ribbon-entry-points)
- [Public API](spec.md#public-api-design), [data contracts](spec.md#data-contracts)
- [Failure semantics](spec.md#failure-semantics), [acceptance](spec.md#acceptance-criteria)

## Compatibility changes

- E-02 requires an explicit source instead of silently using a whole
  worksheet after a single-cell selection. Table totals will be excluded.
- E-02 makes live date interpretation explicit. The public read_range default and
  workbook-file APIs retain their existing behavior.
- E-03: results become historical when their dependencies change. Session controls
  configure event/on-demand monitoring and verified/snapshot-only capture. Current
  export requires fresh comparisons in both monitoring modes; snapshot-only never
  becomes Current. Core outcomes and existing artifact schemas remain unchanged.
- E-04: a private live-only navigation response resolves retained native row labels
  before JSON serialization. Exact counts/caps and canonical diagnostic samples
  stay unchanged. Duplicate/colliding keys require a unique key and rerun;
  missing groups/periods have no target. Selection uses source IDs, numeric bounds
  and the configured current-result preflight. No public/artifact schema changes.
- E-05: optional input.excel context is additive under artifact schema 1. Existing
  consumers may ignore it; artifacts without live context stay unchanged.
- E-05: output collisions use a new unique sheet by default; replacement identifies an
  owned destination explicitly and can never clear a bound source.
- E-06 adds additive TaskPane VersionOverrides 1.0 commands on Excel Home. Both
  commands only show the existing task pane; the Settings route renders a focused
  in-pane settings view and preserves the in-memory session when it returns to
  validation. The base manifest remains a fallback, and no workbook, policy,
  artifact, public API or financial-outcome contract changes.

E-02 implements the first two migrations. E-03 adds generation-safe capture,
calculation/event/policy invalidation and preflight for the existing sheet/JSON/HTML
actions. Its digest encoding and bounds are canonical in
[R-02](spec.md#r-02-freshness-and-run-lifecycle) and
[capture encoding](spec.md#canonical-capture-encoding-v1). Formula identity is
private and separate from the evaluated snapshot digest. Parent 0011's shared
application clears obsolete file results on policy/input changes. E-04 now adds
the bounded diagnostic panel and guarded selection. E-05 now validates/stamps
provenance and uses saved ID-based ownership, explicit completed-results
replacement, unique names, policy loading choices and incomplete-write recovery.
HTML/sheet live views consume the canonical retained collections without extra
hidden caps. File/CLI artifact shapes and rendering stay unchanged. See R-05 and
data contracts for the normative ownership/provenance fields and limits.

Range mode additionally requires stable ExcelApi 1.13 to detect merged headers;
table mode retains the manifest's 1.7 floor. Hosts without 1.13 get an explicit
table/update alternative. This is a mode-specific capability requirement, not a
preview dependency or a change to Python parsing, outcomes or artifact schemas.

## Stable Office API evidence

Reviewed 2026-11-13. Event notifications and lifecycle are documented in
[Microsoft's event guide](https://learn.microsoft.com/en-us/office/dev/add-ins/excel/excel-add-ins-events).
Because handlers are session-scoped, rebind/disposal and a capture preflight are
required by this spec's own integrity contract.

Microsoft distinguishes a table's
[header, data body and total row](https://learn.microsoft.com/en-us/javascript/api/excel/excel.table?view=excel-js-1.9).
The implementation must use those boundaries rather than assume getRange excludes
totals. [Calculation state](https://learn.microsoft.com/en-us/javascript/api/excel/excel.application?view=excel-js-1.9#excel-excel-application-calculationstate-member)
is documented in ExcelApi 1.9. The complete method/event matrix and actual Mac
behavior are separated in the [API matrix](api-matrix.md) and
[baseline evidence](artifacts/README.md). The stable method audit is complete;
the successful [Mac baseline](artifacts/e01-native-baseline.json) now records
actual capability/calculation answers and synthetic timings. A working native
sideload launch is documented in [the evidence notes](artifacts/README.md).

E-01 corrects the existing prototype's declared minimum to ExcelApi 1.7, matching
getRangeByIndexes in its sheet writer. Generated manifests now enforce that floor;
hosts below it can no longer load the prototype. The future 1.9 workflow remains
proposed. No financial, date-reader, artifact or row-identity contract changes here.
The manifest deployment version initially used 1.0.0.0 because
Microsoft's validator rejected the package-derived 0.1.0.0 as below its minimum.
The add-in ID and actual package/report version are unchanged. The later native
baseline establishes a working CLI sideload route; the disabled menu's cause
remains unknown. E-03 live capture enforces 1.9 at runtime.

No stable workbook date-system getter is assumed. E-01 must substantiate any
automatic path; user selection is the defined baseline. A search hit or a preview
type declaration cannot establish a supported-host contract.

Deployment 1.0.0.1 adds distinct ShowTaskpane Titles under R-07. The original
add-in ID, permissions, local origin and financial/runtime contracts stay unchanged.
