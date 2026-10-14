/* A stand-in for the parts of Office.js the add-in uses (smoke_excel.py). It models a
 * workbook of sheets of cells, so what the add-in writes can be read back and checked. */
(function () {
  const config = __CONFIG__;
  const sheets = {};
  const state = { selected: config.selected, sheets: {}, log: [] };
  window.__excel = state;

  const letters = (index) => {
    let text = "";
    for (let n = index + 1; n > 0; n = Math.floor((n - 1) / 26)) text = String.fromCharCode(65 + ((n - 1) % 26)) + text;
    return text;
  };
  const kind = (v) => (v === "" || v == null ? "Empty" : typeof v === "number" ? "Double"
    : String(v).startsWith("#") ? "Error" : "String");

  function makeSheet(name, cells) {
    const sheet = { name, cells: cells.map((row) => row.slice()), formats: {}, bold: [], tables: [] };
    sheets[name] = sheet;
    state.sheets[name] = sheet;
    return sheet;
  }
  const holdings = makeSheet("Holdings", []);
  // The data sits in A3:E7, with two empty rows above it.
  holdings.cells = [[], [], ...config.values];
  holdings.tables = config.table ? [{ name: "HoldingsTable", r0: 2, c0: 0, rows: config.values.length, cols: 5 }] : [];

  function used(sheet) {
    let rows = 0, cols = 0, top = Infinity, left = Infinity;
    sheet.cells.forEach((row, r) => row.forEach((v, c) => {
      if (v !== "" && v != null) { rows = Math.max(rows, r + 1); cols = Math.max(cols, c + 1); top = Math.min(top, r); left = Math.min(left, c); }
    }));
    return rows ? { r0: top, c0: left, rows: rows - top, cols: cols - left } : null;
  }

  function range(sheet, r0, c0, rows, cols) {
    const r = { rowIndex: r0, columnIndex: c0, rowCount: rows, columnCount: cols };
    r.address = `${sheet.name}!${letters(c0)}${r0 + 1}` + (rows * cols > 1 ? `:${letters(c0 + cols - 1)}${r0 + rows}` : "");
    const read = () => Array.from({ length: rows }, (_, i) =>
      Array.from({ length: cols }, (_, j) => { const v = (sheet.cells[r0 + i] || [])[c0 + j]; return v == null ? "" : v; }));
    r.load = () => {
      r.values = read();
      r.numberFormat = r.values.map((row) => row.map(() => "General"));
      r.valueTypes = r.values.map((row) => row.map(kind));
    };
    r.getRow = (i) => range(sheet, r0 + i, c0, 1, cols);
    r.getResizedRange = (dr, dc) => range(sheet, r0, c0, rows + dr, cols + (dc || 0));
    r.getIntersectionOrNullObject = (other) => {
      const top = Math.max(r0, other.rowIndex), bottom = Math.min(r0 + rows, other.rowIndex + other.rowCount);
      const left = Math.max(c0, other.columnIndex), right = Math.min(c0 + cols, other.columnIndex + other.columnCount);
      return top < bottom && left < right ? range(sheet, top, left, bottom - top, right - left) : { isNullObject: true };
    };
    Object.defineProperty(r, "values", { configurable: true, writable: true, value: undefined });
    r.format = { font: {}, autofitColumns() {} };
    Object.defineProperty(r.format.font, "bold", { set(v) { sheet.bold.push(r0); } });
    r.clear = () => { sheet.cells = []; };
    return new Proxy(r, {
      set(target, prop, value) {
        if (prop === "values" && !target.__loading) {
          value.forEach((row, i) => { sheet.cells[r0 + i] = sheet.cells[r0 + i] || []; row.forEach((v, j) => { sheet.cells[r0 + i][c0 + j] = v; }); });
          return true;
        }
        if (prop === "numberFormat") { sheet.formats[`${r0},${c0}`] = value; return true; }
        target[prop] = value;
        return true;
      },
    });
  }

  const sheetApi = (sheet) => ({
    name: sheet.name,
    tables: {
      items: sheet.tables.map((t) => ({ name: t.name, getRange: () => range(sheet, t.r0, t.c0, t.rows, t.cols) })),
      load() {},
    },
    getUsedRange: () => { const u = used(sheet); return range(sheet, u.r0, u.c0, u.rows, u.cols); },
    getUsedRangeOrNullObject: () => {
      const u = used(sheet);
      if (!u) return { isNullObject: true };
      const r = range(sheet, u.r0, u.c0, u.rows, u.cols);
      r.isNullObject = false;
      return r;
    },
    getRangeByIndexes: (r0, c0, rows, cols) => range(sheet, r0, c0, rows, cols),
    activate() { state.active = sheet.name; },
  });

  window.Office = { HostType: { Excel: "Excel" }, onReady: () => Promise.resolve({ host: "Excel" }) };
  window.Excel = {
    run: async (callback) => {
      const context = {
        sync: async () => {},
        workbook: {
          getSelectedRange: () => {
            if (state.selected === "single") return range(holdings, 3, 1, 1, 1); // B4
            return range(holdings, 2, 0, config.values.length, 5); // A3:E7
          },
          worksheets: {
            getActiveWorksheet: () => sheetApi(holdings),
            getItemOrNullObject: (name) => (sheets[name] ? Object.assign(sheetApi(sheets[name]), { isNullObject: false }) : { isNullObject: true }),
            add: (name) => sheetApi(makeSheet(name, [])),
          },
        },
      };
      return callback(context);
    },
  };
})();
