# 0002 — Financial invariants: contracts

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

- Every public rule defines equation, applicability, signs, units, null/empty behavior,
  and tolerance basis.
- Missing columns or incompatible units error; financial invariant violations fail.
- Mixed currencies require explicit grouping or conversion provenance.

Unresolved implementation gaps and contract decisions are tracked in
[tasks.md](tasks.md). Changes to outcomes, IDs, tolerance mathematics, serialization, or
row identity require a spec amendment and migration note.

## Verified reconciliation contract — 2026-11-13

Current main already exports `cash_reconciles` and `nav_reconciles`; no duplicate
rule API is introduced by this delivery. Cash requires an explicit positive or
negative outflow sign. Summary balances/flows use exact uniqueness; transaction
balances use FIRST/LAST with an explicit ordering column, and flows sum.

NAV sums signed market-value lines; liabilities and shorts are negative input
lines. Reported NAV may be absent on some rows, but present values must agree
within a group. Currency is a caller-selected grouping column, never inferred or
converted. Callers select one valuation date or include it in `group_by`.

Tolerance is inclusive and expressed in the input currency's major units. Empty
populations skip. Missing financial values fail by default; skip applies only to
blanks, and non-numeric corruption still fails. Ignoring rows is prohibited for
reconciliation. Diagnostic populations retain exact totals and bounded examples.

The shared suite verifies these contracts across mappings, records, pandas,
the explicit pandas adapter, TableSource, and actual workbook input. Existing
properties cover row-order invariance, broken-group isolation, and NAV identities.
