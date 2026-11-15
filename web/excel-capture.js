/* Private, versioned Excel capture/configuration helpers. Financial checks stay in Python. */
"use strict";

(function () {
  const defaults = Object.freeze({
    monitoring: "events", capture: "verified", confirmations: 2,
    blockRows: 5000, blockCells: 50000, timeoutSeconds: 120,
  });

  function settings(raw) {
    const config = { ...defaults, ...raw };
    for (const [key, choices] of Object.entries({ monitoring: ["events", "on-demand"], capture: ["verified", "snapshot"] })) {
      if (!choices.includes(config[key])) throw new Error(`Choose a valid ${key} setting.`);
    }
    for (const [key, min, max] of [["confirmations", 2, 4], ["blockRows", 1, 5000],
      ["blockCells", 1000, 50000], ["timeoutSeconds", 1, 300]]) {
      if (!Number.isInteger(config[key]) || config[key] < min || config[key] > max) {
        throw new Error(`${key} must be a whole number from ${min} to ${max}.`);
      }
    }
    return Object.freeze(config);
  }

  function scalar(value) {
    if (value === null) return ["null"];
    if (typeof value === "string") return ["string", value];
    if (typeof value === "boolean") return ["boolean", value];
    if (typeof value === "number" && Number.isFinite(value)) {
      return ["number", Object.is(value, -0) ? "-0" : String(value)];
    }
    throw new Error("Excel returned an unsupported or non-finite cell value.");
  }

  function grid(rows, height, width) {
    if (!Array.isArray(rows) || rows.length !== height || rows.some((row) =>
      !Array.isArray(row) || row.length !== width)) throw new Error("Excel returned an incomplete cell grid.");
    return rows.map((row) => row.map(scalar));
  }

  // Array field order is normative. No locale conversion, sorting or Unicode normalization.
  function canonical(source, payload) {
    if (!["range", "table"].includes(source.kind) || typeof payload.date1904 !== "boolean" ||
        payload.firstRow !== source.header_row || source.rowIndex !== source.header_row - 1) {
      throw new Error("Capture identity, physical rows or date interpretation is incomplete.");
    }
    const height = source.data_row_count + 1, width = source.column_count;
    return JSON.stringify(["finassert.excel.snapshot", 1,
      [source.kind, source.worksheet_id, source.worksheet_name,
        source.table_id ?? null, source.table_name ?? null, source.address,
        source.header_row, source.rowIndex, source.columnIndex, source.data_row_count,
        source.column_count, "include_all", payload.date1904 ? "1904" : "1900", "user"],
      grid(payload.values, height, width), grid(payload.numberFormats, height, width),
      grid(payload.valueTypes, height, width)]);
  }

  async function sha256(text) {
    if (!globalThis.crypto || !crypto.subtle) throw new Error("Capture verification needs a secure HTTPS task pane.");
    const bytes = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
    return "sha256:" + [...new Uint8Array(bytes)].map((b) => b.toString(16).padStart(2, "0")).join("");
  }

  async function fingerprints(source, payload, formulas) {
    const [snapshot, formula] = await Promise.all([
      sha256(canonical(source, payload)),
      // Formula identity is private; the public snapshot digest still covers evaluated cells.
      sha256(JSON.stringify(["finassert.excel.formulas", 1,
        grid(formulas, source.data_row_count + 1, source.column_count)])),
    ]);
    return { snapshot, formula };
  }

  function overlaps(address, source) {
    if (!address || typeof address !== "string") return true; // unknown notification: invalidate conservatively
    const letters = (text) => [...text.toUpperCase()].reduce((n, c) => n * 26 + c.charCodeAt(0) - 64, 0) - 1;
    return address.split(",").some((part) => {
      const local = part.slice(part.lastIndexOf("!") + 1).replace(/\$/g, "");
      const match = /^([A-Z]+)(\d+)(?::([A-Z]+)(\d+))?$/i.exec(local);
      if (!match) return true;
      const left = letters(match[1]), top = Number(match[2]) - 1;
      const right = match[3] ? letters(match[3]) : left, bottom = match[4] ? Number(match[4]) - 1 : top;
      return left < source.columnIndex + source.column_count && right >= source.columnIndex &&
        top <= source.rowIndex + source.data_row_count && bottom >= source.rowIndex;
    });
  }

  window.finassertCapture = Object.freeze({ defaults, settings, canonical, fingerprints, overlaps });
})();
