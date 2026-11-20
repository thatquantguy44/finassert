/* finassert Excel add-in: binds one table or fixed rectangular range, writes
 * results to a new sheet, and saves or loads the checks on a sheet. It never changes the
 * cells it reads. All checking happens in the application. */
"use strict";

(function () {
  const RESULTS_SHEET = "finassert results";
  const POLICY_SHEET = "finassert policy";
  const BLOCK_ROWS = 5000; // rows read per request, to stay inside Office's payload limits
  const MAX_CELLS = 5000000;
  let source = null;
  let handlers = [];
  let busy = false;
  let revision = 0;
  let active = null;
  let closing = false;
  let record = null;
  let freshness = "Unbound";
  let reason = "Choose a source.";
  let config = window.finassertCapture.settings({});
  let configError = "";
  const ownedSheetIds = new Set();
  const captureTools = window.finassertCapture;
  let displayedOutcome = null;

  function element(tag, text, parent) {
    const node = document.createElement(tag);
    node.textContent = text;
    parent.appendChild(node);
    return node;
  }

  function renderDiagnostics() {
    const outcome = app().isLiveResult() ? app().result() : null;
    const navigation = outcome && outcome.navigation;
    $("excel-findings").hidden = !navigation;
    if (displayedOutcome !== outcome) {
      displayedOutcome = outcome;
      $("excel-findings-list").replaceChildren();
      $("excel-navigation-state").textContent = "";
      if (navigation) navigation.results.forEach((result, ri) => {
        const card = element("article", "", $("excel-findings-list"));
        card.className = "excel-finding";
        element("h4", `${result.title} — ${result.outcome === "error" ? "could not run" : result.outcome}`, card);
        element("p", `If check fails: ${app().failureAction(result.severity)}.`, card).className = "hint";
        element("p", result.message, card);
        if (!result.collections.length) element("p", "No retained diagnostic examples.", card);
        result.collections.forEach((collection, ci) => {
          element("p", `${collection.kind}: ${collection.count} total; example cap ${collection.limit}; ${collection.observations.length} shown; ${collection.truncated ? "truncated" : "not truncated"}.`, card);
          collection.observations.forEach((sample, oi) => {
            element("pre", JSON.stringify(sample.observation, null, 2), card).className = "excel-observation";
            if (!sample.targets.length) element("p", "No source row", card);
            sample.targets.forEach((target, ti) => {
              if (target.status !== "resolved") {
                element("p", `${target.role} ${JSON.stringify(target.label)}: ${target.reason}`, card);
                return;
              }
              const button = element("button", `Select ${target.column_index === null ? "source row" : "cell in row"} ${target.row} (${target.role.toLowerCase()} ${JSON.stringify(target.label)})`, card);
              button.type = "button";
              button.addEventListener("click", () => navigate(outcome, ri, ci, oi, ti));
            });
          });
        });
      });
    }
    for (const button of $("excel-findings-list").querySelectorAll("button")) {
      button.disabled = busy || freshness !== "Current" || !record || record.outcome !== outcome;
    }
  }

  const $ = (id) => document.getElementById(id);
  const app = () => window.finassertApp;

  function setPaneView(view, updateRoute = false) {
    const settings = view === "settings";
    $("excel-validation-view").hidden = settings;
    $("excel-settings-view").hidden = !settings;
    document.body.classList.add("excel-pane");
    document.body.classList.toggle("excel-settings-route", settings);
    const title = settings ? "Settings" : "Validation";
    document.title = `finassert ${title}`;
    $("app-title").textContent = title;
    $("app-lede").textContent = settings
      ? "Settings panel. Configure how finassert reads and verifies this workbook."
      : "Main validation panel. Choose your source, run checks, and review the results.";
    if (updateRoute) {
      const url = new URL(window.location.href);
      if (settings) url.searchParams.set("view", "settings");
      else url.searchParams.delete("view");
      window.history.replaceState({}, "", url);
    }
    window.scrollTo(0, 0);
    if (updateRoute) {
      $("app-title").focus({ preventScroll: true });
    }
  }

  function say(text, isError) {
    if (app()) app().setStatus(text, isError);
  }

  // Preserve Excel's exact quoting (including doubled apostrophes in sheet names).
  function describe(address) {
    return address;
  }

  const LOAD = ["rowCount", "columnCount", "rowIndex", "columnIndex", "address"];
  const supports = (version) => Office.context.requirements.isSetSupported("ExcelApi", version);
  const epoch = () => $("excel-date-system").value;

  function renderFreshness() {
    const stamp = record ? ` Last verified: ${record.verifiedAt || "not verified"}.` : "";
    const monitor = config.monitoring === "on-demand" ? " Live alerts are off; actions reverify the source." : "";
    const text = `${freshness} — ${reason}${stamp}${monitor}`;
    $("excel-freshness").textContent = text;
    $("excel-freshness").dataset.state = freshness;
    app().setLiveState({ state: freshness, reason, text, busy });
    app().blockData(busy || !source || !epoch() || Boolean(configError));
    for (const id of ["excel-read", "excel-bind-table", "excel-tables-refresh", "excel-date-system",
      "excel-monitoring", "excel-capture-mode", "excel-confirmations", "excel-block-rows",
      "excel-block-cells", "excel-capture-timeout", "excel-settings-reset", "spike-run", "excel-save-policy", "excel-load-policy"]) {
      $(id).disabled = busy;
    }
    $("excel-cancel").disabled = !busy;
    renderOutputControls();
    sourceSummary();
    renderDiagnostics();
  }

  function state(next, message) {
    freshness = next;
    reason = message;
    renderFreshness();
  }

  function invalidate(message, structural = false) {
    revision++;
    if (structural && source && source.kind === "range") {
      source = null;
      record = null;
      app().clearData();
      state("Unbound", message + " Reselect the fixed range.");
    } else if (busy && freshness === "Blocked") renderFreshness();
    else state(source ? (app().result() ? "Stale" : "Ready") : "Unbound", message);
  }

  function assertJob(job) {
    if (closing || active !== job || job.cancelled || revision !== job.generation ||
        source !== job.source || epoch() !== job.dateSystem || app().policyKey() !== job.policyKey ||
        (configError && !job.independent) || JSON.stringify(config) !== job.configKey ||
        (job.dataVersion !== null && job.dataVersion !== app().dataVersion())) {
      throw new Error("The operation was cancelled or its source, policy or settings changed. Rerun the checks.");
    }
    if (performance.now() > job.deadline) throw new Error("Operation timed out between requests. Reduce the source or increase the timeout.");
  }

  async function sync(context, job) {
    if (job) assertJob(job);
    await context.sync();
    if (job) assertJob(job);
  }

  async function operate(kind, action) {
    if (busy || closing) return false;
    const job = { kind, generation: revision, source, dateSystem: epoch(), policyKey: app().policyKey(),
      settings: config, configKey: JSON.stringify(config), dataVersion: null,
      deadline: performance.now() + config.timeoutSeconds * 1000,
      manualAcknowledged: $("excel-manual-calculated").checked, cancelled: false,
      independent: ["policy", "outputs"].includes(kind) };
    active = job;
    busy = true;
    if (["run", "read", "export", "navigate"].includes(kind)) state("Reading", "Reading the bound source.");
    else renderFreshness();
    try {
      if (configError && !job.independent) throw new Error(configError);
      await action(job);
      return true;
    } catch (error) {
      // A completion belonging to an old pane/operation cannot restore any state.
      if (!closing && active === job) {
        if (["read", "bind", "date"].includes(kind)) app().clearData();
        const message = error && error.message ? error.message : String(error);
        state(source ? "Blocked" : "Unbound", message);
        say("Excel could not complete the operation: " + message, true);
      }
      return false;
    } finally {
      if (active === job) { active = null; busy = false; if (!closing) renderFreshness(); }
    }
  }

  function guarded(action, kind = "action") {
    return () => operate(kind, action);
  }

  async function calculation(context, job) {
    if (!supports("1.9") || !source.eventsReady) {
      throw new Error("Verified live checks need ExcelApi 1.9 and edit/calculation/format events. Update Excel.");
    }
    context.application.load(["calculationMode", "calculationState"]);
    await sync(context, job);
    const mode = context.application.calculationMode;
    if (!["Automatic", "AutomaticExceptTables", "Manual"].includes(mode)) throw new Error("Excel returned an unknown calculation mode.");
    if (context.application.calculationState !== "Done") throw new Error("Calculation is pending or running. Calculate in Excel, then try again.");
    if (mode === "Manual" && !job.manualAcknowledged) {
      throw new Error("Manual calculation mode: calculate in Excel, then confirm 'I calculated this workbook' in the pane.");
    }
    if (job.calculationMode && job.calculationMode !== mode) throw new Error("Calculation mode changed during the operation. Rerun.");
    job.calculationMode = mode;
  }

  function checkSize(range) {
    if (range.rowCount < 2 || range.columnCount < 1) {
      throw new Error("Select a header and at least one data row, or explicitly choose a workbook table.");
    }
    if (range.rowCount * range.columnCount > MAX_CELLS) {
      throw new Error("Select at most 5,000,000 cells, including the header. No cells were fetched.");
    }
  }

  function sourceSummary(parsedRows) {
    if (source && parsedRows != null) source.parsed_row_count = parsedRows;
    if (source) parsedRows = source.parsed_row_count;
    $("excel-source-summary").textContent = source
      ? `${source.kind === "table" ? `Table "${source.table_name}"; ` : "Fixed range; "}` +
        `worksheet "${source.worksheet_name}"; ${source.address}; header row ${source.header_row}; ` +
        `${source.data_row_count} physical data row(s), ${source.column_count} column(s). ` +
        (parsedRows == null ? "" : `${parsedRows} parsed data row(s). `) +
        (source.kind === "table" ? "Table totals excluded. " : "Totals exclusion follows the selected bounds. ") +
        `Hidden and filtered rows included. Date system: ${epoch() || "choose 1900 or 1904"} (user choice).`
      : "No source bound.";
    $("excel-source-read").disabled = busy || !source || !epoch();
  }

  async function refreshTables() {
    const tables = await Excel.run(async (context) => {
      const collection = context.workbook.tables;
      collection.load("items/id,items/name");
      await context.sync();
      for (const table of collection.items) table.worksheet.load(["id", "name"]);
      await context.sync();
      return collection.items.map((table) => ({ id: table.id, name: table.name, sheet: table.worksheet.name }));
    });
    const picker = $("excel-table");
    picker.replaceChildren(new Option(tables.length ? "Choose a table…" : "No workbook tables", ""),
      ...tables.map((table) => new Option(`${table.sheet} — ${table.name}`, table.id)));
  }

  async function tableRange(context, id, job) {
    const table = context.workbook.tables.getItem(id);
    table.load(["id", "name"]);
    table.worksheet.load(["id", "name"]);
    table.rows.load("count");
    await sync(context, job);
    if (!table.rows.count) throw new Error("The table has no data rows.");
    const header = table.getHeaderRowRange();
    const body = table.getDataBodyRange();
    header.load(LOAD);
    body.load(LOAD);
    await sync(context, job);
    if (header.rowCount !== 1 || body.rowIndex !== header.rowIndex + 1 ||
        body.columnIndex !== header.columnIndex || body.columnCount !== header.columnCount) {
      throw new Error("The table must have one header row directly above its data body.");
    }
    const range = header.getResizedRange(body.rowCount, 0);
    range.load(LOAD);
    await sync(context, job);
    return { range, sheet: table.worksheet, table };
  }

  function descriptor(range, sheet, table) {
    checkSize(range);
    return { kind: table ? "table" : "range", worksheet_id: sheet.id, worksheet_name: sheet.name,
      ...(table ? { table_id: table.id, table_name: table.name } : {}),
      address: describe(range.address), header_row: range.rowIndex + 1,
      rowIndex: range.rowIndex, columnIndex: range.columnIndex,
      data_row_count: range.rowCount - 1, column_count: range.columnCount,
      hidden_rows: "include_all" };
  }

  async function disposeHandlers() {
    const previous = handlers;
    handlers = [];
    for (const handler of previous) {
      await Excel.run(handler.context, async (context) => { handler.remove(); await context.sync(); });
    }
  }

  function installHandlers(context, sheet, bound, table) {
    const add = (member, callback) => {
      if (member && typeof member.add === "function") handlers.push(member.add((event) => {
        if (!closing && source === bound) callback(event);
      }));
    };
    bound.eventsReady = ["onChanged", "onCalculated", "onFormatChanged"].every(
      (name) => sheet[name] && typeof sheet[name].add === "function");
    add(sheet.onChanged, (event) => {
      if (event.changeType !== "RangeEdited") {
        $("excel-manual-calculated").checked = false;
        invalidate("The worksheet structure changed.", true);
      } else if (config.monitoring === "events" && captureTools.overlaps(event.address, bound)) {
        $("excel-manual-calculated").checked = false;
        invalidate("Bound source cells changed.");
      }
    });
    add(sheet.onFormatChanged, (event) => {
      if (config.monitoring === "events" && captureTools.overlaps(event.address, bound)) invalidate("Source number formats changed.");
    });
    add(sheet.onCalculated, () => {
      $("excel-manual-calculated").checked = false;
      if (config.monitoring === "events") invalidate("The source worksheet recalculated.");
    });
    if (table) add(table.onChanged, () => {
      if (config.monitoring === "events") {
        $("excel-manual-calculated").checked = false;
        invalidate("The bound table changed or resized.");
      }
    });
  }

  async function bind(kind, job) {
    await disposeHandlers();
    assertJob(job);
    source = null;
    revision++;
    job.generation = revision;
    job.source = null;
    record = null;
    app().clearData();
    state("Unbound", "Resolving the selected source.");
    sourceSummary();
    if (kind === "range" && !supports("1.13")) {
      throw new Error("Range binding needs ExcelApi 1.13 to reject merged headers. Update Excel or choose a table.");
    }
    const bound = await Excel.run(async (context) => {
      let range, sheet, table;
      if (kind === "table") {
        if (!$("excel-table").value) throw new Error("Choose a table first.");
        ({ range, sheet, table } = await tableRange(context, $("excel-table").value, job));
      } else {
        try {
          range = context.workbook.getSelectedRange();
          range.load(LOAD);
          sheet = range.worksheet;
          sheet.load(["id", "name"]);
          await sync(context, job);
        } catch (error) {
          assertJob(job);
          throw new Error("Select one rectangular range; disjoint selections are not supported.");
        }
      }
      const bound = descriptor(range, sheet, table);
      installHandlers(context, sheet, bound, table);
      await sync(context, job);
      return bound;
    });
    assertJob(job);
    source = bound;
    job.source = bound;
    sourceSummary();
    if (epoch()) await captureSource(job);
    else {
      state("Ready", "Source bound; choose 1900 or 1904 before reading.");
      say("Source bound. Choose the workbook's 1900 or 1904 date system before reading or running.");
    }
  }

  async function resolvedRange(context, bound, job) {
    if (bound.kind === "table") {
      const resolved = await tableRange(context, bound.table_id, job);
      if (resolved.sheet.id !== bound.worksheet_id || resolved.table.id !== bound.table_id) {
        throw new Error("The bound table is no longer on its original worksheet. Choose the source again.");
      }
      return resolved;
    }
    const sheet = context.workbook.worksheets.getItem(bound.worksheet_id);
    sheet.load(["id", "name"]);
    const range = sheet.getRangeByIndexes(bound.rowIndex, bound.columnIndex,
      bound.data_row_count + 1, bound.column_count);
    range.load(LOAD);
    await sync(context, job);
    if (sheet.id !== bound.worksheet_id) throw new Error("The bound worksheet no longer exists. Reselect the source.");
    return { range, sheet };
  }

  // Reads a range in blocks of rows, with the formats and types Excel reports.
  async function readRange(context, range, job) {
    const values = [];
    const numberFormats = [];
    const valueTypes = [];
    const formulas = [];
    const limits = job ? job.settings : config;
    if (range.columnCount > limits.blockCells) {
      throw new Error("One source row exceeds the cells-per-request setting. Increase that setting or select fewer columns.");
    }
    const blockRows = Math.max(1, Math.min(limits.blockRows, Math.floor(limits.blockCells / range.columnCount)));
    for (let start = 0; start < range.rowCount; start += blockRows) {
      const rows = Math.min(blockRows, range.rowCount - start);
      const block = range.getRow(start).getResizedRange(rows - 1, 0);
      block.load(["values", "numberFormat", "valueTypes", "formulas"]);
      await sync(context, job);
      values.push(...block.values);
      numberFormats.push(...block.numberFormat);
      valueTypes.push(...block.valueTypes);
      formulas.push(...block.formulas);
    }
    return { values, numberFormats, valueTypes, formulas, firstRow: range.rowIndex + 1 };
  }

  async function readCapture(job) {
    if (!source || !epoch()) throw new Error("Bind one source and choose 1900 or 1904 before running.");
    assertJob(job);
    const bound = job.source;
    const capture = await Excel.run(async (context) => {
      await calculation(context, job);
      const { range, sheet, table } = await resolvedRange(context, bound, job);
      const current = descriptor(range, sheet, table);
      if (bound.kind === "range") {
        const merged = range.getRow(0).getMergedAreasOrNullObject();
        await sync(context, job);
        if (!merged.isNullObject) throw new Error("Unmerge the source header cells, then reselect the range.");
      }
      const { formulas, ...payload } = await readRange(context, range, job);
      payload.date1904 = job.dateSystem === "1904";
      const again = await resolvedRange(context, bound, job);
      if (JSON.stringify(current) !== JSON.stringify(descriptor(again.range, again.sheet, again.table))) {
        throw new Error("Source identity or bounds changed during a chunked read. Rerun.");
      }
      await calculation(context, job);
      return { current, payload, formulas };
    });
    assertJob(job);
    if (!capture.payload.values.slice(1).some((row) => row.some((cell) =>
      cell != null && (typeof cell !== "string" || cell.trim() !== "")))) {
      throw new Error("The source has no nonblank data rows.");
    }
    const fingerprints = await captureTools.fingerprints(capture.current, capture.payload, capture.formulas);
    assertJob(job);
    return { ...capture, ...fingerprints, capturedAt: new Date().toISOString() };
  }

  function ingest(capture, job) {
    assertJob(job);
    const bound = job.source;
    // The Python reader owns header normalization and all cell/date interpretation.
    const parsed = app().useData(capture.current.address, JSON.stringify(capture.payload), "excel-range", true);
    job.dataVersion = app().dataVersion();
    if (!parsed) throw new Error("The bound source could not be parsed. Correct its headers or data and read again.");
    if (!parsed.rowCount) {
      throw new Error("The source has no nonblank data rows.");
    }
    if (bound.headers && JSON.stringify(bound.headers) !== JSON.stringify(parsed.columns)) {
      source = null;
      sourceSummary();
      throw new Error("Source headers changed. Reselect the source and review every column mapping before running.");
    }
    Object.assign(bound, capture.current, { headers: parsed.columns, date_system: job.dateSystem, date_system_source: "user" });
    sourceSummary(parsed.rowCount);
    say(`Read ${bound.kind === "table" ? `the table "${bound.table_name}"` : "the bound range"} (${bound.address}).`);
  }

  async function captureSource(job) {
    record = null;
    state("Reading", "Reading a preview; Run checks verifies the result.");
    const capture = await readCapture(job);
    ingest(capture, job);
    state("Ready", "Source preview read. Run the checks to verify a result.");
  }

  function sameCapture(left, right) {
    return left.snapshot === right.snapshot && left.formula === right.formula;
  }

  async function runBound(job) {
    const first = await readCapture(job);
    ingest(first, job);
    state("Checking", "Checking the captured input; the candidate is not yet current.");
    const outcome = app().evaluate();
    if (!outcome.ok) {
      app().publishResult(outcome);
      throw new Error(outcome.error || "The policy is invalid. Fix the listed problems and rerun.");
    }
    assertJob(job);
    // Let queued edits and host notifications run after synchronous Python evaluation.
    await new Promise((resolve) => setTimeout(resolve, 0));
    assertJob(job);
    let verifiedAt = null;
    if (job.settings.capture === "verified") {
      for (let i = 1; i < job.settings.confirmations; i++) {
        state("Reading", `Verifying capture ${i + 1} of ${job.settings.confirmations}.`);
        const after = await readCapture(job);
        if (!sameCapture(first, after)) throw new Error("The source changed between captures. Candidate discarded; rerun the checks.");
        verifiedAt = after.capturedAt;
      }
    }
    assertJob(job);
    record = { snapshot: first.snapshot, formula: first.formula, capturedAt: first.capturedAt,
      verifiedAt, policyKey: job.policyKey, settingsKey: job.configKey, geometry: first.current,
      parsedRows: source.parsed_row_count, dateSystem: job.dateSystem, outcome };
    if (verifiedAt) app().excelEvidence(outcome, excelContext(record));
    app().publishResult(outcome);
    $("excel-manual-calculated").checked = false;
    if (verifiedAt) state("Current", "The result matched its source at the last verification time.");
    else state("Stale", "Snapshot-only result: stable capture is disabled; current-result export is unavailable.");
  }

  async function withCurrentResult(action, kind = "export") {
    if (!app().isLiveResult()) return operate("action", action);
    if (busy || freshness !== "Current" || !record || config.capture !== "verified") {
      say("Rerun with stable capture enabled before exporting or navigating a current result.", true);
      return false;
    }
    const result = record;
    return operate(kind, async (job) => {
      if (result.policyKey !== job.policyKey || result.settingsKey !== job.configKey || app().result() !== result.outcome) {
        throw new Error("The result's policy or settings changed. Rerun before exporting.");
      }
      for (let i = 0; i < job.settings.confirmations; i++) {
        const current = await readCapture(job);
        if (!sameCapture(result, current)) throw new Error("The bound source changed since this result. Rerun before exporting.");
        result.verifiedAt = current.capturedAt;
      }
      assertJob(job);
      app().excelEvidence(result.outcome, excelContext(result));
      await action(job, result);
      assertJob(job);
      $("excel-manual-calculated").checked = false;
      state("Current", "Source and policy reverified before the action.");
    });
  }

  function excelContext(result) {
    const geometry = result.geometry;
    return { schema_version: 1, kind: geometry.kind,
      worksheet_id: geometry.worksheet_id, worksheet_name: geometry.worksheet_name,
      ...(geometry.kind === "table" ? { table_id: geometry.table_id, table_name: geometry.table_name } : {}),
      address: geometry.address, header_row: geometry.header_row,
      data_row_count: result.parsedRows, physical_data_row_count: geometry.data_row_count,
      column_count: geometry.column_count, hidden_rows: "include_all",
      date_system: result.dateSystem, date_system_source: "user",
      captured_at: result.capturedAt, verified_at: result.verifiedAt, snapshot_sha256: result.snapshot };
  }

  function renderOutputControls() {
    $("excel-replace").disabled = busy || !$("excel-replace-target").value || !app().result() ||
      (app().isLiveResult() && freshness !== "Current");
    for (const id of ["excel-replace-target", "excel-output-refresh", "excel-policy-sheet", "excel-policy-refresh"]) $(id).disabled = busy;
  }

  async function refreshOutputs(job, preferredPolicy) {
    const entries = await window.finassertOutput.list((context) => sync(context, job));
    const selected = $("excel-replace-target").value;
    const policy = preferredPolicy || $("excel-policy-sheet").value;
    const eligible = entries.filter((entry) => entry.owner?.state === "complete");
    $("excel-replace-target").replaceChildren(new Option("Choose a completed owned results sheet…", ""),
      ...eligible.filter((entry) => entry.owner.role === "results" && (!source || entry.id !== source.worksheet_id))
        .map((entry) => new Option(entry.name, entry.id)));
    if ([...$("excel-replace-target").options].some((item) => item.value === selected)) $("excel-replace-target").value = selected;
    const policies = entries.filter((entry) => entry.owner?.role === "policy" && entry.owner.state === "complete" ||
      !entry.owner && entry.name === POLICY_SHEET);
    $("excel-policy-sheet").replaceChildren(new Option("Choose a saved policy…", ""),
      ...policies.map((entry) => new Option(entry.name, entry.id)));
    $("excel-policy-sheet").value = policies.some((entry) => entry.id === policy) ? policy : policies.at(-1)?.id || "";
    renderOutputControls();
    return entries;
  }

  function outputOptions(job, replaceId) {
    return { replaceId, sync: (context) => sync(context, job), check: () => { if (job) assertJob(job); },
      isSource: (id) => source?.worksheet_id === id || job?.source?.worksheet_id === id,
      canRecover: () => !closing };
  }

  async function navigate(outcome, ri, ci, oi, ti) {
    if (!record || record.outcome !== outcome || app().result() !== outcome || !app().isLiveResult()) return false;
    const target = outcome.navigation?.results[ri]?.collections[ci]?.observations[oi]?.targets[ti];
    if (!target || target.status !== "resolved") return false;
    $("excel-navigation-state").textContent = "Verifying the source before navigation…";
    const selected = await withCurrentResult(async (job, result) => {
      await Excel.run(async (context) => {
        const { range, sheet, table } = await resolvedRange(context, job.source, job);
        if (JSON.stringify(descriptor(range, sheet, table)) !== JSON.stringify(result.geometry)) {
          throw new Error("Source identity or bounds changed. Rerun before navigating.");
        }
        const row = target.row - 1;
        const column = target.column_index;
        if (!Number.isSafeInteger(row) || row <= range.rowIndex || row >= range.rowIndex + range.rowCount ||
            (column !== null && (!Number.isSafeInteger(column) || column < 0 || column >= range.columnCount))) {
          throw new Error("Diagnostic target is outside the captured source. Review the mapping and rerun.");
        }
        assertJob(job);
        // Numeric indices and worksheet identity avoid parsing diagnostic text,
        // quoted names, formulas, links or business keys as Excel addresses.
        const destination = sheet.getRangeByIndexes(row, range.columnIndex + (column === null ? 0 : column),
          1, column === null ? range.columnCount : 1);
        sheet.activate();
        destination.select();
        await sync(context, job);
      });
    }, "navigate");
    if (!closing) $("excel-navigation-state").textContent = selected
      ? `Selected ${target.column_index === null ? "source row" : "cell in row"} ${target.row}. Source data was not changed.`
      : `Navigation unavailable. ${reason}`;
    return selected;
  }

  // Synthetic diagnostics keep their separate session-owned scratch destination.
  // Results and policy output use the durable ID-based lifecycle below.
  async function freshSheet(context, name) {
    let sheet = context.workbook.worksheets.getItemOrNullObject(name);
    await context.sync();
    if (sheet.isNullObject) {
      sheet = context.workbook.worksheets.add(name);
      sheet.load("id");
      await context.sync();
      ownedSheetIds.add(sheet.id);
    } else {
      sheet.load("id");
      await context.sync();
      if (source && sheet.id === source.worksheet_id) throw new Error("Output cannot replace the bound source worksheet.");
      if (!ownedSheetIds.has(sheet.id)) {
        throw new Error(`The sheet "${name}" already exists and was not created in this pane session. Rename it before trying again.`);
      }
      const used = sheet.getUsedRangeOrNullObject();
      await context.sync();
      if (!used.isNullObject) used.clear();
    }
    return sheet;
  }

  async function writeResults(sheetData, job, replaceId) {
    return window.finassertOutput.write(sheetData, "results", outputOptions(job, replaceId));
  }

  async function savePolicy(job) {
    if (!app().hasChecks()) {
      say("Add or open some checks first.", true);
      return;
    }
    const yaml = app().policyYaml();
    if (yaml === null) return;
    const rows = app().policySheet(yaml);
    const sheet = await window.finassertOutput.write({ rows, boldRows: [0] }, "policy", outputOptions(job));
    await refreshOutputs(job, sheet.id);
    say(`Saved the checks on the sheet "${sheet.name}". Your data was not changed.`);
  }

  async function loadPolicy(job) {
    const entries = await refreshOutputs(job);
    const id = $("excel-policy-sheet").value;
    const chosen = entries.find((entry) => entry.id === id);
    if (!chosen) { say("No completed saved policy is available. Save a policy or refresh the list.", true); return; }
    const values = await Excel.run(async (context) => {
      const sheet = context.workbook.worksheets.getItem(id);
      const used = sheet.getUsedRange(true);
      used.load("values");
      await sync(context, job);
      return used.values;
    });
    const text = app().policyFromSheet(values);
    if (!text.ok) {
      say(text.error, true);
      return;
    }
    app().openPolicyText(text.text, "finassert-policy.yml", `the checks saved in this workbook`);
  }

  async function useSelection(job) {
    if (!app() || !app().ready()) {
      say("The checking engine is still loading. Try again in a moment.", true);
      return;
    }
    say("Reading the cells…");
    await bind("range", job);
  }

  async function writeToSheet(replaceId) {
    if (!app() || !app().result()) return;
    $("excel-output-status").textContent = "Preparing and verifying the export…";
    const done = await withCurrentResult(async (job) => {
      const sheet = await writeResults(app().resultsSheet(), job, replaceId);
      await refreshOutputs(job);
      const text = `Results written to the sheet "${sheet.name}" as captured snapshot evidence. Your data was not changed.`;
      $("excel-output-status").textContent = text;
      say(text);
    });
    if (!done && !closing) $("excel-output-status").textContent = reason;
    return done;
  }

  function applySettings() {
    try {
      const next = captureTools.settings({
        monitoring: $("excel-monitoring").value, capture: $("excel-capture-mode").value,
        confirmations: Number($("excel-confirmations").value), blockRows: Number($("excel-block-rows").value),
        blockCells: Number($("excel-block-cells").value), timeoutSeconds: Number($("excel-capture-timeout").value),
      });
      const changed = JSON.stringify(config) !== JSON.stringify(next) || configError;
      config = next;
      configError = "";
      $("excel-settings-status").textContent = next.capture === "verified"
        ? `${next.confirmations} matching captures; ${next.blockRows} rows / ${next.blockCells} cells per request; ${next.timeoutSeconds}s timeout.`
        : "Snapshot-only results remain unverified and cannot export as current evidence.";
      if (changed) invalidate("Freshness or capture settings changed. Run again.");
      else renderFreshness();
    } catch (error) {
      configError = error.message;
      revision++;
      $("excel-settings-status").textContent = configError;
      state("Blocked", "Invalid capture settings: " + configError);
    }
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
      const payload = await readRange(context, range);
      payload.date1904 = epoch() === "1904";
      return { name: describe(range.address), payload };
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
    for (const v of ["1.1", "1.2", "1.3", "1.4", "1.5", "1.7", "1.8", "1.9", "1.13"]) {
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
      return { ok: info.sets["1.7"] === true, detail: `ExcelApi sets supported: ${Object.entries(info.sets).filter(([, ok]) => ok).map(([v]) => v).join(", ") || "none"}` +
        (missing.length ? `; not supported: ${missing.join(", ")}` : "") + " (the current add-in needs 1.7 for sheet writes)" };
    });
    await run("planned workflow API baseline", async () => {
      // This reads host metadata only. E-02/E-03 own the actual workflow guards.
      if (info.sets["1.9"] !== true) {
        return { ok: false, detail: "Spec 0016 needs ExcelApi 1.9; the current prototype uses 1.7. Calculation-state probe skipped." };
      }
      const baseline = await Excel.run(async (context) => {
        const sheet = context.workbook.worksheets.getActiveWorksheet();
        context.application.load(["calculationMode", "calculationState"]);
        await context.sync();
        return {
          calculationMode: context.application.calculationMode,
          calculationState: context.application.calculationState,
          worksheetEvents: Object.fromEntries(["onChanged", "onCalculated", "onFormatChanged"].map(
            (name) => [name, Boolean(sheet[name] && typeof sheet[name].add === "function")]
          )),
          dateSystem: "not detected; explicit user choice is required in E-02",
          currentDatePayload: "date1904 explicitly supplied from the required user choice",
        };
      });
      info.workflowBaseline = baseline;
      const readable = ["Automatic", "AutomaticExceptTables", "Manual"].includes(baseline.calculationMode) &&
        ["Done", "Pending", "Calculating"].includes(baseline.calculationState);
      return { ok: readable && Object.values(baseline.worksheetEvents).every(Boolean),
        detail: JSON.stringify(baseline) + " (read-only probe; no calculation setting changed)" };
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
    if (!epoch()) throw new Error("Choose 1900 or 1904 before running diagnostics.");
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
    setPaneView(new URLSearchParams(window.location.search).get("view"));
    if (typeof Office === "undefined" || !Office.onReady) return;
    const info = await Office.onReady();
    if (info.host !== Office.HostType.Excel) return;
    // The add-in works from one explicit workbook source. Keep the browser-only
    // file picker out of this host so there is one clear starting point.
    document.body.classList.add("excel-host");
    $("data-drop").hidden = true;
    $("sheet-picker").hidden = true;
    $("excel-panel").hidden = false;
    for (const id of ["excel-write", "excel-save-policy", "excel-load-policy"]) $(id).hidden = false;
    $("excel-open-settings").addEventListener("click", () => setPaneView("settings", true));
    $("excel-back-to-validation").addEventListener("click", () => setPaneView("validation", true));
    window.addEventListener("popstate", () => {
      setPaneView(new URLSearchParams(window.location.search).get("view"));
    });
    $("excel-read").addEventListener("click", guarded(useSelection, "bind"));
    $("excel-tables-refresh").addEventListener("click", guarded(refreshTables));
    $("excel-bind-table").addEventListener("click", guarded((job) => bind("table", job), "bind"));
    $("excel-source-read").addEventListener("click", guarded(captureSource, "read"));
    $("excel-date-system").addEventListener("change", () => {
      invalidate("Date interpretation changed.");
      record = null;
      app().clearData();
      if (source && epoch()) operate("date", captureSource);
      else {
        state(source ? "Ready" : "Unbound", "Choose 1900 or 1904 before running.");
        say("Choose the workbook's 1900 or 1904 date system before running.");
      }
    });
    $("excel-write").addEventListener("click", () => writeToSheet());
    $("excel-replace").addEventListener("click", () => writeToSheet($("excel-replace-target").value));
    $("excel-replace-target").addEventListener("change", renderOutputControls);
    $("excel-output-refresh").addEventListener("click", guarded(refreshOutputs, "outputs"));
    $("excel-policy-refresh").addEventListener("click", guarded(refreshOutputs, "outputs"));
    $("excel-save-policy").addEventListener("click", guarded(savePolicy, "policy"));
    $("excel-load-policy").addEventListener("click", guarded(loadPolicy, "policy"));
    $("spike-run").addEventListener("click", guarded(spike, "diagnostics"));
    $("spike-copy").addEventListener("click", guarded(copyReport));
    window.finassertExcel = {
      run: () => operate("run", runBound),
      withCurrentResult,
      navigate,
      policyChanged(message) { invalidate(message); },
      inputChanged() { record = null; invalidate("Input changed. Run the bound source again for verified live results."); },
      status: () => ({ state: freshness, reason, busy, generation: revision, settings: { ...config },
        snapshot: record ? { sha256: record.snapshot, capturedAt: record.capturedAt, verifiedAt: record.verifiedAt } : null }),
    };
    for (const id of ["excel-monitoring", "excel-capture-mode", "excel-confirmations", "excel-block-rows", "excel-block-cells", "excel-capture-timeout"]) {
      $(id).addEventListener("change", applySettings);
      if ($(id).tagName === "INPUT") $(id).addEventListener("input", applySettings);
    }
    $("excel-settings-reset").addEventListener("click", () => {
      for (const [id, key] of [["excel-monitoring", "monitoring"], ["excel-capture-mode", "capture"],
        ["excel-confirmations", "confirmations"], ["excel-block-rows", "blockRows"],
        ["excel-block-cells", "blockCells"], ["excel-capture-timeout", "timeoutSeconds"]]) {
        $(id).value = captureTools.defaults[key];
      }
      applySettings();
    });
    $("excel-manual-calculated").addEventListener("change", () => {
      if (busy) invalidate("Manual calculation confirmation changed during the operation. Try again.");
      else renderFreshness();
    });
    $("excel-cancel").addEventListener("click", () => {
      if (!active) return;
      active.cancelled = true;
      invalidate("Cancellation requested; the current host request or Python check must finish first.");
    });
    applySettings();
    await guarded(refreshTables)();
    renderFreshness();
    // Office destroys session handlers when the pane closes. Avoid new host requests on pagehide.
    window.addEventListener("pagehide", () => { closing = true; revision++; handlers = []; record = null; });
  }

  start();
})();
