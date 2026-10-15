# Changelog

All notable changes will be documented here. The project follows Keep a Changelog
and intends to use Semantic Versioning after the public API stabilizes.

## [Unreleased]

### Added

- Dependency-free core validation engine and structured reports.
- Portfolio weight-sum and nonnegative-value rules.
- Decimal-aware absolute and relative tolerance utility.
- Mapping, row-record, and optional pandas support.
- Typed grouped mappings with explicit sum, first, last, and uniqueness
  aggregation policies.
- Custom callable rules, registry, text/JSON reporting, tests, documentation, and
  implementation specifications.
- Versioned YAML/JSON policies (`finassert.policy`) with an allowlisted rule
  catalog, plain-language rule descriptions, and diagnostics that report every
  problem with line numbers and suggested spellings.
- `finassert check` and `finassert rules` commands with documented exit codes,
  atomic report writing, and reproducible timestamps via `SOURCE_DATE_EPOCH`.
- Dependency-free CSV and JSON loaders that keep decimals exact and label rows
  as a spreadsheet does.
- Report artifacts with schema version, tool version, policy digest, and input
  context, plus self-contained, accessible HTML reports.
- Single-file browser application (`scripts/build_web.py`) that runs checks
  locally with Pyodide and exports the policy it ran, a headless-browser smoke
  test run in CI against the Pyodide CDN, and sample data and policy files.

- Excel `.xlsx` input with no dependency, in the CLI (`--sheet`) and the
  browser app, reading stored values exactly and refusing uncached formulas and
  ambiguous sheets; Parquet input through the `parquet` extra.

- Starter policy templates (`long-only-holdings`, `target-allocation`) with
  stated assumptions and adaptation notes, written by `finassert init` and
  offered in the browser app; `finassert templates` lists them.

- `finassert-assistant`, a Model Context Protocol server (`assistant` extra)
  that lets AI assistants list checks, validate policies, inspect files, and
  run checks, restricted to the folders given with `--root`.

- Grouped reconciliation rules: `cash_reconciles` (opening plus flows equals
  closing, with a required outflow sign convention, summary or transaction
  rows) and `nav_reconciles` (signed market values add up to the reported NAV),
  in the catalog, CLI, browser app, and assistant server, with
  `cash-reconciliation` and `nav-reconciliation` templates.
- `ColumnMapping.order_key` and `aggregate_ordered`: first and last values are
  taken by an explicit ordering column, never by row order.

- `weights_sum_to_one(group_by=...)` checks each portfolio of a multi-portfolio
  file; `no_duplicates` and `required_fields` check file shape; a
  `multi-portfolio-holdings` template combines them with NAV reconciliation.
- Sample `cash.csv` and `holdings.csv` files and example pages for cash
  reconciliation, NAV reconciliation, and multi-portfolio holdings; a test keeps
  each sample showing exactly its documented break.

- Valuation, return, and exposure rules: `market_value_reconciles` (quantity
  times price times an optional multiplier), `simple_return_reconciles` (with a
  required return unit), `gross_within_limit` and `net_within_limit` (per
  portfolio, optionally as a fraction of a base such as the NAV), and
  `position_within_limit` (largest single position). They are in the catalog,
  CLI, browser app, and assistant server, with `position-valuation` and
  `return-reconciliation` templates and sample files; policy files accept
  plain-number settings such as limits.

- `scripts/verify_dist.py` installs the built wheel into a fresh environment and
  runs the sample policy, checks versions and the source distribution's
  contents, and is run by CI and the release workflow, which also runs
  `twine check`; the release process is written up in `docs/releasing.md`.
  Publishing to PyPI remains off until maintainers enable it.

- Column matching: `finassert suggest` (and `suggest_templates`, the browser app,
  and the assistant's `suggest` tool) ranks the starter policies by how well
  their columns match a file's headers and proposes which header plays which
  part (`Mkt Val` for market value, `Shares` for quantity), explaining every
  match, listing ambiguous candidates instead of guessing, and writing a policy
  with the matches to confirm at the top.

- Portfolio-management rules: `in_range`, `weights_match_market_values`,
  `drift_within_band` (warns by default), `turnover_within_limit` (requires
  `sides`), and `position_rolls_forward` (requires `sell_sign`), in the catalog,
  CLI, browser app, and assistant, with a `position-rollforward` template,
  column-matching names, sample files, and docs.
- Excel add-in (initial): `scripts/build_excel.py` builds a task pane and manifest that
  read the selected cells (numbers, dates, percentages, and Excel errors read by the
  same rules as a saved workbook, with the sheet's own row numbers), run checks with the
  same engine as the browser app, and write a results sheet without changing the data.
  Tested against a stand-in for Excel in CI; not yet run in real Excel. The results sheet
  opens with a stamp (outcome, policy name and fingerprint, range checked, counts, time,
  version); checks can be saved to and loaded from a `finassert policy` sheet; a single
  selected cell uses its table; `--bundle-pyodide` carries the engine inside the add-in
  for use with no CDN; `scripts/serve_excel.py` serves the build for trials; CI runs
  Microsoft's manifest validator (informational).
- Real-Excel spike: a **Diagnostics for testers** section in the Excel task pane runs the
  spike checklist (environment, API support, security policy, network use, writing and
  reading 50,000 generated rows, the multi-portfolio template with planted breaks, the
  results sheet, saving and loading checks, and that data is unchanged) and produces a
  report to send back; `docs/design/excel-spike.md` is the runbook with manual checks.
- Severity now gates the run: a failed check set to `severity: warning` or `info`
  is reported (as a Warning in the HTML report and browser app) but does not
  fail the report or the exit code; `finassert check --fail-on warning|info`
  raises the threshold. Reports count `warnings` and `blocking_failures`.

### Changed

- **Behavior change:** `ValidationReport.passed` and `finassert check` no longer
  fail for a failed check of `warning` or `info` severity. Checks default to
  `error`, so existing policies behave as before; a check that could not run
  still fails the run at any severity.
- The private grouped cash-reconciliation prototype is replaced by the public
  `accounting.cash_reconciles` rule.
- Grouped rules treat spaces-only text as blank, read the ordering column only
  when first/last balances need it, and never let `null_policy: skip` hide
  non-numeric values. Date ties in transaction rows now say to use a unique
  sequence number or timestamp.
- Excel input treats blank text cells as empty and numeric text as numbers,
  like CSV; sheet selection problems exit with code 3 and suggest `--sheet`.
- Missing-column errors list the available columns and suggest the closest one.
- Weight-sum results for non-numeric weights also report `invalid_rows` using
  the dataset's row labels.
