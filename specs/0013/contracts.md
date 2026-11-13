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

## Report/CLI migration note — 2026-11-13

`write_report_xlsx` is available from `finassert.excel` and `finassert.reporting`.
It writes a separate workbook atomically, with Summary, Results, and Diagnostics
sheets. Metadata and structured observations use canonical JSON; Decimal values
and formula-like text are literal strings. Unrepresentable text (over Excel's
32767-character cell limit or invalid control characters) errors before replacing
an existing report, rather than silently truncating evidence.

CLI `--output` continues to mean JSON. Use additive `--xlsx` for an Excel report
and `--header-row`/`--max-row` for an explicit worksheet region. Workbook bounds
are recorded in the artifact; cells outside the explicit region are not checked.
Report paths cannot replace the input or policy. JSON input rejects nonstandard
NaN/infinity constants; existing Python observations still serialize as text.

Unresolved implementation gaps and contract decisions are tracked in
[tasks.md](tasks.md). Changes to outcomes, IDs, tolerance mathematics, serialization, or
row identity require a spec amendment and migration note.

## Region migration note — 2026-11-13

Hidden inputs remain included by default. `hidden="reject"` / CLI `--hidden reject`
refuses hidden selected inputs. Visibility counts and capped examples are exposed
on both file sources and recorded in additive `input.workbook` context. Existing
worksheet row labels, explicit totals bounds, formula caches and epochs remain
unchanged. Merged headers and uncached header formulas now fail before evaluation
instead of accepting an ambiguous or missing name. No recalculation or skipping.
