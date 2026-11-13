# 0004 — DataFrame adapters: contracts

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

- Column values and labels have equal length, and multi-column native labels align.
- Adapters preserve dtypes, input order, duplicate labels, and caller data.
- Grouped reductions are explicitly configured. Public FIRST/LAST rules require
  `order_key`; low-level reductions retain physical ordering when no order is supplied.

## Migration note — 2026-11-13

Malformed column sources with unequal value/label lengths now raise
`InvalidDataError` before rule evaluation. Explicit `CellError` markers also raise
with row/column context. These inputs can no longer produce a false pass.

Unresolved implementation gaps and contract decisions are tracked in
[tasks.md](tasks.md). Changes to outcomes, IDs, tolerance mathematics, serialization, or
row identity require a spec amendment and migration note.
