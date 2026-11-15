/* A stand-in for the parts of Office.js the add-in uses (smoke_excel.py). It models a
 * workbook of sheets of cells, so what the add-in writes can be read back and checked. */
(function () {
  const config = __CONFIG__;
  const sheets = {};
  const state = { selected: config.selected, sheets: {}, log: [], reads: [], handlers: [], selection: config.selection,
    formulas: config.formulas || {}, numberFormats: config.numberFormats || [], activeRuns: 0, maxActiveRuns: 0 };
  window.__excel = state;
  const supports = (version) => (config.requirements || {})[version] !== false;
  const eventMember = (version, sheet, event, tableId) => supports(version) ? { add(callback) {
    const handler = { callback, sheet, event, tableId, removed: false };
    state.handlers.push(handler);
    return { context: {}, remove() { handler.removed = true; } };
  } } : undefined;
  state.emit = (event, args, sheet = config.sheetName || "Holdings", tableId) => state.handlers
    .filter((h) => !h.removed && h.sheet === sheet && h.event === event && h.tableId === tableId)
    .forEach((h) => h.callback(args));
  state.change = (changeType, sheet = config.sheetName || "Holdings", address = "A3:E5") =>
    state.emit("changed", { changeType, address }, sheet);
  state.recalculate = () => state.emit("calculated", {});
  state.formatChanged = (address = "A3:E5") => state.emit("format", { address });
  state.tableChanged = (id = "table-1") => state.emit("table", {}, config.sheetName || "Holdings", id);
  const application = {
    calculationMode: config.calculationMode || "Automatic",
    calculationState: config.calculationState || "Done",
    load() { state.log.push("read calculation metadata"); },
  };
  state.application = application;

  const letters = (index) => {
    let text = "";
    for (let n = index + 1; n > 0; n = Math.floor((n - 1) / 26)) text = String.fromCharCode(65 + ((n - 1) % 26)) + text;
    return text;
  };
  const kind = (v) => (v === "" || v == null ? "Empty" : typeof v === "number" ? "Double"
    : String(v).startsWith("#") ? "Error" : "String");

  function makeSheet(name, cells) {
    const sheet = { id: `sheet-${name}-${Object.keys(sheets).length}`, name,
      cells: cells.map((row) => row.slice()), formats: {}, bold: [], tables: [] };
    sheets[name] = sheet;
    state.sheets[name] = sheet;
    return sheet;
  }
  const holdings = makeSheet(config.sheetName || "Holdings", []);
  // The data sits in A3:E7, with two empty rows above it.
  const top = config.rowIndex == null ? 2 : config.rowIndex, left = config.columnIndex || 0;
  const width = config.values[0].length;
  holdings.cells = Array.from({ length: top }, () => []).concat(config.values.map((r) => Array(left).fill("").concat(r)));
  holdings.tables = config.table ? [{ id: "table-1", name: "HoldingsTable", r0: top, c0: left,
    rows: config.values.length, cols: width, totals: config.totals || false }] : [];
  state.recreateSheet = () => { holdings.id = "replacement-sheet"; };

  function used(sheet) {
    let rows = 0, cols = 0, top = Infinity, left = Infinity;
    sheet.cells.forEach((row, r) => row.forEach((v, c) => {
      if (v !== "" && v != null) { rows = Math.max(rows, r + 1); cols = Math.max(cols, c + 1); top = Math.min(top, r); left = Math.min(left, c); }
    }));
    return rows ? { r0: top, c0: left, rows: rows - top, cols: cols - left } : null;
  }

  function range(sheet, r0, c0, rows, cols) {
    const r = { rowIndex: r0, columnIndex: c0, rowCount: rows, columnCount: cols };
    Object.defineProperty(r, "worksheet", { get: () => sheetApi(sheet) });
    const sheetAddress = /[^A-Za-z0-9_]/.test(sheet.name) ? `'${sheet.name.replace(/'/g, "''")}'` : sheet.name;
    r.address = `${sheetAddress}!${letters(c0)}${r0 + 1}` + (rows * cols > 1 ? `:${letters(c0 + cols - 1)}${r0 + rows}` : "");
    const read = () => Array.from({ length: rows }, (_, i) =>
      Array.from({ length: cols }, (_, j) => { const v = (sheet.cells[r0 + i] || [])[c0 + j]; return v == null ? "" : v; }));
    r.load = (properties) => {
      if (String(properties).includes("values")) {
        state.reads.push({ r0, c0, rows, cols });
        if (state.failReadAt === state.reads.length) throw new Error("synthetic payload limit");
        r.values = read();
        r.numberFormat = r.values.map((row, i) => row.map((_, j) =>
          (state.numberFormats[r0 + i - top] || [])[c0 + j - left] || "General"));
        r.valueTypes = r.values.map((row) => row.map(kind));
        r.formulas = r.values.map((row, i) => row.map((v, j) => state.formulas[`${r0 + i},${c0 + j}`] ?? v));
        if (state.onRead) state.onRead({ r0, c0, rows, cols, number: state.reads.length });
        if (state.pauseReadAt === state.reads.length) state.pauseNextSync = true;
      }
    };
    r.getMergedAreasOrNullObject = () => ({ isNullObject: !config.mergedHeader });
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

  const tableApi = (sheet, t) => ({
    id: t.id, name: t.name, worksheet: sheetApi(sheet), load() {},
    rows: { count: t.rows - 1 - (t.totals ? 1 : 0), load() {} },
    getRange: () => range(sheet, t.r0, t.c0, t.rows, t.cols),
    getHeaderRowRange: () => range(sheet, t.r0, t.c0, 1, t.cols),
    getDataBodyRange: () => range(sheet, t.r0 + 1, t.c0, t.rows - 1 - (t.totals ? 1 : 0), t.cols),
    onChanged: eventMember("1.7", sheet.name, "table", t.id),
  });
  const sheetApi = (sheet) => ({
    id: sheet.id,
    name: sheet.name,
    load() {},
    onChanged: eventMember("1.7", sheet.name, "changed"),
    onCalculated: eventMember("1.8", sheet.name, "calculated"),
    onFormatChanged: eventMember("1.9", sheet.name, "format"),
    tables: {
      get items() { return sheet.tables.map((t) => tableApi(sheet, t)); },
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

  window.Office = {
    HostType: { Excel: "Excel" },
    onReady: () => Promise.resolve({ host: "Excel" }),
    context: {
      platform: "PC",
      diagnostics: { host: "Excel", platform: "PC", version: "16.0.stub" },
      requirements: { isSetSupported: (_name, version) => supports(version) },
    },
  };
  window.Excel = {
    run: async (contextOrCallback, callback) => {
      callback = callback || contextOrCallback;
      state.activeRuns++;
      state.maxActiveRuns = Math.max(state.maxActiveRuns, state.activeRuns);
      const context = {
        sync: async () => {
          if (state.pauseNextSync) {
            state.pauseNextSync = false;
            state.paused = true;
            await new Promise((resolve) => { state.resume = () => { state.paused = false; resolve(); }; });
          }
          if (state.onSync) state.onSync();
        },
        application,
        workbook: {
          getSelectedRange: () => {
            if (state.selected === "disjoint") throw new Error("InvalidSelection");
            if (state.selection) { const s = state.selection; return range(holdings, s.r0, s.c0, s.rows, s.cols); }
            if (state.selected === "single") return range(holdings, 3, 1, 1, 1); // B4
            return range(holdings, top, left, config.values.length, width);
          },
          tables: {
            get items() { return Object.values(sheets).flatMap((s) => s.tables.map((t) => tableApi(s, t))); },
            load() {},
            getItem: (id) => {
              for (const s of Object.values(sheets)) {
                const t = s.tables.find((t) => t.id === id);
                if (t) return tableApi(s, t);
              }
              throw new Error("The bound table no longer exists; choose the source again.");
            },
          },
          worksheets: {
            getActiveWorksheet: () => sheetApi(holdings),
            getItem: (name) => {
              const found = Object.values(sheets).find((s) => s.name === name || s.id === name);
              if (!found) throw new Error("The bound worksheet no longer exists; reselect the source.");
              return sheetApi(found);
            },
            getItemOrNullObject: (name) => (sheets[name] ? Object.assign(sheetApi(sheets[name]), { isNullObject: false }) : { isNullObject: true }),
            add: (name) => sheetApi(makeSheet(name, [])),
          },
        },
      };
      try { return await callback(context); }
      finally { state.activeRuns--; }
    },
  };
})();
