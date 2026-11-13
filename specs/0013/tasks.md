# 0013 — Excel workbook integration: tasks

[Spec](spec.md) · [Plan](plan.md) · [Tasks](tasks.md) · [Roadmap](roadmap.md) ·
[Contracts](contracts.md) · [Handoff](handoff.md) · [Agent instructions](AGENTS.md)

Baseline recorded 2026-11-13. Checked items identify existing implementation, not full
acceptance certification.

## Existing baseline

- [x] The optional excel extra and initial read_workbook/WorkbookSource implementation
  exist.
- [x] Reader tests cover numeric conversion, selected headers, basic errors, row labels,
  and file non-mutation.

## Remaining work, in order

- [x] Detect uncached formulas before dropping trailing blank rows; review reproduced a
  formula-only final row becoming empty input and passing non_negative.
- [x] Make Excel error cells yield the specified evaluation-error behavior instead of
  ordinary rule failure.
- [ ] Run the full shared 0004 adapter contract suite over WorkbookSource.
- [ ] Add coverage for cached formulas, workbook epochs, hidden/merged regions, and
  header/row-label properties.
- [ ] Implement write_report_xlsx Summary/Results sheets with Decimal text and
  formula-injection protection.
- [ ] Resolve hidden-region reporting and totals-row options; max_row already bounds the
  selected region.
- [ ] Add CLI workbook flags after 0007; add a Diagnostics sheet after 0005 defines
  structured observations.

Record evidence in [handoff.md](handoff.md) before checking off work.
