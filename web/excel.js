/* finassert Excel add-in: reads the selected cells and writes results to a new sheet.
 * It never changes the cells it reads. All checking happens in the application. */
"use strict";

(function () {
  const RESULTS_SHEET = "finassert results";
  const BLOCK_ROWS = 5000; // rows read per request, to stay inside Office's payload limits

  const $ = (id) => document.getElementById(id);

  function say(text, isError) {
    if (window.finassertApp) window.finassertApp.setStatus(text, isError);
  }

  // Excel's own address, such as "Sheet1!A4:F20", without the workbook path.
  function describe(address) {
    return address.replace(/^'?\[.*?\]/, "").replace(/^'|'(?=!)/g, "");
  }

  async function readSelection() {
    return Excel.run(async (context) => {
      const sheet = context.workbook.worksheets.getActiveWorksheet();
      let range = context.workbook.getSelectedRange();
      range.load(["rowCount", "columnCount", "rowIndex", "address"]);
      await context.sync();
      if (range.rowCount * range.columnCount === 1) {
        range = sheet.getUsedRange(true);
        range.load(["rowCount", "columnCount", "rowIndex", "address"]);
        await context.sync();
      }
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
        payload: { values, numberFormats, valueTypes, firstRow: range.rowIndex + 1 },
      };
    });
  }

  async function writeResults(rows) {
    await Excel.run(async (context) => {
      let sheet = context.workbook.worksheets.getItemOrNullObject(RESULTS_SHEET);
      await context.sync();
      if (sheet.isNullObject) {
        sheet = context.workbook.worksheets.add(RESULTS_SHEET);
      } else {
        const used = sheet.getUsedRangeOrNullObject();
        await context.sync();
        if (!used.isNullObject) used.clear();
      }
      const width = rows[0].length;
      sheet.getRangeByIndexes(0, 0, rows.length, width).values = rows;
      sheet.getRangeByIndexes(0, 0, 1, width).format.font.bold = true;
      sheet.getUsedRange().format.autofitColumns();
      sheet.activate();
      await context.sync();
    });
  }

  async function useSelection() {
    const app = window.finassertApp;
    if (!app || !app.ready()) {
      say("The checking engine is still loading. Try again in a moment.", true);
      return;
    }
    say("Reading the selected cells…");
    const selection = await readSelection();
    app.useData(selection.name, JSON.stringify(selection.payload), "excel-range");
  }

  async function writeToSheet() {
    const app = window.finassertApp;
    if (!app || !app.result()) return;
    await writeResults(app.resultsSheet());
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
    $("excel-write").hidden = false;
    $("excel-read").addEventListener("click", guarded(useSelection));
    $("excel-write").addEventListener("click", guarded(writeToSheet));
  }

  start();
})();
