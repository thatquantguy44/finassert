# 0011 — Excel workbook integration

**Status:** Proposed

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
header selection, a column mapping onto 0004 contracts, row identity that points
at worksheet row numbers, and a tabular `.xlsx` diagnostics export.

## Non-goals

Excel add-ins, Office.js, xlwings or COM automation, UDFs, Microsoft Graph or
other hosted workbook APIs, macro (`.xlsm`) execution, formula recalculation,
writing results into the source workbook, and a general REST service. These are
deferred below; "Excel API" in this spec means a Python API for workbook files.

## Proposed architecture

An optional `excel` extra depends on openpyxl and is never imported by the core.
`read_workbook` returns a column source satisfying the 0004 `ColumnSource`
contract, reusing `ColumnMapping`. `write_report_xlsx` renders a 0005 report to
a workbook. Reading opens files read-only with `data_only=True`, so only cached
formula values are seen and the file is never modified.

## Public API design

```python
from finassert.adapters import ColumnMapping, GroupKey
from finassert.excel import read_workbook, write_report_xlsx

source = read_workbook(
    "positions.xlsx",
    sheet="Positions",
    header_row=3,
    mapping=ColumnMapping(
        columns={"market_value": "MV (USD)", "weight": "Weight"},
        group_keys=(GroupKey("portfolio", "Portfolio"),),
    ),
)
report = fa.check(source, rules)
write_report_xlsx(report, "validation.xlsx")
```

Proposed CLI extension to 0007: `--format xlsx --sheet NAME --header-row N` and
`--output report.xlsx`.

## Data contracts

Row labels default to the worksheet row number (1-based, as Excel displays it)
and are unique unless a `row_key` column is configured. Headers are matched
exactly after documented whitespace trimming; duplicate headers are an error.
Cell values map as follows: numeric cells to `Decimal` via their stored text
where available, never through binary float rounding; blank cells to `None`;
error cells (`#N/A`, `#DIV/0!`) to a distinct error marker that rules treat as
an evaluation error, not a null; dates to `datetime.date` or timezone-naive
`datetime` with the workbook epoch (1900 or 1904) honored. The report workbook
has fixed sheets: `Summary`, `Results`, and `Diagnostics` (one row per
diagnostic with sheet, row, column, rule ID, outcome, expected, observed).

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

1. Freeze cell-to-value conversion table and error marker. 2. `read_workbook`
with header and mapping handling plus row-number labels. 3. Contract tests from
0004. 4. `write_report_xlsx`. 5. CLI flags in 0007. 6. Decide whether totals-row
and hidden-row handling need explicit options.

## Acceptance criteria

Core imports without openpyxl; reading never modifies the file; diagnostics cite
the worksheet row Excel shows; Decimal values round-trip without float drift;
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
