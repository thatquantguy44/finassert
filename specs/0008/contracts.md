# 0008 — Financial units and currencies: contracts

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

- Unlike currencies and incompatible dimensions cannot be combined implicitly.
- FX conversion is explicit and retains direction, source, and an aware UTC timestamp.
- Financial materiality remains distinct from currency minor-unit rounding.

Unresolved implementation gaps and contract decisions are tracked in
[tasks.md](tasks.md). Changes to outcomes, IDs, tolerance mathematics, serialization, or
row identity require a spec amendment and migration note.

## Initial implementation and migration note — 2026-11-13

The module is opt-in and adds no dependency or implicit coercion to existing
numeric rules. Money, Price, and Notional have distinct dimensions. Ratio values
require explicit bps/percentage/fraction conversions. Currency validation is
syntactic; `UNIT:` names explicitly extend the namespace without claiming an
active ISO assignment registry.

FX requires aware `as_of`/valuation timestamps, positive finite rates, source,
direction agreement, and an explicit maximum age. Exact age boundaries pass;
future/stale rates error. Same-currency rates must equal one. Explicit inversion
uses at least 50 Decimal digits; property tests assert round trips within a
declared tolerance rather than promising exact division for recurring ratios.

Converted quantities retain all rate records through same-dimension arithmetic.
`MoneySource` unwraps only declared, homogeneous Money columns. Unit/FX context
is reset before each rule and recorded in result metadata; later checks cannot
inherit stale provenance. More than 100 distinct rates errors instead of dropping
evidence. Typed values serialize as structured dictionaries, including every rate.
