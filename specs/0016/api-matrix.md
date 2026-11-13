# 0016 E-01 — Stable Office API audit

Reviewed 2026-11-13 against the official stable API references. This is a code/API
audit, not proof that any particular Excel installation supports these members.
Actual host requirement-set answers and the read-only probe belong in baseline
evidence. Tracking issue: [#23](https://github.com/thatquantguy44/finassert/issues/23).

## Existing prototype

| Operations | Stable API set | Use |
| --- | --- | --- |
| Workbook.getSelectedRange; WorksheetCollection lookup/add; worksheet tables; table name/getRange | 1.1 | Source selection and owned-output lookup |
| Range row/column counts, rowIndex/address, values/numberFormat/valueTypes, getRow/getResizedRange | 1.1 | Chunked source capture |
| Worksheet.getUsedRange(valuesOnly=true) | 1.2 for valuesOnly | Single-cell fallback and policy loading |
| Range.getIntersectionOrNullObject; Worksheet.getUsedRangeOrNullObject; WorksheetCollection.getItemOrNullObject | 1.4 | Table hit detection and output existence |
| Worksheet.getRangeByIndexes | 1.7 | Results/policy/diagnostic sheet writes |
| Range.clear, values/numberFormat assignment, font formatting, column autofit, worksheet activation | Covered by the 1.7 floor above | Owned-output rendering |

The former diagnostic claim of 1.4 overlooked getRangeByIndexes. The manifest
and current-prototype diagnostic now declare **1.7**. This is a support-declaration
correction, not an implementation of the proposed 1.9 workflow or a statement
about the local host. Existing read/policy/report semantics are preserved.

Sources: [Workbook](https://learn.microsoft.com/en-us/javascript/api/excel/excel.workbook?view=excel-js-1.9),
[Worksheet](https://learn.microsoft.com/en-us/javascript/api/excel/excel.worksheet?view=excel-js-1.9),
[WorksheetCollection](https://learn.microsoft.com/en-us/javascript/api/excel/excel.worksheetcollection?view=excel-js-1.9),
[Table](https://learn.microsoft.com/en-us/javascript/api/excel/excel.table?view=excel-js-1.9),
[Range](https://learn.microsoft.com/en-us/javascript/api/excel/excel.range?view=excel-js-1.9),
[RangeFormat](https://learn.microsoft.com/en-us/javascript/api/excel/excel.rangeformat?view=excel-js-1.9).

## Planned workflow

| Proposed operation | Stable API set / decision | Owner |
| --- | --- | --- |
| Table.getHeaderRowRange / getDataBodyRange / getTotalRowRange; worksheet/table IDs | 1.1; use explicit boundaries and identities | E-02 |
| Worksheet.onChanged | 1.7 | E-03 |
| Worksheet.onCalculated | 1.8 | E-03 |
| Worksheet.onFormatChanged | 1.9 | E-03 |
| Application.calculationMode get | 1.1; never set it | E-03 |
| Application.calculationState get | 1.9 | E-03 |
| Range.select and worksheet activation | 1.1, after target verification | E-04 |
| Workbook date system | No stable getter is part of the audited 1.9 contract; explicit user choice remains the baseline | E-02 |

The proposed full-workflow floor remains **1.9**. The new diagnostic probes mode,
state and event-member presence only after isSetSupported reports 1.9. It does
not subscribe handlers, trigger calculation, inspect user cells, guess an epoch,
or validate support by reading an undocumented/preview property. Pending/manual
states are recorded, not enforced by this E-01 observation tool.

Sources: [Worksheet events](https://learn.microsoft.com/en-us/javascript/api/excel/excel.worksheet?view=excel-js-1.9),
[Application calculation properties](https://learn.microsoft.com/en-us/javascript/api/excel/excel.application?view=excel-js-1.9),
[event lifecycle](https://learn.microsoft.com/en-us/office/dev/add-ins/excel/excel-add-ins-events),
[Excel date systems](https://support.microsoft.com/en-us/excel/date-systems-in-excel).

## Verification boundary

Browser regressions use actual bundled finassert/Pyodide and a configurable Office
stand-in. They cover unsupported 1.9, Automatic/Done, Manual/Pending and
Automatic/Calculating without changing settings. These tests establish probe
behavior, not real host support. Three strict expected failures reproduce Run
using an old snapshot and exports remaining available after source/policy changes.
They must become ordinary passing tests when E-03 implements those contracts.

Mac application metadata and the concrete add-in-loading finding are recorded in
[the baseline evidence](artifacts/e01-baseline.json). No actual Office.js capability
or timing value is substituted with a stand-in result.
