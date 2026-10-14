# Excel add-in (initial)

The add-in checks data inside Excel without saving a file first. It is a task pane
that runs the same engine as the [browser app](browser-app.md): choose a template or
open a policy, run the checks, and read the report, all in a pane beside the sheet.

**Status: initial.** Everything on the finassert side is built and tested against a
stand-in for Excel (`scripts/smoke_excel.py`). It has not yet been run in real Excel on
Windows, Mac, or the web: that is the spike in the
[design note](design/excel-integration.md), and until it has been done the add-in
should be treated as a prototype.

## What it does

1. **Use the selected cells.** Select the cells that hold your data, with the column
   names in the first row, and press the button. Select a single cell to use
   everything on the sheet. Large selections are read in blocks.
2. **Run checks.** Starting from a template, the pane matches its columns to your
   headers and asks you to confirm each match, as the browser app does.
3. **Report.** The report names rows by the sheet's own row numbers, so "row 6" is row
   6 in Excel, even when your selection starts lower down.
4. **Write results to a sheet.** One button creates (or replaces) a sheet named
   `finassert results` listing each check and each problem row. **Your data is never
   changed**; the add-in does not edit, highlight, or delete cells.

## How Excel's cells are read

The same rules as a saved workbook and a CSV file, so a check gives the same answer
either way:

- Numbers keep their shortest decimal text (`0.1`, not `0.1000000000000000055`), and
  whole numbers become integers. Excel keeps 15 significant digits.
- A cell whose number format is a date is read as a date, not a serial number.
  Workbooks that count dates from 1904 are read with the 1900 system unless told
  otherwise; Office does not report which one a workbook uses, so check dates in a
  1904 workbook.
- Percentages are never rescaled: a cell showing 40% holds 0.4 and stays 0.4.
- Numeric text is read as a number; blank and spaces-only cells are blank, and blanks
  are never zero.
- A cell showing an Excel error (`#N/A`, `#DIV/0!`) is an invalid value that fails the
  row. The pane tells you how many there are and where.

## Building and trying it

```bash
python scripts/build_excel.py --base-url https://localhost:3000/ --output-dir dist/excel
```

This writes `taskpane.html` (the pane, one file), `manifest.xml`, and two placeholder
icons. Office loads the pane from a web address, so the files must be served over
HTTPS from the `--base-url` you gave (a static host is enough). For local trials,
Microsoft's `office-addin-dev-certs` tool installs a trusted development certificate.

Then load the add-in following Microsoft's guide for sideloading Office Add-ins on your
platform: Excel on the web and Windows can upload a manifest or use a shared-folder
catalog, Mac uses a folder in Excel's container, and organizations deploy through the
Microsoft 365 admin centre (centralized deployment). The manifest should also be
checked with Microsoft's `office-addin-manifest validate`, which has not yet been run
against this one.

## Privacy and security

- The pane runs entirely in the Excel window. Your cells are passed to the engine in
  the page and are never sent anywhere.
- It does load two things from the network: Microsoft's Office library
  (`appsforoffice.microsoft.com`), which Office requires and cannot be pinned with a
  hash, and the Python engine (Pyodide), which is hash-pinned as in the browser app.
  Bundling Pyodide with the add-in for fully offline use is planned.
- The page's content security policy allows only those two sources and the two
  scripts it contains, each pinned by hash. Whether Office's task-pane host honours
  the same policy is checked in the spike.
- Text written to the results sheet that Excel could read as a formula (starting with
  `=`, `+`, `-`, or `@`) is prefixed so it stays text.

## Not yet built

Highlighting failing cells (changes made by an add-in cannot be undone with Ctrl+Z, so
this needs a clear opt-in and a way to restore), worksheet functions such as
`=FINASSERT.CHECK(...)`, a ribbon button (the manifest only registers the task pane,
opened from Insert › My Add-ins), a bundled offline engine, and AppSource publication.
