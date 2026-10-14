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

  async function readSelection() {
    return Excel.run(async (context) => {
      const sheet = context.workbook.worksheets.getActiveWorksheet();
      const { range, what } = await chooseRange(context, sheet);
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
      return {
        name: describe(range.address),
        what,
        payload: { values, numberFormats, valueTypes, firstRow: range.rowIndex + 1 },
      };
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
  }

  start();
})();
