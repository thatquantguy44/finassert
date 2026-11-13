# 0013 — Excel workbook integration: contracts

[Spec](spec.md) · [Plan](plan.md) · [Tasks](tasks.md) · [Roadmap](roadmap.md) ·
[Contracts](contracts.md) · [Handoff](handoff.md) · [Agent instructions](AGENTS.md)

[spec.md](spec.md) is the normative requirements source. This file indexes the contracts
and review focus; it does not introduce a second definition.

## Contract references

- [Public API](spec.md#public-api-design)
- [Data contracts](spec.md#data-contracts)
- [Failure semantics](spec.md#failure-semantics)
- [Acceptance criteria](spec.md#acceptance-criteria)

## Review focus

- Worksheet row numbers remain default labels, and reading never modifies the source
  workbook.
- Cached values are not recalculated; an unreadable or uncached formula region cannot
  pass silently.
- Error markers are distinct from nulls; Decimal report values and formula-like strings
  are written as text.

## Migration note — 2026-11-13

Formula detection now precedes trailing blank-row removal, so an uncached final
formula cannot disappear. `ExcelError` is a dependency-free `CellError` marker;
requesting its column through rule extraction raises an evaluation error naming
the column and row. Direct `WorkbookSource.column` reads still expose the marker.
Only selected columns are evaluated. Main's existing `parse_xlsx` and selected
range APIs retain their documented error-text behavior for compatibility.

Unresolved implementation gaps and contract decisions are tracked in
[tasks.md](tasks.md). Changes to outcomes, IDs, tolerance mathematics, serialization, or
row identity require a spec amendment and migration note.
