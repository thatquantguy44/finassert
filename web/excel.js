/* finassert Excel add-in: reads the selected cells (or the table they are in), writes
 * results to a new sheet, and saves or loads the checks on a sheet. It never changes the
 * cells it reads. All checking happens in the application. */
"use strict";

(function () {
  const RESULTS_SHEET = "finassert results";
  const POLICY_SHEET = "finassert policy";
  const BLOCK_ROWS = 5000; // rows read per request, to stay inside Office's payload limits

  const $ = (id) => document.getElementById(id);
  const app = () => window.finassertApp;

  function say(text, isError) {
    if (app()) app().setStatus(text, isError);
  }

  // Excel's own address, such as "Sheet1!A4:F20", without the workbook path.
  function describe(address) {
    return address.replace(/^'?\[.*?\]/, "").replace(/^'|'(?=!)/g, "");
  }

  const LOAD = ["rowCount", "columnCount", "rowIndex", "address"];

  // The cells to read: what is selected; for a single cell, the table it is in, else
  // everything on the sheet.
  async function chooseRange(context, sheet) {
    let range = context.workbook.getSelectedRange();
    range.load(LOAD);
    await context.sync();
    let what = "the selected cells";
    if (range.rowCount * range.columnCount === 1) {
      const selected = range;
      range = null;
      sheet.tables.load("items/name");
      await context.sync();
      for (const table of sheet.tables.items) {
        const tableRange = table.getRange();
        const hit = selected.getIntersectionOrNullObject(tableRange);
        await context.sync();
        if (!hit.isNullObject) {
          range = tableRange;
          what = `the table "${table.name}"`;
          break;
        }
      }
      if (!range) {
        range = sheet.getUsedRange(true);
        what = "everything on the sheet";
      }
      range.load(LOAD);
      await context.sync();
    }
    return { range, what };
  }

  // Reads a range in blocks of rows, with the formats and types Excel reports.
  async function readRange(context, range) {
    const values = [];
    const numberFormats = [];
    const valueTypes = [];
    for (let start = 0; start < range.rowCount; start += BLOCK_ROWS) {
      const rows = Math.min(BLOCK_ROWS, range.rowCount - start);
      const block = range.getRow(start).getResizedRange(rows - 1, 0);
      block.load(["values", "numberFormat", "valueTypes"]);
      await context.sync();
      values.push(...block.values);
      numberFormats.push(...block.numberFormat);
      valueTypes.push(...block.valueTypes);
    }
    return { values, numberFormats, valueTypes, firstRow: range.rowIndex + 1 };
  }

  async function readSelection() {
    return Excel.run(async (context) => {
      const sheet = context.workbook.worksheets.getActiveWorksheet();
      const { range, what } = await chooseRange(context, sheet);
      return { name: describe(range.address), what, payload: await readRange(context, range) };
    });
  }

  // A sheet that finassert owns: created if missing, emptied if it already exists.
  async function freshSheet(context, name) {
    let sheet = context.workbook.worksheets.getItemOrNullObject(name);
    await context.sync();
    if (sheet.isNullObject) {
      sheet = context.workbook.worksheets.add(name);
    } else {
      const used = sheet.getUsedRangeOrNullObject();
      await context.sync();
      if (!used.isNullObject) used.clear();
    }
    return sheet;
  }

  async function writeResults(sheetData) {
    await Excel.run(async (context) => {
      const sheet = await freshSheet(context, RESULTS_SHEET);
      const { rows, boldRows } = sheetData;
      const width = rows[0].length;
      sheet.getRangeByIndexes(0, 0, rows.length, width).values = rows;
      for (const row of boldRows) sheet.getRangeByIndexes(row, 0, 1, width).format.font.bold = true;
      sheet.getUsedRange().format.autofitColumns();
      sheet.activate();
      await context.sync();
    });
  }

  async function savePolicy() {
    if (!app().hasChecks()) {
      say("Add or open some checks first.", true);
      return;
    }
    const yaml = app().policyYaml();
    if (yaml === null) return;
    const rows = app().policySheet(yaml);
    await Excel.run(async (context) => {
      const sheet = await freshSheet(context, POLICY_SHEET);
      const column = sheet.getRangeByIndexes(0, 0, rows.length, 1);
      column.numberFormat = rows.map(() => ["@"]); // text, so nothing is converted or calculated
      column.values = rows;
      sheet.getRangeByIndexes(0, 0, 1, 1).format.font.bold = true;
      sheet.getUsedRange().format.autofitColumns();
      await context.sync();
    });
    say(`Saved the checks on the sheet "${POLICY_SHEET}". Your data was not changed.`);
  }

  async function loadPolicy() {
    const values = await Excel.run(async (context) => {
      const sheet = context.workbook.worksheets.getItemOrNullObject(POLICY_SHEET);
      await context.sync();
      if (sheet.isNullObject) return null;
      const used = sheet.getUsedRange(true);
      used.load("values");
      await context.sync();
      return used.values;
    });
    if (values === null) {
      say(`This workbook has no sheet named "${POLICY_SHEET}".`, true);
      return;
    }
    const text = app().policyFromSheet(values);
    if (!text.ok) {
      say(text.error, true);
      return;
    }
    app().openPolicyText(text.text, "finassert-policy.yml", `the checks saved in this workbook`);
  }

  async function useSelection() {
    if (!app() || !app().ready()) {
      say("The checking engine is still loading. Try again in a moment.", true);
      return;
    }
    say("Reading the cells…");
    const selection = await readSelection();
    app().useData(selection.name, JSON.stringify(selection.payload), "excel-range");
    say(`Read ${selection.what} (${selection.name}).`);
  }

  async function writeToSheet() {
    if (!app() || !app().result()) return;
    await writeResults(app().resultsSheet());
    say(`Results written to the sheet "${RESULTS_SHEET}". Your data was not changed.`);
  }

  function guarded(action) {
    return async () => {
      try {
        await action();
      } catch (error) {
        say("Excel could not be read or written: " + (error && error.message ? error.message : error), true);
      }
    };
  }

  /* ---------- diagnostics for testers ---------- */

  const SPIKE_SHEET = "finassert spike data";
  const POSITIONS = 50; // positions per test portfolio
  const EXPECTED_ORIGINS = [location.origin, "https://appsforoffice.microsoft.com", "https://cdn.jsdelivr.net"];
  const violations = [];
  document.addEventListener("securitypolicyviolation", (event) =>
    violations.push(`${event.violatedDirective} blocked ${event.blockedURI}`));

  // A deterministic book: every portfolio has 50 positions of 2% (exactly 100%), market
  // values that add up to its NAV, and unique tickers. The first position of the first
  // three portfolios is 3% / 30,000, so exactly three portfolios break both checks.
  function testRows(portfolios) {
    const rows = [["portfolio", "ticker", "weight", "market_value", "nav"]];
    for (let p = 1; p <= portfolios; p++) {
      for (let i = 1; i <= POSITIONS; i++) {
        rows.push([`P${String(p).padStart(4, "0")}`, `T${String(i).padStart(3, "0")}`, 0.02, 20000, 1000000]);
      }
    }
    for (const p of [0, 1, 2]) {
      rows[1 + p * POSITIONS][2] = 0.03;
      rows[1 + p * POSITIONS][3] = 30000;
    }
    return rows;
  }

  async function writeTestData(rows) {
    await Excel.run(async (context) => {
      const sheet = await freshSheet(context, SPIKE_SHEET);
      for (let start = 0; start < rows.length; start += BLOCK_ROWS) {
        const block = rows.slice(start, start + BLOCK_ROWS);
        sheet.getRangeByIndexes(start, 0, block.length, block[0].length).values = block;
        await context.sync();
      }
    });
  }

  async function readTestData() {
    return Excel.run(async (context) => {
      const sheet = context.workbook.worksheets.getItem(SPIKE_SHEET);
      const range = sheet.getUsedRange(true);
      range.load(LOAD);
      await context.sync();
      return { name: describe(range.address), payload: await readRange(context, range) };
    });
  }

  function environment() {
    const info = {};
    try {
      const d = Office.context.diagnostics || {};
      Object.assign(info, { host: d.host, platform: d.platform, version: d.version });
    } catch (error) { info.diagnostics = String(error); }
    info.contextPlatform = Office.context.platform;
    info.userAgent = navigator.userAgent;
    info.sets = {};
    for (const v of ["1.1", "1.2", "1.3", "1.4", "1.5", "1.7", "1.9"]) {
      try { info.sets[v] = Office.context.requirements.isSetSupported("ExcelApi", v); } catch (error) { info.sets[v] = null; }
    }
    return info;
  }

  async function runSpike(portfolios, how) {
    const steps = [];
    const run = async (name, work) => {
      const started = performance.now();
      try {
        const outcome = await work();
        steps.push({ name, status: outcome.ok ? "PASS" : "FAIL", detail: outcome.detail,
          ms: Math.round(performance.now() - started) });
        return outcome;
      } catch (error) {
        steps.push({ name, status: "FAIL", detail: String(error && error.message ? error.message : error),
          ms: Math.round(performance.now() - started) });
        return null;
      }
    };
    const info = environment();
    const startedAt = Math.round(performance.now());
    const requestsBefore = performance.getEntriesByType("resource");
    steps.push({ name: "environment", status: "INFO", ms: 0,
      detail: `${info.host || "?"} on ${info.platform || info.contextPlatform || "?"}, version ${info.version || "?"}; loaded via: ${how}` });
    await run("Excel API support", async () => {
      const missing = Object.entries(info.sets).filter(([, ok]) => !ok).map(([v]) => v);
      return { ok: info.sets["1.4"] === true, detail: `ExcelApi sets supported: ${Object.entries(info.sets).filter(([, ok]) => ok).map(([v]) => v).join(", ") || "none"}` +
        (missing.length ? `; not supported: ${missing.join(", ")}` : "") + " (the add-in needs 1.4)" };
    });
    await run("engine start-up", async () => {
      const ms = app().readyMs();
      const heap = performance.memory ? ` JS heap ${Math.round(performance.memory.usedJSHeapSize / 1048576)} MB.` : " Memory is not reported here.";
      return { ok: typeof ms === "number" && ms < 120000, detail: `ready ${ms} ms after the page started (limit 120 s).${heap}` };
    });
    await run("security policy", async () => ({
      ok: violations.length === 0,
      detail: violations.length ? `${violations.length} violation(s): ${violations.slice(0, 5).join("; ")}` : "no content-security-policy violations",
    }));
    await run("network use", async () => {
      const entries = requestsBefore.map((r) => ({ url: r.name, at: Math.round(r.startTime) }));
      const origins = [...new Set(entries.map((r) => new URL(r.url).origin))];
      const unexpected = origins.filter((o) => !EXPECTED_ORIGINS.includes(o));
      const late = entries.filter((r) => r.at > app().readyMs() + 1000);
      return { ok: unexpected.length === 0 && late.length === 0,
        detail: `${entries.length} request(s) to ${origins.join(", ") || "nowhere"}` +
          (unexpected.length ? `; UNEXPECTED origins: ${unexpected.join(", ")}` : "") +
          (late.length ? `; ${late.length} request(s) after the engine was ready` : "; none after the engine was ready") };
    });

    const rows = testRows(portfolios);
    const wrote = await run(`write ${(rows.length - 1).toLocaleString()} test rows`, async () => {
      await writeTestData(rows);
      return { ok: true, detail: `sheet "${SPIKE_SHEET}" created` };
    });
    let read = null;
    if (wrote) {
      read = await run("read the rows back", async () => {
        const data = await readTestData();
        const got = data.payload.values.length - 1;
        app().useData(data.name, JSON.stringify(data.payload), "excel-range");
        return { ok: got === rows.length - 1, detail: `${got.toLocaleString()} rows read from ${data.name}`, data };
      });
    }
    let result = null;
    if (read) {
      await run("run the multi-portfolio template", async () => {
        result = app().runTemplate("multi-portfolio-holdings");
        const report = JSON.parse(result.artifact_json).report.results;
        const failed = (id) => (report.find((r) => r.rule_id === id).metadata.failed_group_count);
        const weights = failed("portfolio.weights_sum_to_one");
        const nav = failed("accounting.nav_reconciles");
        const clean = report.filter((r) => r.rule_id.startsWith("data.")).every((r) => r.outcome === "passed");
        return { ok: weights === 3 && nav === 3 && clean,
          detail: `weights failed in ${weights} portfolio(s) (expected 3), NAV in ${nav} (expected 3); data checks ${clean ? "passed" : "FAILED"}` };
      });
    }
    if (result) {
      await run("write the results sheet", async () => {
        const sheetData = app().resultsSheet();
        await writeResults(sheetData);
        return { ok: sheetData.rows.length > 10, detail: `${sheetData.rows.length} row(s) written to "${RESULTS_SHEET}"` };
      });
      await run("save and load the checks", async () => {
        const before = app().policyYaml();
        await savePolicy();
        await loadPolicy();
        const after = app().policyYaml();
        return { ok: before !== null && before === after, detail: before === after ? "the checks round-tripped unchanged" : "the loaded checks differ from the saved ones" };
      });
      await run("your data was not changed", async () => {
        const again = await readTestData();
        const same = JSON.stringify(again.payload.values) === JSON.stringify(read.data.payload.values);
        return { ok: same, detail: same ? "the test rows read back identical after every step" : "the rows changed" };
      });
    }
    const failures = steps.filter((step) => step.status === "FAIL").length;
    const lines = steps.map((step) => `${step.status.padEnd(4)}  ${step.name}${step.ms ? ` (${step.ms} ms)` : ""}: ${step.detail}`);
    lines.push("", failures ? `${failures} step(s) FAILED` : "All steps passed", "",
      JSON.stringify({ finassert: app().version || null, steps: steps.map(({ name, status, ms }) => ({ name, status, ms })), environment: info, startedAt }));
    return lines.join("\n");
  }

  async function spike() {
    const portfolios = Math.max(10, Math.min(2000, Number($("spike-portfolios").value) || 1000));
    const box = $("spike-report");
    box.value = "Running… this creates the sheet \"" + SPIKE_SHEET + "\" and can take a minute.";
    say("Running the diagnostics…");
    box.value = await runSpike(portfolios, $("spike-how").value);
    say("Diagnostics finished. Copy the report from the panel.");
  }

  async function copyReport() {
    const box = $("spike-report");
    try {
      await navigator.clipboard.writeText(box.value);
    } catch (error) {
      box.select();
      document.execCommand("copy");
    }
    say("Report copied.");
  }
  async function start() {
    if (typeof Office === "undefined" || !Office.onReady) return;
    const info = await Office.onReady();
    if (info.host !== Office.HostType.Excel) return;
    $("excel-panel").hidden = false;
    for (const id of ["excel-write", "excel-save-policy", "excel-load-policy"]) $(id).hidden = false;
    $("excel-read").addEventListener("click", guarded(useSelection));
    $("excel-write").addEventListener("click", guarded(writeToSheet));
    $("excel-save-policy").addEventListener("click", guarded(savePolicy));
    $("excel-load-policy").addEventListener("click", guarded(loadPolicy));
    $("spike-run").addEventListener("click", guarded(spike));
    $("spike-copy").addEventListener("click", guarded(copyReport));
  }

  start();
})();
