/* Private workbook output lifecycle. Ownership is scoped to this add-in and saved
 * with the workbook; names never confer permission to replace a worksheet. */
"use strict";
(function () {
  const PREFIX = "finassert.output.v1.";
  const base = (role) => role === "results" ? "finassert results" : "finassert policy";
  const valid = (value, id) => value && value.schema_version === 1 && value.worksheet_id === id &&
    ["results", "policy"].includes(value.role) && ["complete", "incomplete"].includes(value.state) &&
    typeof value.operation === "string" && value.operation.length > 0;

  async function inventory(context, sync) {
    const sheets = context.workbook.worksheets;
    sheets.load("items/id,items/name");
    await sync(context);
    const settings = context.workbook.settings;
    if (!settings) throw new Error("Workbook settings are unavailable. Update Excel before writing output.");
    const entries = sheets.items.map((sheet) => {
      const setting = settings.getItemOrNullObject(PREFIX + sheet.id);
      setting.load("value");
      return { sheet, setting };
    });
    await sync(context);
    return entries.map(({ sheet, setting }) => ({ id: sheet.id, name: sheet.name,
      owner: !setting.isNullObject && valid(setting.value, sheet.id) ? setting.value : null }));
  }

  async function list(sync = (context) => context.sync()) {
    return Excel.run((context) => inventory(context, sync));
  }

  function stage(data) {
    const { rows, boldRows } = data;
    const width = rows?.[0]?.length;
    if (!width || rows.length > 1048576 || width > 16384 || rows.length * width > 5000000 ||
        rows.some((row) => row.length !== width || row.some((cell) =>
          !["string", "number", "boolean"].includes(typeof cell) ||
          (typeof cell === "number" && !Number.isFinite(cell)) ||
          (typeof cell === "string" && cell.length > 32767))) ||
        boldRows.some((row) => !Number.isInteger(row) || row < 0 || row >= rows.length)) {
      throw new Error("Output exceeds Excel's cell/row limits or is malformed. Download JSON/HTML instead.");
    }
    return { rows: rows.map((row) => row.slice()), boldRows: boldRows.slice(), width };
  }

  function literalValues(rows) {
    // Range.values consumes a leading apostrophe, even with text formatting.
    // Preserve staged literal quotes and the Python formatter's safety prefixes.
    return rows.map((row) => row.map((cell) => typeof cell === "string" && cell.startsWith("'") ? "'" + cell : cell));
  }

  async function write(data, role, options = {}) {
    if (!["results", "policy"].includes(role)) throw new Error("Choose a valid output role.");
    const prepared = stage(data); // All rendering and bounds checks precede mutations.
    const sync = options.sync || ((context) => context.sync());
    const check = options.check || (() => {});
    const isSource = options.isSource || (() => false);
    const operation = [...crypto.getRandomValues(new Uint32Array(4))].map((n) => n.toString(16)).join("-");
    let destination = null;
    let touched = false;
    try {
      await Excel.run(async (context) => {
        const entries = await inventory(context, sync);
        check();
        let sheet;
        if (options.replaceId) {
          const entry = entries.find((item) => item.id === options.replaceId);
          if (!entry || !entry.owner || entry.owner.role !== role || role !== "results" || entry.owner.state !== "complete") {
            throw new Error("The selected destination is not a completed owned results sheet. Refresh the list or create a new sheet.");
          }
          if (isSource(entry.id)) throw new Error("Output cannot replace the bound source worksheet.");
          sheet = context.workbook.worksheets.getItem(entry.id);
        } else {
          const names = new Set(entries.map((entry) => entry.name.toLowerCase()));
          let name = base(role), suffix = 2;
          while (names.has(name.toLowerCase())) {
            if (suffix > 100000) throw new Error("Too many output names. Rename an unused output sheet and retry.");
            name = `${base(role)} (${suffix++})`;
          }
          sheet = context.workbook.worksheets.add(name);
        }
        sheet.load(["id", "name"]);
        await sync(context);
        destination = { id: sheet.id, name: sheet.name };
        if (isSource(sheet.id)) throw new Error("Output cannot write to the bound source worksheet.");
        const ownership = { schema_version: 1, worksheet_id: sheet.id, role, state: "incomplete", operation };
        context.workbook.settings.add(PREFIX + sheet.id, ownership);
        await sync(context);
        // Replacement is explicit and authorized by the saved ID, never its name.
        touched = true;
        if (options.replaceId) {
          const used = sheet.getUsedRangeOrNullObject();
          await sync(context);
          if (!used.isNullObject) used.clear();
        }
        const marker = sheet.getRangeByIndexes(0, 0, 1, prepared.width);
        marker.numberFormat = [Array(prepared.width).fill("@")];
        marker.values = [["INCOMPLETE finassert export — do not use as completed evidence", ...Array(prepared.width - 1).fill("")]];
        await sync(context);
        const chunk = Math.max(1, Math.min(5000, Math.floor(50000 / prepared.width)));
        for (let start = 1; start < prepared.rows.length; start += chunk) {
          check();
          if (isSource(sheet.id)) throw new Error("Output became a bound source. Write stopped.");
          const block = prepared.rows.slice(start, start + chunk);
          const cells = sheet.getRangeByIndexes(start, 0, block.length, prepared.width);
          cells.numberFormat = block.map((row) => row.map(() => "@"));
          cells.values = literalValues(block);
          await sync(context);
        }
        for (const row of prepared.boldRows) sheet.getRangeByIndexes(row, 0, 1, prepared.width).format.font.bold = true;
        sheet.getUsedRange().format.autofitColumns();
        await sync(context);
        const claim = context.workbook.settings.getItemOrNullObject(PREFIX + sheet.id);
        claim.load("value");
        await sync(context);
        if (claim.isNullObject || !valid(claim.value, sheet.id) || claim.value.role !== role ||
            claim.value.state !== "incomplete" || claim.value.operation !== operation || isSource(sheet.id)) {
          throw new Error("Output ownership changed during writing. Completion was refused.");
        }
        marker.values = literalValues([prepared.rows[0]]);
        context.workbook.settings.add(PREFIX + sheet.id, { ...ownership, state: "complete" });
        if (role === "results") sheet.activate();
        await sync(context);
      });
      return destination;
    } catch (error) {
      // Best effort quarantine; never delete a partial sheet or write after close.
      if (destination && touched && !isSource(destination.id) && (!options.canRecover || options.canRecover())) {
        try {
          await Excel.run(async (context) => {
            const claim = context.workbook.settings.getItemOrNullObject(PREFIX + destination.id);
            claim.load("value");
            await context.sync();
            if (claim.isNullObject || claim.value.operation !== operation || isSource(destination.id) ||
                (options.canRecover && !options.canRecover())) return;
            const sheet = context.workbook.worksheets.getItem(destination.id);
            sheet.getRangeByIndexes(0, 0, 1, 1).values = [["INCOMPLETE finassert export — do not use as completed evidence"]];
            context.workbook.settings.add(PREFIX + destination.id, { ...claim.value, state: "incomplete" });
            await context.sync();
          });
        } catch (_) { /* Host may still be protected/unavailable; report uncertainty. */ }
      }
      throw new Error(`Export failed${destination ? ` on "${destination.name}"` : ""}: ${error.message || error}. ` +
        (destination ? "A partial sheet may remain; do not use it as completed evidence. Correct the cause and create a new sheet." : "No completed output was created."));
    }
  }

  window.finassertOutput = Object.freeze({ list, write });
})();
