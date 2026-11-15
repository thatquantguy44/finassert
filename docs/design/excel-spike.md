# Real-Excel spike: runbook

The native Mac E-01 baseline passed on 2026-11-13 in Excel 16.115. The
[retained report](https://github.com/thatquantguy44/finassert/blob/feature/excel-source-binding-dates/specs/0016/artifacts/e01-native-diagnostics.txt)
records capabilities, calculation and 50,000-row timings. E-03 adds session-configurable
capture/freshness with separate evidence; the completed E-04–E-06
workflow still requires its own acceptance run. This is the repeatable host test. It takes about 15 minutes per platform: a built-in
diagnostics panel runs most of the checklist and produces a report to send back, and a
short list of manual checks covers what only a person looking at Excel can judge.

Do this on **each platform that matters to you** (Excel on Windows, Excel on Mac,
Excel on the web), and keep going past a failure: a failure on one platform does not
stop the others, and the report says exactly what broke.

## What you need

- Excel with the Microsoft 365 or a recent perpetual build, and a **new, empty workbook**
  (the diagnostics create one sheet, `finassert spike data`, with 50,000 rows).
- A computer that can run `python` 3.11+ and `node` (for Microsoft's tools). Everything
  below runs on your computer; nothing is uploaded.
- About 150 MB of free disk if you want the offline build.

## 1. Build and serve

```bash
git clone https://github.com/thatquantguy44/finassert && cd finassert
python scripts/build_excel.py --base-url https://localhost:3000/ --output-dir dist/excel
npx --yes office-addin-dev-certs install        # a certificate Excel trusts for localhost
python scripts/serve_excel.py --dir dist/excel \
    --cert ~/.office-addin-dev-certs/localhost.crt --key ~/.office-addin-dev-certs/localhost.key
```

(The certificate files are in the folder the `install` command prints; on Windows it is
under `%USERPROFILE%\.office-addin-dev-certs`.) Check `https://localhost:3000/taskpane.html`
opens in a browser without a certificate warning.

## 2. Load the add-in

Pick one route per run and **say which one in the diagnostics**; the spike should be
repeated once with a second route (step 5 of the original plan: sideloaded, then
centrally deployed).

| Platform | Route |
|---|---|
| Windows or Mac | `npx --yes office-addin-debugging start dist/excel/manifest.xml desktop --app excel` opens Excel with the add-in loaded. |
| Excel on the web | Insert › Add-ins › My Add-ins › Manage My Add-ins › **Upload My Add-in**, choose `dist/excel/manifest.xml`. |
| Any (organization) | Upload the manifest in the Microsoft 365 admin centre under Integrated apps (centralized deployment). |

The Mac CLI route has been verified. The CLI expects a package.json in its working
directory; a disposable directory with a minimal private package suffices. With
the server already running, add --no-debug --no-live-reload --dev-server-port 3000.
Open the generated sideload workbook if Excel does not bring it forward. The
Developer Add-ins menu was disabled in the baseline; the generated workbook opened
the pane successfully. Other platforms/routes remain unverified. Record failures.

Then open **Insert › My Add-ins › finassert**. The pane should open and say "Ready"
after a few seconds.

## 3. Run the diagnostics

In the pane, choose **1900 or 1904** to match this disposable workbook, open
**Diagnostics for testers**, choose how the add-in was loaded, leave
**Test portfolios** at 1000 (50,000 rows), press **Run the diagnostics**, and wait (a
minute or two). Press **Copy the report** and paste it into your reply.

Each line is `PASS`, `FAIL`, or `INFO`:

| Step | Passes when | If it fails |
|---|---|---|
| Excel API support | ExcelApi 1.7 is supported; sheet writes use `getRangeByIndexes` (the null-object methods need 1.4) | The manifest declares 1.7; record an unsupported host without claiming compatibility. |
| planned workflow API baseline | ExcelApi 1.9 supports reading calculation state; edit/calculation/format event members are present | Record the failure for spec 0016. This probe reads metadata only and does not implement freshness or date selection. |
| engine start-up | the engine is ready in under 120 s | The pane may be too heavy for that platform: use the offline build, then the thin-service fallback. |
| security policy | no content-security-policy violations | Office's task-pane host does not honour the page's policy, or blocks one of its sources: send the violation text. |
| network use | requests go only to the page's own origin, `appsforoffice.microsoft.com`, and (unless bundled) `cdn.jsdelivr.net`, and none after the engine is ready | Something is calling out that should not: send the origins. |
| write 50,000 test rows / read them back | all 50,000 rows come back | Office's request size limit is lower than the 5,000-row block: reduce `BLOCK_ROWS`. |
| run the multi-portfolio template | exactly the 3 planted breaks are found in each of the two grouped checks, and the data checks pass | Wrong numbers at scale: a correctness bug. Send the report. |
| write the results sheet | the sheet is written | Send the message. |
| save and load the checks | the policy round-trips unchanged | Excel altered a line of the policy text; see manual check 4. |
| your data was not changed | the test rows read back identical after every step | **Stop and report**: the add-in must never change data. |

The timings (milliseconds) matter as much as pass and fail: if reading 50,000 rows takes
more than about 30 seconds, say so.

## 4. Manual checks

These need a person looking at Excel. Note what you see.

1. **Excel errors.** In a new sheet, make a small table with a header row and a cell
   containing `=NA()`. Select it and press **Use selected range**. The pane should
   say one cell shows an Excel error, and a check on that column should fail that row.
2. **Dates.** A column of real dates formatted `yyyy-mm-dd`: the preview should show
   dates, not numbers like 46023. Repeat in a workbook using the 1904 date system
   and choose **1904** in the pane: both fixtures must display the same intended
   date. Clear the selector and confirm that the live source cannot run.
3. **Percentages.** A weight cell showing `40%` should read as 0.4 in the preview.
4. **The policy sheet.** After **Save these checks in the workbook**, open the
   `finassert policy` sheet. Lines should show as plain text with their leading spaces,
   no stray apostrophes, nothing converted to a number or date. Edit one line (for
   example change a tolerance), press **Load the checks saved in the workbook**, and
   confirm the change appears in the pane.
5. **Text that looks like a formula.** Name a policy `=1+1`, save it to the workbook,
   and check the sheet shows the text, not `2`, then load it back.
6. **Tables.** Insert a table (Insert › Table), choose it in the workbook table picker,
   press **Use this table** and confirm the exact header/body bounds and totals
   exclusion. A single selected cell must request an explicit table/larger range.
7. **Results sheet.** After a run, **Write results to a sheet**: the stamp at the top
   should be readable, the Row column should match the rows you see in Excel, and your
   data sheet should be untouched.
8. **Offline.** Build with `--bundle-pyodide download` (about 14 MB more), serve it, run the
   diagnostics again, and confirm network use lists only your own origin and
   `appsforoffice.microsoft.com`.

## What to send back

Per platform and route: the diagnostics report, plus one line per manual check
(pass, or what you saw), plus the Excel version and platform. From that I will:

- fix what failed, and add what the real Excel showed to the stand-in so CI would have
  caught it;
- record supported platforms, minimum API set, and measured start-up and read times in
  [the add-in page](../excel-add-in.md), replacing "not yet run in real Excel";
- decide, per platform, whether the in-pane engine is viable or the thin-service
  fallback is needed.

## What the diagnostics cannot tell you

Whether a person finds the pane pleasant to use, how Excel behaves with very large or
protected workbooks, whether a corporate proxy or endpoint-security tool blocks the
engine, and AppSource certification. Note anything that felt wrong.
