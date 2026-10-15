# Excel integration design

**Status:** the finassert side is built and tested against a stand-in for Excel (see
[the add-in](../excel-add-in.md)); the spike below, which needs real Excel, has not been run.

Spreadsheet *files* already work: `finassert check` and the browser app read
`.xlsx` workbooks. This note covers checking data *inside* Excel, without saving
a file first. It records what exists in the market, the options, and a
recommendation, so the next step is a small experiment rather than a guess.

## What exists

A search of the market in October 2026 found no public API or Excel add-in that
checks finance-specific invariants (holdings against NAV, cash roll-forward,
exposure limits) in place. The nearest things do something else:

- **Excel's own data validation** ([`Range.dataValidation`](https://learn.microsoft.com/en-us/office/dev/add-ins/excel/excel-add-ins-data-validation))
  checks one cell as it is entered. Only the "stop" alert style blocks entry.
  It cannot express "this column adds up to that cell".
- **Reconciliation platforms** (Duco, SmartStream, and Gresham's
  [Control for Investment Management](https://funds-europe.com/gresham-launches-cloud-upgrade-for-investment-managers/),
  formerly Electra) take files into a hosted workspace. The search found no
  documented Excel upload API for NAV reconciliation from any of them.
- **Vendor add-ins** such as [ScaleX Invest's](https://www.scalex-invest.com/blog/scalex-invest-releases-an-excel-add-in-for-seamless-data-export-and-reporting)
  pull the vendor's own data into Excel; they do not validate yours.
- **Data-quality libraries** (Great Expectations, Pandera, Soda) have no
  finance rules and no Excel integration.

## What can host the checks

| Option | Fit |
|---|---|
| **Python in Excel** (Microsoft's feature) | Not viable. It runs in a Microsoft cloud container with [no network access and a curated Anaconda package set](https://support.microsoft.com/en-us/excel/python/data-security-and-python-in-excel), so finassert cannot be installed, and the data leaves the computer. |
| **Office add-in (task pane) running Pyodide** | Recommended. [xlwings Lite](https://www.xlwings.org/lite/vs-python-in-excel) already runs Pyodide inside an Excel task pane on Windows, macOS, and Excel on the web, which removes the biggest unknown. finassert already runs under Pyodide in the browser app. |
| **Thin add-in calling a local or hosted service** | Works everywhere but reintroduces a server, and the "your files never leave this computer" promise becomes a deployment detail. Keep as a fallback if Pyodide proves too heavy in a locked-down environment. |
| **Build on xlwings Lite or PyXLL** | Faster start, but adds a dependency (xlwings Lite's self-hosted option is paid) and puts a third party between users and the checks. |
| **Do nothing new** | Valid: save as `.xlsx` and use the CLI or browser app. The add-in only removes that step. |

## Recommendation

An Office add-in whose task pane is the existing browser app, adapted to read
from and write to the workbook through the [Excel JavaScript API](https://msdn.microsoft.com/EN-US/library/mt616485.aspx).
The Python engine, policies, templates, column matching, and reports are reused
unchanged, so results in Excel match the command line and browser app exactly.

How it behaves:

1. **Read** the selected range, a named table, or the used range of a sheet.
   The first row is the header row, as for CSV.
2. **Run** a policy chosen from the templates, opened from a file, or built in
   the pane, with the same column matching and confirmation notes.
3. **Report** in the pane (the HTML report), and optionally write a **Results
   sheet** with one row per failing check or row. The user's data is never
   modified. Marking failing cells (a fill or comment) was considered and left out
   of the first version: changes made by an add-in cannot be undone with Ctrl+Z, so
   it needs a clear opt-in and a way to restore.
4. **Export** the policy (YAML) and report, so the same checks run in a pipeline.

## Numbers, dates, and what Excel hands over

- **Numbers** arrive as doubles. Convert through their shortest decimal text
  (`0.1`, not `0.1000000000000000055…`), which matches what the `.xlsx` loader
  reads from a saved file, so a check gives the same answer either way. Excel
  keeps 15 significant digits, and the report should say values were read as
  Excel stores them.
- **Dates** arrive as serial numbers. Request each cell's number format with the
  values and reuse the date handling in `_xlsx.py`, including the 1904 date
  system, so a date column is not mistaken for a number.
- **Formulas** return their cached values; a cell showing an error (`#N/A`,
  `#DIV/0!`) is an invalid value that fails the row, never a blank or zero.
- **Blank, text, and percent cells** keep the loader's rules: blanks are never
  zero, numeric text is read as a number, and a percentage stored as 0.4 or 40 is
  never rescaled.
- **Selection size**: ranges are read in blocks. The practical limits on one
  request's size are to be measured in the spike.

## Distribution and trust

- A task pane is a web page, so it must be served over HTTPS from a static host.
  After loading, it should make no network requests; to keep that promise
  offline, Pyodide and the finassert wheel are bundled with the add-in instead
  of fetched from a CDN (about the size of the current browser app plus
  Pyodide's runtime).
- Microsoft [recommends centralized deployment](https://learn.microsoft.com/en-us/office/dev/add-ins/publish/publish)
  for organizations. SharePoint catalogs do not support newer manifest features
  and do not support Excel for Mac; Mac users need AppSource or centralized
  deployment. AppSource requires certification.
- The browser app's Content-Security-Policy and subresource-integrity pinning
  carry over. Whether the Office task pane allows the same policy is a question
  for the spike.

## Spike before committing

The runbook is [real-Excel spike](excel-spike.md): a diagnostics panel in the add-in runs
most of this list and produces a report; a short manual list covers the rest.

A one-week experiment, in this order, stops at the first blocker:

1. Load Pyodide and the finassert wheel in a task pane on Windows, Mac, and
   Excel on the web; record start-up time and memory.
2. Read a 50,000-row range and run the multi-portfolio template; record time.
3. Confirm the pane makes no requests after load and the policy is respected.
4. Write a Results sheet and mark failing cells.
5. Confirm a sideloaded and a centrally deployed copy both work.

If step 1 fails on any platform, fall back to the thin-service option for that
platform, or ship the add-in for the platforms where it works.

## Not in scope

Custom worksheet functions such as `=FINASSERT.CHECK(range, policy)`. They are
attractive but recalculate often and hide failures inside cells, against the
rule that failures are never shown as passes. Reconsider once the task pane
exists. Live data feeds, write-back of corrected values, and macros are also out.
