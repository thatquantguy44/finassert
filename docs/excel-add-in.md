# Excel add-in (initial)

Read the [comprehensive user guide](user-guide.md) or choose **Download user guide
(PDF)** in the pane. The local server exposes matching metadata at
`GET /api/finassert/v1/user-guide` and the attachment at
`GET /api/finassert/v1/user-guide.pdf`. The guide is a public, read-only document;
downloading it does not read workbook cells or enable the private reference reader.

The add-in checks data inside Excel without saving a file first. It is a task pane
that runs the same engine as the [browser app](browser-app.md): choose a template or
open a policy, run the checks, and read the report, all in a pane beside the sheet.

**Status: initial, with a native Mac baseline.** Excel 16.115 on macOS 26.5.1
opened the corrected sideloaded pane and passed the synthetic 50,000-row diagnostic
on 2026-11-13. Engine startup was 1,062 ms, reading/preview 561 ms and template
checking/render 631 ms. This verifies that build and fixture; the complete
freshness/navigation/output workflow and Windows/web acceptance remain pending.
See the [evidence](https://github.com/thatquantguy44/finassert/blob/main/specs/0016/artifacts/README.md)
and [real-host runbook](design/excel-spike.md).

The manifest declares ExcelApi 1.7 because results/policy sheet writes use
`getRangeByIndexes`. Diagnostics also probe the planned spec 0016 floor of 1.9,
record calculation mode/state and check event members without changing settings.
Range binding additionally needs stable ExcelApi 1.13 for merged-header detection;
on earlier hosts, choose a table or update Excel. Live capture requires ExcelApi
1.9, settled calculation and a required date-system choice.
The manifest deployment version is 1.0.0.1; the pane
and reports retain the actual finassert package version. Maintainers bump
ADD_IN_VERSION in scripts/build_excel.py when releasing an updated manifest.

The two Home commands open tabs named **finassert Validation** and **finassert
Settings**. Each pane starts with a large **Validation** or **Settings** heading
and an explanation of that panel. After updating an installed manifest, restart
Excel if it still displays cached tab names. Save work before restarting.

In results sheets, **Result** is what happened. **If check fails** describes the
policy action: **Block validation**, **Show warning**, or **Show information**.
A passed check can be configured to block if it fails. The underlying JSON and
policy still use severity values `error`, `warning`, and `info`.

The next delivery is scoped in
[spec 0016](https://github.com/thatquantguy44/finassert/blob/main/specs/0016/spec.md):
explicit source/date binding and configurable stable capture/freshness are
implemented as E-02/E-03. E-04 navigation and E-05 verified snapshot exports,
unique destinations and saved ownership are merged into main. E-06 has prepared
synthetic fixtures and a retained-export/CLI verifier. On 2026-11-16 the current
build passed native 50,000-row diagnostics, verified capture, actual JSON/HTML/
worksheet parity, strict CLI comparison and source integrity. Native write/read/
check-render timings were 322/732/750 ms. The small correction/date loop now passes on native 1900 and 1904, with actual
exports/CLI parity and source integrity. Table/hidden/failure/race/keyboard cases
remain pending; complete Mac acceptance is not claimed. Maintainers can
follow the [current pickup](https://github.com/thatquantguy44/finassert/blob/main/specs/0016/acceptance.md#current-pickup-and-retained-native-files).

An optional [QuantSmith reference](quantsmith-reference.md) panel reads its
configured local checkout by default, with an explicit pinned-GitHub alternative,
through the add-in's same-origin, read-only API. It is loaded only when requested
and does not send workbook data. Real Excel host acceptance of this panel is pending.

## What it does

1. **Bind one source.** Choose a workbook table and press **Use this table**, or
   select one rectangle with a header row and data and press **Use selected range**.
   Tables use their actual header/body and exclude totals; fixed range bounds own
   totals exclusion. A single cell never expands to the whole sheet. Choose the
   workbook's **1900 or 1904 date system**; neither is preselected. The summary
   shows the sheet, exact address, header, physical/parsed rows, width and date
   interpretation. Hidden and filtered rows are included. Moving the selection
   keeps the source bound. Structural range edits require reselection; missing
   sheet/table IDs cannot be replaced just by matching a display name.
2. **Run checks.** Starting from a template, the pane matches its columns to your
   headers and asks you to confirm each match, as the browser app does. Each Run
   rereads the bound source. Changed headers require rebinding and mapping review;
   failed/partial reads cannot run. Rebinding or changing dates clears the result.
   The pane shows Current only after matching stable captures around evaluation.
   Relevant edits, recalculation, policy or settings changes make old results
   historical. Currentness is separate from whether the financial checks passed.
3. **Report and navigate.** Diagnostic findings show complete counts, example
   caps, truncation and retained row/group examples. Use **Select cell** or
   **Select source row** with a mouse or keyboard. Navigation rechecks the source,
   then selects one unambiguous cell or the source columns of a physical row.
   Ordinary labels use Excel's physical row numbers, including gaps. Configured
   business keys are resolved against the captured data; they are never treated
   as worksheet row numbers. Duplicate/colliding keys require a unique key and
   rerun. Missing groups/periods show **No source row**. Stale, blocked and
   snapshot-only results cannot navigate; correct the cause and rerun.
4. **Write results to a sheet.** A Current result is reread and compared again
   before sheet/JSON/HTML export; missed events cannot authorize an old result.
   The default button creates `finassert results`, or a unique numbered name
   when that name already exists. It opens with a snapshot stamp:
   the outcome, the policy's name and fingerprint, what was checked
   (`Holdings!A3:E7`), source IDs/bounds, parsed and physical row counts, date
   interpretation, evaluated snapshot digest, capture/verification times (UTC)
   and the finassert version. Each check shows canonical counts/caps/truncation
   and retained examples. **Refresh output sheets**, choose a completed owned
   destination, then **Replace selected results sheet** to replace it explicitly.
   Exported evidence describes its captured snapshot; later source edits require
   a new run and never silently rewrite earlier output.
5. **Save and load the checks.** "Save these checks in the workbook" writes the policy
   to `finassert policy` or a new unique name, one line per row, so the workbook carries its
   own checks and a colleague can load them with "Load the checks saved in the
   workbook". Choose the saved policy in the picker; use **Refresh saved policies**
   after reopening. The sheet is plain text you can read and edit; the add-in reads
   column A from row 3. Valid policy save/load and YAML download remain available
   independently of result freshness or invalid capture settings. Legacy default
   policy sheets can still be read without being adopted as writable destinations.

**Your source data is never changed.** Normal output uses `finassert results`
and `finassert policy` with unique names on collision. Replacement requires a
completed results sheet's saved ownership ID and can never clear a bound source
sheet. Ownership is saved with the workbook, independently of session-only source
and capture settings. Names alone, including outputs from older builds without
ownership records, do not authorize replacement.

## Output failures

Rows and text limits are checked before creating or clearing a sheet. Excel output
is limited to 5,000,000 cells, normal worksheet bounds and 32,767 characters per
cell; use JSON/HTML for larger text. Protected sheets, host errors or cancellation
report an export failure and may leave a clearly incomplete destination. Completion
is recorded only after body/style writes succeed. Recovery marks the same owned
operation incomplete where the host permits it; no partial sheet is deleted.
Correct the cause, rerun checks for a Current result and create a new output.
If completion cannot be confirmed, do not use that sheet as completed evidence.

## Freshness and capture settings

Open **Freshness and capture settings** in the pane. Settings last for this pane
session; reopening restores defaults and requires a new binding/date choice.
Changing settings requires a new run.

| Setting | Default | Choices |
| --- | --- | --- |
| Change monitoring | Live workbook events | Live alerts or on demand |
| Capture verification | Verify stable captures | Verified or snapshot only |
| Matching captures | 2 | 2–4 |
| Rows per request | 5,000 | 1–5,000 |
| Cells per request | 50,000 | 1,000–50,000 |
| Operation timeout | 120 seconds | 1–300 seconds |

On demand turns off immediate value/format/calculation alerts; Run, navigation and export
still verify the source. Current always describes the last verification time.
Snapshot only evaluates one capture for inspection and stays unverified/Stale;
current-result exports and navigation remain unavailable. Restore defaults returns to live events
and two matching captures. Neither option changes the financial rules.

Unbound needs a source; Ready needs a run; Reading/Checking are in progress;
Current matched at the displayed UTC time; Stale is historical; Blocked explains
a problem that needs correction. Manual calculation requires calculating in Excel
and checking **I calculated this workbook in Excel** before the next action.
The pane never recalculates or changes Excel's calculation mode.

Cancel and timeout take effect between host requests. An outstanding request or
Python evaluation cannot be interrupted. Reduce request sizes for host payload
errors; a single row must fit the configured cell limit. The total source ceiling
remains 5,000,000 cells.

## How Excel's cells are read

The same rules as a saved workbook and a CSV file, so a check gives the same answer
either way:

- Numbers keep their shortest decimal text (`0.1`, not `0.1000000000000000055`), and
  whole numbers become integers. Excel keeps 15 significant digits.
- A cell whose number format is a date is read as a date, not a serial number.
  Choose 1900 or 1904 to match the workbook setting before reading. The add-in
  passes that choice explicitly and does not change Excel's date setting.
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
through the Microsoft 365 admin centre (centralized deployment). The Mac CLI route was verified for the native baseline; Windows/web and
centralized deployment remain unverified. If the Mac menu entry is disabled, the
CLI-generated sideload workbook can open the pane. Run the CLI from a directory
with a minimal package.json (it expects one), using --no-debug --no-live-reload
and --dev-server-port 3000 when the HTTPS server is already running.

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

## Ribbon access

The generated manifest adds a **finassert** group to Excel's **Home** ribbon with
**Open validation** and **Settings**. **Open validation** opens the normal workflow.
**Settings** opens a separate, focused settings view in the task pane with the
freshness, capture and request-limit controls; it hides the validation workflow and
has a **Back to validation** action that preserves the open pane's session. These
commands do not run checks or change workbook cells by themselves. The manifest
passes static Office schema validation. Native Mac Home visibility, both launch
routes and validation engine Ready were observed on 2026-11-20. Full Mac acceptance
and broader platform support remain pending.

## Not yet built

Highlighting failing cells (changes made by an add-in cannot be undone with Ctrl+Z, so
this needs a clear opt-in and a way to restore), worksheet functions such as
`=FINASSERT.CHECK(...)`, custom/contextual ribbon workflows, and AppSource publication.
