/* finassert browser application. All validation runs in Python (finassert.web). */
"use strict";

(function () {
  const PYODIDE_URL = "{{PYODIDE_URL}}";
  const state = {
    web: null,
    pyodide: null,
    catalog: [],
    data: null, // {name, text, columns}
    checks: [], // [{id, spec, values}]
    result: null,
    nextId: 1,
  };

  const $ = (id) => document.getElementById(id);

  function setStatus(text, isError) {
    const node = $("status");
    node.textContent = text;
    node.classList.toggle("error", Boolean(isError));
  }

  function call(name, ...args) {
    return JSON.parse(state.web[name](...args));
  }

  async function boot() {
    try {
      const pyodide = await loadPyodide({ indexURL: PYODIDE_URL });
      // Fetch everything up front so no request is made once files are opened.
      await pyodide.loadPackage("pyyaml");
      const wheel = $("finassert-wheel");
      const bytes = Uint8Array.from(atob(wheel.textContent.trim()), (c) => c.charCodeAt(0));
      const sitePackages = pyodide.runPython("import site; site.getsitepackages()[0]");
      pyodide.unpackArchive(bytes, "zip", { extractDir: sitePackages });
      state.pyodide = pyodide;
      state.web = pyodide.pyimport("finassert.web");
      state.catalog = call("catalog").rules;
      state.templates = call("templates").templates;
      renderCatalogPicker();
      renderTemplates();
      setStatus("Ready. Nothing you open here is uploaded.");
      refresh();
    } catch (error) {
      setStatus("The checking engine could not load: " + error.message, true);
    }
  }

  function renderCatalogPicker() {
    const select = $("add-check");
    select.replaceChildren(
      ...state.catalog.map((spec) => option(spec.name, spec.title))
    );
  }

  function option(value, text, selected) {
    const node = document.createElement("option");
    node.value = value;
    node.textContent = text;
    if (selected) node.selected = true;
    return node;
  }

  function element(tag, attributes, children) {
    const node = document.createElement(tag);
    for (const [key, value] of Object.entries(attributes || {})) {
      if (key === "text") node.textContent = value;
      else if (key === "className") node.className = value;
      else node.setAttribute(key, value);
    }
    for (const child of children || []) node.append(child);
    return node;
  }

  /* ---------- data ---------- */

  async function openData(file) {
    if (!file || !state.web) return;
    const workbook = /\.xls[xm]$/i.test(file.name);
    const content = workbook ? new Uint8Array(await file.arrayBuffer()) : await file.text();
    state.pending = { name: file.name, content };
    $("sheet-picker").hidden = true;
    showData(null);
  }

  function showData(sheet) {
    const { name, content } = state.pending;
    const info = call("inspect_input", content, name, sheet);
    const errorBox = $("data-error");
    if (!info.ok) {
      state.data = null;
      renderSuggestions([]);
      $("data-summary").hidden = true;
      if (info.sheets) {
        $("sheet-select").replaceChildren(
          option("", "Choose a sheet…", true),
          ...info.sheets.map((item) => option(item, item))
        );
        $("sheet-picker").hidden = false;
        errorBox.hidden = true;
      } else {
        errorBox.textContent = "This file could not be read: " + info.error;
        errorBox.hidden = false;
      }
      refresh();
      return;
    }
    errorBox.hidden = true;
    state.data = { name, content, sheet, columns: info.columns };
    const where = sheet ? `${name}, sheet "${sheet}"` : name;
    $("data-name").textContent =
      `${where}: ${info.row_count} row(s), ${info.columns.length} column(s).` +
      (info.row_count > info.preview.length ? ` First ${info.preview.length} rows:` : "");
    const head = element("tr", {}, info.columns.map((c) => element("th", { scope: "col", text: c })));
    const rows = info.preview.map((row) =>
      element("tr", {}, info.columns.map((c) => element("td", { text: row[c] == null ? "" : String(row[c]) })))
    );
    $("data-preview").replaceChildren(element("thead", {}, [head]), element("tbody", {}, rows));
    $("data-summary").hidden = false;
    renderSuggestions(call("suggest", JSON.stringify(info.columns)).suggestions);
    renderChecks();
    refresh();
  }

  function renderSuggestions(fits) {
    const box = $("suggestions");
    if (!fits.length) {
      box.hidden = true;
      box.replaceChildren();
      return;
    }
    const buttons = fits.slice(0, 3).map((fit) => {
      const button = element("button", { type: "button" }, [
        `${fit.title} (${fit.matched} of ${fit.expected} columns matched)`,
      ]);
      button.addEventListener("click", () => {
        $("template").value = fit.name;
        useTemplate(fit.name);
      });
      return button;
    });
    box.replaceChildren(element("span", { className: "hint", text: "This file looks like: " }), ...buttons);
    box.hidden = false;
  }

  /* ---------- checks ---------- */

  function addCheck(name, values) {
    const spec = state.catalog.find((item) => item.name === name);
    if (!spec) return;
    const initial = {};
    for (const parameter of spec.parameters) {
      if (parameter.kind === "column") {
        const columns = state.data ? state.data.columns : [];
        initial[parameter.name] =
          parameter.default && columns.includes(parameter.default) ? parameter.default : "";
      } else if (parameter.kind === "tolerance") {
        initial[parameter.name] = { absolute: parameter.default || "", relative: "" };
      } else if (parameter.kind === "columns") {
        initial[parameter.name] = [];
      } else {
        initial[parameter.name] = parameter.default == null ? "" : String(parameter.default);
      }
    }
    // Numbers loaded from a policy keep their original type unless edited, so an
    // unchanged policy runs and exports exactly as it was written.
    const tagged = {};
    const mappings = {};
    const remember = (path, raw) => {
      const loaded = loadedNumber(raw);
      if (loaded.tag) tagged[path] = loaded;
      return loaded.text;
    };
    for (const [key, value] of Object.entries(values || {})) {
      const parameter = spec.parameters.find((p) => p.name === key);
      if (parameter && parameter.kind === "tolerance") {
        if (isToleranceMapping(value)) {
          mappings[key] = Object.keys(value);
          initial[key] = {
            absolute: "absolute" in value ? remember(`${key}.absolute`, value.absolute) : "",
            relative: "relative" in value ? remember(`${key}.relative`, value.relative) : "",
          };
        } else {
          initial[key] = { absolute: remember(`${key}.absolute`, value), relative: "" };
        }
      } else if (parameter && parameter.kind === "columns") {
        initial[key] = Array.isArray(value) ? value.map(String) : [String(value)];
      } else if (parameter && parameter.kind === "number") {
        initial[key] = remember(key, value);
      } else {
        initial[key] = String(value);
      }
    }
    const explicit = new Set(Object.keys(values || {}));
    state.checks.push({ id: state.nextId++, spec, values: initial, tagged, mappings, explicit });
    renderChecks();
    refresh();
  }

  function loadedNumber(raw) {
    if (raw !== null && typeof raw === "object") {
      if (typeof raw.$float === "string") return { text: raw.$float, tag: "$float" };
      if (typeof raw.$int === "string") return { text: raw.$int, tag: "$int" };
    }
    return { text: raw == null ? "" : String(raw), tag: null };
  }

  function isToleranceMapping(value) {
    return (
      value !== null &&
      typeof value === "object" &&
      typeof value.$float !== "string" &&
      typeof value.$int !== "string"
    );
  }

  function isDefault(parameter, value) {
    const fallback = parameter.default == null ? "" : String(parameter.default);
    if (parameter.kind === "tolerance") {
      return value.absolute.trim() === fallback && !value.relative.trim();
    }
    if (parameter.kind === "columns") return value.length === 0;
    return String(value).trim() === fallback || String(value).trim() === "";
  }

  function numberValue(check, path, text) {
    const loaded = check.tagged[path];
    return loaded && loaded.text === text ? { [loaded.tag]: text } : text;
  }

  function renderChecks() {
    const container = $("checks");
    container.replaceChildren(...state.checks.map(renderCheck));
    $("no-checks").hidden = state.checks.length > 0;
  }

  function renderCheck(check, index) {
    const { spec, values } = check;
    const remove = element("button", { type: "button", className: "link", "aria-label": `Remove check ${index + 1}` }, ["Remove"]);
    remove.addEventListener("click", () => {
      state.checks = state.checks.filter((item) => item.id !== check.id);
      renderChecks();
      refresh();
    });
    const fields = spec.parameters.map((parameter) => renderField(check, parameter));
    return element("article", { className: "check", "aria-label": spec.title }, [
      element("header", {}, [
        element("div", {}, [
          element("h3", { text: `${index + 1}. ${spec.title}` }),
          element("p", { className: "hint", text: spec.summary }),
        ]),
        remove,
      ]),
      element("p", { className: "caution" }, [
        element("strong", { text: "Don't use when: " }),
        spec.inappropriate_when,
      ]),
      element("div", { className: "grid" }, fields),
    ]);
  }

  function renderField(check, parameter) {
    const id = `check-${check.id}-${parameter.name}`;
    const value = check.values[parameter.name];
    const set = (next) => {
      check.values[parameter.name] = next;
      refresh();
    };
    let control;
    if (parameter.kind === "column") {
      const columns = state.data ? state.data.columns : [];
      const choices = columns.includes(value) || !value ? columns : [value, ...columns];
      control = element("select", { id }, [
        option(
          "",
          parameter.required
            ? "Choose a column…"
            : parameter.default == null
              ? "Not used"
              : `Default (${parameter.default})`,
          !value
        ),
        ...choices.map((c) => option(c, c, c === value)),
      ]);
      control.addEventListener("change", () => set(control.value));
    } else if (parameter.kind === "choice") {
      // A required choice with no default starts unselected, so it must be picked.
      const prompt = parameter.default == null ? [option("", "Choose…", !value)] : [];
      control = element("select", { id }, [
        ...prompt,
        ...parameter.choices.map((c) => option(c, c, c === value)),
      ]);
      control.addEventListener("change", () => set(control.value));
    } else if (parameter.kind === "columns") {
      const columns = state.data ? state.data.columns : [];
      const choices = [...value.filter((c) => !columns.includes(c)), ...columns];
      const boxes = choices.map((column, index) => {
        const boxId = `${id}-${index}`;
        const box = element("input", { id: boxId, type: "checkbox" });
        box.checked = value.includes(column);
        box.addEventListener("change", () => {
          const current = check.values[parameter.name].filter((c) => c !== column);
          // Keep columns in the order they were ticked: group keys are ordered.
          set(box.checked ? [...current, column] : current);
        });
        return element("label", { for: boxId, className: "checkbox" }, [box, " ", column]);
      });
      control = element("fieldset", { className: "columns", id }, [
        // The visible label is the group's legend, since a fieldset cannot be a label target.
        element("legend", { text: parameter.label + (parameter.required ? " (required)" : "") }),
        ...(boxes.length ? boxes : [element("p", { className: "hint", text: "Open a data file to choose columns." })]),
      ]);
    } else if (parameter.kind === "integer") {
      control = element("input", { id, type: "number", min: String(parameter.minimum ?? 0), step: "1", value });
      control.addEventListener("input", () => set(control.value));
    } else if (parameter.kind === "number") {
      control = element("input", { id, type: "text", inputmode: "decimal", value });
      control.addEventListener("input", () => set(control.value));
    } else {
      const absolute = element("input", { id, type: "text", inputmode: "decimal", value: value.absolute });
      absolute.addEventListener("input", () => set({ ...check.values[parameter.name], absolute: absolute.value }));
      const children = [
        element("label", { for: id, text: parameter.label }),
        absolute,
        element("p", { className: "hint", text: parameter.description }),
      ];
      if (parameter.allow_relative) {
        const relativeId = `${id}-relative`;
        const relative = element("input", { id: relativeId, type: "text", inputmode: "decimal", value: value.relative, placeholder: "0" });
        relative.addEventListener("input", () => set({ ...check.values[parameter.name], relative: relative.value }));
        children.push(
          element("details", {}, [
            element("summary", { text: "Relative allowance" }),
            element("label", { for: relativeId, text: "Relative allowance (fraction of the larger value)" }),
            relative,
          ])
        );
      }
      return element("div", { className: "field" }, children);
    }
    const heading =
      parameter.kind === "columns"
        ? []
        : [
            element("label", {
              for: id,
              text: parameter.label + (parameter.required ? " (required)" : ""),
            }),
          ];
    return element("div", { className: "field" }, [
      ...heading,
      control,
      element("p", { className: "hint", text: parameter.description }),
    ]);
  }

  function policyDocument() {
    const document_ = { version: 1 };
    const name = $("policy-name").value.trim();
    const description = $("policy-description").value.trim();
    const assumptions = $("policy-assumptions").value.split("\n").map((s) => s.trim()).filter(Boolean);
    if (name) document_.name = name;
    if (description) document_.description = description;
    if (assumptions.length) document_.assumptions = assumptions;
    document_.rules = state.checks.map((check) => {
      const entry = { rule: check.spec.name };
      for (const parameter of check.spec.parameters) {
        const value = check.values[parameter.name];
        // Leave out settings still at their default unless the opened policy
        // spelled them out, so the policy that runs is the one that was written.
        if (!check.explicit.has(parameter.name) && isDefault(parameter, value)) continue;
        if (parameter.kind === "tolerance") {
          const name = parameter.name;
          const absolute = value.absolute.trim();
          const relative = value.relative.trim();
          const keys = check.mappings[name];
          if (keys || relative) {
            const mapping = {};
            if (absolute || (keys && keys.includes("absolute")) || !keys) {
              mapping.absolute = numberValue(check, `${name}.absolute`, absolute || "0");
            }
            if (relative) mapping.relative = numberValue(check, `${name}.relative`, relative);
            entry[name] = mapping;
          } else if (absolute) {
            entry[name] = numberValue(check, `${name}.absolute`, absolute);
          }
        } else if (parameter.kind === "columns") {
          entry[parameter.name] = [...value];
        } else if (parameter.kind === "number") {
          const text = String(value).trim();
          if (text) entry[parameter.name] = numberValue(check, parameter.name, text);
        } else if (parameter.kind === "integer") {
          const text = String(value).trim();
          if (text) entry[parameter.name] = /^\d+$/.test(text) ? Number(text) : text;
        } else if (value !== "") {
          entry[parameter.name] = value;
        }
      }
      return entry;
    });
    return document_;
  }

  async function openPolicy(file) {
    if (!file || !state.web) return;
    const text = await file.text();
    const parsed = call("read_policy", text, file.name);
    if (!parsed.ok) {
      showIssues(parsed.issues, `${file.name} has problems:`);
      setStatus("The policy file was not opened.", true);
      return;
    }
    applyPolicy(parsed.policy);
    setStatus(`Opened ${file.name} with ${parsed.policy.rules.length} check(s).`);
  }

  function applyPolicy(policy) {
    $("policy-name").value = policy.name || "";
    $("policy-description").value = policy.description || "";
    $("policy-assumptions").value = (policy.assumptions || []).join("\n");
    $("policy-assumptions").rows = Math.max(3, (policy.assumptions || []).length + 1);
    state.checks = [];
    for (const entry of policy.rules) {
      const { rule, ...values } = entry;
      const spec = state.catalog.find((item) => item.name === rule || item.rule_id === rule);
      addCheck(spec.name, values);
    }
    showIssues([]);
    renderChecks();
    refresh();
  }

  function renderTemplates() {
    $("template").replaceChildren(
      option("", "Choose a template…", true),
      ...state.templates.map((item) => option(item.name, item.title))
    );
  }

  function useTemplate(name) {
    const template = state.templates.find((item) => item.name === name);
    const notes = $("template-notes");
    if (!template) {
      notes.hidden = true;
      return;
    }
    // With a file open, the template's column names are matched to the file's
    // headers; every match is listed for the person to confirm.
    let policy = template.policy;
    let adapt = template.adapt;
    if (state.data) {
      const fit = call("suggest", JSON.stringify(state.data.columns), name).suggestions[0];
      policy = fit.policy;
      adapt = fit.adapt;
    }
    applyPolicy(policy);
    notes.replaceChildren(
      element("strong", { text: "Before relying on this template: " }),
      [...adapt, "Check the assumptions below hold for your file."].join(" ")
    );
    notes.hidden = false;
    setStatus(`Started from the "${template.title}" template.`);
  }

  function showIssues(issues, heading) {
    const box = $("policy-issues");
    if (!issues.length) {
      box.hidden = true;
      return;
    }
    box.replaceChildren(
      element("strong", { text: heading || "Please fix these before running:" }),
      element("ul", {}, issues.map((issue) => element("li", { text: issue.text })))
    );
    box.hidden = false;
  }

  /* ---------- run ---------- */

  function guarded(action) {
    return async (...args) => {
      try {
        await action(...args);
      } catch (error) {
        setStatus("Something went wrong: " + (error && error.message ? error.message : error), true);
      }
    };
  }

  function run() {
    if (!state.data) return;
    const outcome = call(
      "run",
      state.data.content,
      state.data.name,
      JSON.stringify(policyDocument()),
      state.data.sheet
    );
    if (!outcome.ok) {
      $("results").hidden = true;
      if (outcome.issues) showIssues(outcome.issues);
      setStatus(outcome.error || "The checks could not run.", true);
      return;
    }
    showIssues([]);
    state.result = outcome;
    const counts = outcome.counts;
    const banner = $("result-banner");
    banner.className = "result-banner " + (outcome.passed ? "passed" : "failed");
    banner.textContent = outcome.passed
      ? `✓ Passed: ${counts.passed} passed, ${counts.skipped} skipped.`
      : `✗ Failed: ${counts.failed} failed, ${counts.error} could not run, ${counts.passed} passed.`;
    $("report-frame").srcdoc = outcome.html;
    const input = cliArgument(state.data.name);
    const sheet = state.data.sheet ? cliArgument(state.data.sheet) : null;
    $("cli-command").textContent =
      `finassert check --config policy.yml --input ${input.text}` +
      (sheet ? ` --sheet ${sheet.text}` : "") +
      " --html report.html";
    // Names with special characters are quoted for macOS/Linux shells only.
    $("cli-note").hidden = input.plain && (!sheet || sheet.plain);
    $("results").hidden = false;
    setStatus("Checks finished. The full report is below.");
  }

  // Names made only of ordinary characters are safe inside double quotes in
  // every common shell (bash, PowerShell, cmd), so show them that way.
  const PLAIN_NAME = /^[^"$`\\%^&|<>!;'\r\n]*$/;

  function cliArgument(text) {
    const value = String(text);
    if (PLAIN_NAME.test(value)) return { text: `"${value}"`, plain: true };
    // Otherwise single-quote for POSIX shells, which stops $(...) and backticks.
    return { text: "'" + value.replace(/'/g, "'\\''") + "'", plain: false };
  }

  function download(text, name, type) {
    const url = URL.createObjectURL(new Blob([text], { type }));
    const link = element("a", { href: url, download: name });
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 0);
  }

  function baseName() {
    const name = (state.data && state.data.name) || "data";
    return name.replace(/\.[^.]+$/, "");
  }

  function refresh() {
    const ready = Boolean(state.web && state.data && state.checks.length);
    $("run").disabled = !ready;
  }

  function wireDrop(zone, input, handler) {
    input.addEventListener("change", () => handler(input.files[0]));
    zone.addEventListener("dragover", (event) => {
      event.preventDefault();
      zone.classList.add("dragging");
    });
    zone.addEventListener("dragleave", () => zone.classList.remove("dragging"));
    zone.addEventListener("drop", (event) => {
      event.preventDefault();
      zone.classList.remove("dragging");
      handler(event.dataTransfer.files[0]);
    });
  }

  wireDrop($("data-drop"), $("data-file"), guarded(openData));
  $("sheet-select").addEventListener("change", guarded(async () => {
    if ($("sheet-select").value) showData($("sheet-select").value);
  }));
  $("policy-file").addEventListener("change", guarded(async () => {
    await openPolicy($("policy-file").files[0]);
    $("policy-file").value = "";
  }));
  $("template").addEventListener("change", guarded(async () => useTemplate($("template").value)));
  $("add-check-button").addEventListener("click", () => addCheck($("add-check").value));
  $("run").addEventListener("click", guarded(run));
  $("download-html").addEventListener("click", () =>
    download(state.result.html, `${baseName()}-report.html`, "text/html"));
  $("download-json").addEventListener("click", () =>
    download(state.result.artifact_json, `${baseName()}-report.json`, "application/json"));
  $("download-policy").addEventListener("click", () =>
    download(state.result.policy_yaml, "policy.yml", "application/yaml"));

  boot();
})();
