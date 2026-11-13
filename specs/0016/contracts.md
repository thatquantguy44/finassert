# 0016 — Excel add-in validation workflow: contracts

[spec.md](spec.md) is normative. This file indexes review and compatibility; it
does not define another version of the workflow.

- [Source binding](spec.md#r-01-explicit-source-binding)
- [Freshness and lifecycle](spec.md#r-02-freshness-and-run-lifecycle)
- [Diagnostic navigation](spec.md#r-03-diagnostic-navigation)
- [Date interpretation](spec.md#r-04-explicit-date-interpretation)
- [Evidence and output](spec.md#r-05-evidence-and-safe-output)
- [Real-host acceptance](spec.md#r-06-real-host-acceptance)
- [Public API](spec.md#public-api-design), [data contracts](spec.md#data-contracts)
- [Failure semantics](spec.md#failure-semantics), [acceptance](spec.md#acceptance-criteria)

## Proposed compatibility changes

- The add-in will require an explicit source instead of silently using a whole
  worksheet after a single-cell selection. Table totals will be excluded.
- Live date interpretation becomes explicit. The public read_range default and
  workbook-file APIs retain their existing behavior.
- Old results become historical/stale when their dependencies change. Current-result
  export and navigation require verification. Core outcomes remain unchanged.
- Optional input.excel context is additive under artifact schema 1. Existing
  consumers may ignore it; artifacts without live context stay unchanged.
- Output collisions use a new unique sheet by default; replacement identifies an
  owned destination explicitly and can never clear a bound source.

These are proposed migrations, not changes made by the scoping commit. E-03/E-05
must amend affected 0005/0011 contracts and retain old artifact regression fixtures.

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
actual Mac Office.js behavior remains unobserved because the add-in entry is disabled.

E-01 corrects the existing prototype's declared minimum to ExcelApi 1.7, matching
getRangeByIndexes in its sheet writer. Generated manifests now enforce that floor;
hosts below it can no longer load the prototype. The future 1.9 workflow remains
proposed. No financial, date-reader, artifact or row-identity contract changes here.
The manifest deployment version is separately maintained at 1.0.0.0 because
Microsoft's validator rejected the package-derived 0.1.0.0 as below its minimum.
The add-in ID and actual package/report version are unchanged. This does not
establish the cause of the disabled native entry or prove a successful install.

No stable workbook date-system getter is assumed. E-01 must substantiate any
automatic path; user selection is the defined baseline. A search hit or a preview
type declaration cannot establish a supported-host contract.
