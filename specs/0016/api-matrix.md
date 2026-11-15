# 0016 E-01 — Stable Office API audit

Reviewed 2026-11-13 against the official stable API references. This is a code/API
audit, not proof that any particular Excel installation supports these members.
Actual host requirement-set answers and the read-only probe belong in baseline
evidence. Tracking issue: [#23](https://github.com/thatquantguy44/finassert/issues/23).

## Existing prototype

| Operations | Stable API set | Use |
| --- | --- | --- |
| Workbook.getSelectedRange; WorksheetCollection lookup/add; worksheet tables; table name/getRange | 1.1 | Source selection and owned-output lookup |
| Range row/column counts, rowIndex/address, values/numberFormat/valueTypes/formulas, getRow/getResizedRange | 1.1 | Chunked source capture |
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

## E-02 amendment and native observations

E-01 subsequently completed in native Excel 16.115 on Mac. All audited sets
through 1.9 were supported; calculation was Automatic/Done and the three event
members were present. See [the actual report](artifacts/e01-native-diagnostics.txt).
This supersedes the earlier unresolved-loading status without changing that
historical observation. Microsoft's sideload CLI and its generated workbook
opened the pane while the menu entry had been disabled.

E-02 uses stable Range.getMergedAreasOrNullObject (ExcelApi **1.13**) to reject
merged headers, including vertical merges at the selection edge. It checks that
capability before range binding; earlier hosts can explicitly choose a table.
Table header/body/ID APIs remain 1.1; structural notifications and sheet writes
use the 1.7 manifest floor. The later freshness workflow still needs 1.9.
Native E-02 range capture exercised the 1.13 guard successfully. No stable date
getter was established: a user choice with no default supplies every live payload.

Source: Microsoft's [stable Range reference](https://learn.microsoft.com/en-us/javascript/api/excel/excel.range?view=office-js)
and [1.13 requirement set](https://learn.microsoft.com/en-us/javascript/api/requirement-sets/excel/excel-api-1-13-requirement-set).
The [E-02 record](artifacts/e02-native-verification.json) retains actual source,
date and selection observations; the full E-06 workflow remains pending.

## E-03 amendment

Live capture now enforces stable 1.9 calculation/event support. Range.formulas
is a stable 1.1 read, checked against the [Range reference](https://learn.microsoft.com/en-us/javascript/api/excel/excel.range?view=excel-js-1.9#excel-excel-range-formulas-member)
on 2026-11-14; it supplies a separate private formula fingerprint. Rebind removes
handlers using their original contexts. Shutdown discards callbacks/session state
without starting Office requests; Microsoft documents automatic event destruction
on refresh/close in its [event lifecycle](https://learn.microsoft.com/en-us/office/dev/add-ins/excel/excel-add-ins-events#lifecycle-of-an-event-handler).
No global event disabling or recalculation is used. The E-01 expected failures
are now ordinary passing browser cases. Native E-03 evidence is retained
[here](artifacts/e03-native-verification.json); complete E-06 remains pending.

## E-04 selection audit and focused native evidence

Rechecked 2026-11-15: stable
[Range.select](https://learn.microsoft.com/en-us/javascript/api/excel/excel.range?view=excel-js-1.9#excel-excel-range-select-member(1))
is ExcelApi 1.1. Worksheet activation is also 1.1; numeric
[Worksheet.getRangeByIndexes](https://learn.microsoft.com/en-us/javascript/api/excel/excel.worksheet?view=excel-js-1.9#excel-excel-worksheet-getrangebyindexes-member(1))
uses the existing 1.7 floor. E-04 introduces no requirement-set increase. It
resolves worksheet/table IDs and validates captured geometry before selecting
numeric source coordinates. The
[focused Mac record](artifacts/e04-native-navigation.json) verifies actual F8
selection on an offset source with an apostrophe in its sheet name; no preview
API or text-derived A1 formula/link was used. Full E-06 remains pending.
