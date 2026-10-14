/* A stand-in for the parts of Office.js the add-in uses (smoke_excel.py). */
(function () {
  const sheetData = __SHEET__;
  const state = { written: null, sheetName: null, selected: "__SELECTED__", log: [] };
  window.__excel = state;
  const kind = (v) => (v === "" ? "Empty" : typeof v === "number" ? "Double"
    : String(v).startsWith("#") ? "Error" : "String");
  const grid = sheetData.values;
  const width = grid[0].length;
  function range(row0, rows, address) {
    const r = { rowIndex: sheetData.rowIndex + row0, rowCount: rows, columnCount: width, address };
    r.getRow = (i) => range(row0 + i, 1, address);
    r.getResizedRange = (delta) => range(row0, rows + delta, address);
    r.load = () => {
      const slice = grid.slice(row0, row0 + rows);
      r.values = slice;
      r.numberFormat = slice.map((row) => row.map(() => "General"));
      r.valueTypes = slice.map((row) => row.map(kind));
    };
    return r;
  }
  const full = () => range(0, grid.length, "Holdings!A3:E7");
  window.Office = { HostType: { Excel: "Excel" }, onReady: () => Promise.resolve({ host: "Excel" }) };
  window.Excel = {
    run: async (callback) => {
      const context = {
        sync: async () => {},
        workbook: {
          getSelectedRange: () => {
            if (state.selected === "single") {
              const cell = range(1, 1, "Holdings!B4");
              cell.columnCount = 1;
              return cell;
            }
            return full();
          },
          worksheets: {
            getActiveWorksheet: () => ({ name: sheetData.name, getUsedRange: () => full() }),
            getItemOrNullObject: () => ({ isNullObject: true }),
            add: (name) => {
              state.sheetName = name;
              return {
                getRangeByIndexes: () => ({
                  set values(rows) { state.written = rows; },
                  format: { font: {} },
                }),
                getUsedRange: () => ({ format: { autofitColumns() {} } }),
                activate() {},
              };
            },
          },
        },
      };
      return callback(context);
    },
  };
})();
