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

### Changed

- Missing-column errors list the available columns and suggest the closest one.
- Weight-sum results for non-numeric weights also report `invalid_rows` using
  the dataset's row labels.
