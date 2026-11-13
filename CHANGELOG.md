# Changelog

All notable changes will be documented here. The project follows Keep a Changelog
and intends to use Semantic Versioning after the public API stabilizes.

## [Unreleased]

### Changed

- Organized specifications into numbered workspaces with dedicated spec, plan,
  tasks, roadmap, agent instructions, contracts, and handoff files; added a
  reusable template for future specs. Existing specification requirements are
  unchanged.

### Added

- Dependency-free core validation engine and structured reports.
- Portfolio weight-sum and nonnegative-value rules.
- Decimal-aware absolute and relative tolerance utility.
- Mapping, row-record, and optional pandas support.
- Typed grouped mappings with explicit sum, first, last, and uniqueness
  aggregation policies.
- Optional `finassert.excel.read_workbook` (`excel` extra) exposing a worksheet
  as a `ColumnSource` with worksheet row labels.
- Custom callable rules, registry, text/JSON reporting, tests, documentation, and
  implementation specifications.
