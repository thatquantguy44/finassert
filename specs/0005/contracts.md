# 0005 — Reporting and diagnostics: contracts

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

- Formatters are views over canonical results and do not change validation truth.
- Decimal precision is retained as text, and output is strict-JSON compatible.
- Diagnostic counts remain complete even when row/group details are capped.

Unresolved implementation gaps and contract decisions are tracked in
[tasks.md](tasks.md). Changes to outcomes, IDs, tolerance mathematics, serialization, or
row identity require a spec amendment and migration note.

## Migration note — 2026-11-13

Results gain an additive `diagnostics` field containing bounded collections with
`kind`, `count`, `limit`, `observations`, and `truncated`. Legacy metadata is
retained, with missing/invalid weight lists now honoring `max_violations`.
Consumers should use source row labels rather than legacy filtered positions.
NaN/infinite floats now serialize to explicit text rather than raising or
emitting invalid JSON. Artifact schema 1 and main's severity-based blocking are
preserved. Naive explicit artifact timestamps are rejected instead of assuming
the host timezone. Redaction hooks remain a separate milestone.
