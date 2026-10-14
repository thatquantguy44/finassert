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
   names in the first row, and press the button. Select a single cell to use the
   table it is in (with its real headers), or, outside a table, everything on the
   sheet. The pane says which it used. Large selections are read in blocks.
2. **Run checks.** Starting from a template, the pane matches its columns to your
   headers and asks you to confirm each match, as the browser app does.
3. **Report.** The report names rows by the sheet's own row numbers, so "row 6" is row
   6 in Excel, even when your selection starts lower down.
4. **Write results to a sheet.** One button creates (or replaces) a sheet named
   `finassert results`. It opens with a stamp that makes the sheet usable as evidence:
   the outcome, the policy's name and fingerprint, what was checked
   (`Holdings!A3:E7`), the counts, the time (UTC), and the finassert version. Below it
   is each check and each problem row.
5. **Save and load the checks.** "Save these checks in the workbook" writes the policy
   to a sheet named `finassert policy`, one line per row, so the workbook carries its
   own checks and a colleague can load them with "Load the checks saved in the
   workbook". The sheet is plain text you can read and edit; the add-in reads column A
   from row 3.

**Your data is never changed.** The add-in writes only its own two sheets
(`finassert results` and `finassert policy`, replaced if they already exist) and never
edits, highlights, or deletes your cells.

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
python scripts/serve_excel.py --dir dist/excel --cert localhost.pem --key localhost-key.pem
```

The first command writes `taskpane.html` (the pane, one file), `manifest.xml`, and two
placeholder icons. The second serves them. Office loads the pane from a web address and
insists on HTTPS, so the certificate must be one Excel trusts: Microsoft's
`npx office-addin-dev-certs install` installs a development certificate for `localhost`,
and the files it writes are the certificate and key to pass. Without `--cert` and
`--key` the server uses plain HTTP, which is enough to look at the pane in a browser but
not for Excel. The server listens on your computer only and never caches.

Then load the add-in. Microsoft's `npx office-addin-debugging start manifest.xml desktop`
can sideload it and open Excel; or follow Microsoft's guide to sideloading Office
Add-ins for your platform: Excel on the web and Windows can upload a manifest or use a
shared-folder catalog, Mac uses a folder in Excel's container, and organizations deploy
through the Microsoft 365 admin centre (centralized deployment). These steps come from
Microsoft's documentation and have not been run against this add-in yet.

CI runs Microsoft's manifest validator (`office-addin-manifest validate`) on every
build. It calls a Microsoft web service, so for now a failure there is informational.

### Offline use

By default the pane fetches the Python engine (Pyodide) from a CDN, hash-pinned. To carry
the engine inside the add-in so the only network request left is Office's own library:

```bash
python scripts/build_excel.py --base-url https://example.com/finassert/ \
    --bundle-pyodide download            # or a path to a Pyodide 0.27.7 distribution
```

This adds a `pyodide/` folder (about 14 MB) beside the pane. Every file is checked: the
loader against the pinned hash, each package against the index's SHA-256, and the version
against the one the add-in expects. The pane's content security policy then allows
`'self'` instead of the CDN.

## Privacy and security

- The pane runs entirely in the Excel window. Your cells are passed to the engine in
  the page and are never sent anywhere.
- It does load two things from the network: Microsoft's Office library
  (`appsforoffice.microsoft.com`), which Office requires and cannot be pinned with a
  hash, and the Python engine (Pyodide), which is hash-pinned as in the browser app, or
  bundled with the add-in (see above) for no network use beyond Office's library.
- The page's content security policy allows only those two sources and the two
  scripts it contains, each pinned by hash. Whether Office's task-pane host honours
  the same policy is checked in the spike.
- Text written to the results sheet that Excel could read as a formula (starting with
  `=`, `+`, `-`, or `@`) is prefixed so it stays text.

## Not yet built

Highlighting failing cells (changes made by an add-in cannot be undone with Ctrl+Z, so
this needs a clear opt-in and a way to restore), worksheet functions such as
`=FINASSERT.CHECK(...)`, a ribbon button (the manifest only registers the task pane,
opened from Insert › My Add-ins), and AppSource publication.
