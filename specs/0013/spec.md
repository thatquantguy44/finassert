# 0013 — Excel workbook integration

**Status:** Reader, report writer, and CLI worksheet-region/report extensions implemented (initial)

## Problem statement

Finance teams keep positions, NAV bridges, and cash ledgers in Excel workbooks.
Validating them today requires users to load sheets into pandas themselves, with
no documented handling of merged headers, formulas, or reporting back to the
workbook.

## Motivation and use cases

Analysts validate a sheet before it is circulated, operations teams gate a
workbook in CI via the CLI (0007), and reviewers receive diagnostics as an
`.xlsx` they can filter and annotate.

## Goals

Define optional, explicit workbook input and report output: named sheet and
header selection, a `ColumnSource` over physical header names, row identity that points at
worksheet row numbers, and a tabular `.xlsx` report export.

## Non-goals

Excel add-ins, Office.js, xlwings or COM automation, UDFs, Microsoft Graph or
other hosted workbook APIs, macro (`.xlsm`) execution, formula recalculation,
writing results into the source workbook, and a general REST service. These are
deferred below; "Excel API" in this spec means a Python API for workbook files.

## Proposed architecture

An optional `excel` extra depends on openpyxl and is never imported by the core.
`read_workbook` returns an object satisfying the core `ColumnSource` protocol
(`column(name) -> (values, labels)`), exactly like `PandasDataFrameAdapter`. It
exposes physical headers only. `ColumnMapping` stays on the rules, as in 0004,
and its `row_key` and group keys are resolved by the existing extraction path,
so the reader needs no mapping argument. `write_report_xlsx` renders a 0005
report to a workbook. Reading opens files read-only with `data_only=True`, so only cached
formula values are seen and the file is never modified.

## Public API design

```python
from finassert.adapters import ColumnMapping, GroupKey
from finassert.excel import read_workbook, write_report_xlsx

mapping = ColumnMapping(
    columns={"market_value": "MV (USD)", "weight": "Weight"},
    group_keys=(GroupKey("portfolio", "Portfolio"),),
)
source = read_workbook("positions.xlsx", sheet="Positions", header_row=3)
report = fa.check(source, rules_built_with(mapping))
write_report_xlsx(report, "validation.xlsx")
```

Use `hidden="include"` (default) or `hidden="reject"` with `read_workbook`,
`parse_xlsx` or `load_input`. Include retains every selected row/column; reject
errors on a hidden selected sheet, row (including the header), or named column.
Neither mode silently skips cells. `workbook_metadata` records sheet state and
counts/examples/truncation of hidden selected rows/columns, capped at 20 examples.
CLI `--hidden include|reject` applies the same policy and records that metadata
in the additive artifact `input.workbook` field. Hidden rows outside explicit
bounds and unnamed columns do not affect the selected region.
Merged ranges intersecting the header row are rejected as ambiguous in both
readers; no merged header filling is inferred.

CLI extensions to 0007: `--format xlsx --sheet NAME --header-row N --max-row N`
select the worksheet region. `--xlsx report.xlsx` writes the reviewer workbook;
`--output report.json` retains the existing JSON artifact contract.

## Data contracts

Row labels default to the worksheet row number (1-based, as Excel displays it)
and are unique unless a `row_key` column is configured. Headers are matched
exactly after documented whitespace trimming; duplicate headers are an error.
Cell values map as follows: numeric cells to `Decimal` from the shortest round-trip
representation of the value openpyxl parsed (`Decimal(repr(x))`, so `0.1` is
`Decimal('0.1')`, never the binary expansion); blank cells to `None`;
error cells (`#N/A`, `#DIV/0!`) to a distinct error marker that rules treat as
an evaluation error, not a null; dates to `datetime.date` or timezone-naive
`datetime` with the workbook epoch (1900 or 1904) honored. The report workbook
has fixed sheets: `Summary` (counts by outcome) and `Results` (one row per
`ValidationResult`: rule ID, name, outcome, severity, message, observed,
expected, tolerance, and `metadata` serialized as canonical JSON text). Decimals
are written as text to avoid float drift. Rule metadata is currently free-form
(`missing_rows`, `invalid_positions`, ...), so the writer does not flatten it
into per-row records. A `Diagnostics` sheet renders the structured, bounded
collections defined by 0005, retaining total count, cap, and truncation. Values beginning with `=`, `+`, `-`,
or `@` are written as text to prevent formula injection when a reviewer opens the
report.

## Financial and numerical edge cases

Percent-formatted cells (`5%` stored as `0.05`), accounting-format negatives,
thousands scaling in headers, hidden rows and columns, merged header cells,
totals rows under the data, formulas with no cached value (file never opened in
Excel), text-typed numbers, and currency stored only in number format.
Currency is never inferred from formatting; it must come from a column or from
0008 configuration.

## Failure semantics

Missing sheet, header row, or mapped column is an error. Formula cells with no
cached value are evaluation errors naming the cell. Password-protected, corrupt,
or unsupported files are input errors. A skipped or unreadable region is never a
pass. Reports never include full rows beyond the bounded diagnostic fields.

## Implementation milestones

1. Cell conversion table and distinct error marker (complete).
2. Reader, header selection, explicit row bound, and row labels (complete).
3. Shared 0004 contracts and generated adapter equivalence (complete).
4. Atomic `write_report_xlsx` with literal strings/Decimals (complete).
5. CLI worksheet-region and report flags (complete).
6. Explicit include/reject hidden-region policy and bounded visibility metadata (complete); totals
   are excluded through an explicit row bound.
7. Structured bounded Diagnostics sheet under 0005 (complete).

## Open questions

- Hidden input policy is resolved as explicit include/reject; include remains
  the compatibility default, with metadata retained in CLI artifacts.
- How is the end of data detected when a totals row follows? Implemented as an
  explicit `max_row` option; only fully blank trailing rows are dropped.
- Is `data_only=True` acceptable when a workbook was last saved by a tool that
  does not cache formula values? Implemented: yes; the first uncached formula cell is
  an input error naming the cell.

## Acceptance criteria

Core imports without openpyxl; reading never modifies the file; row labels
passed to rules are the worksheet row numbers Excel shows; Decimal values round-trip without float drift;
formula and error cells fail loudly; results match the same data passed through
the pandas adapter.

## Testing requirements

Generated fixture workbooks covering every edge case above, the shared 0004
adapter contract suite, a byte-for-byte non-mutation check, round-trip of the
report workbook, Hypothesis cases for header and row-label alignment, and a CLI
subprocess test for `.xlsx` input and output.

## Dependencies on other specifications

Uses 0001, 0003, 0004, and 0005. CLI flags extend 0007. Currency handling
defers to 0008.

## Explicit deferred work

Excel add-in or Office.js task pane, xlwings/COM live integration, custom
worksheet functions, Microsoft Graph or other hosted Excel APIs, `.xls` legacy
format, `.xlsb`, in-place annotation of the source workbook, and charts in the
report are deferred.
