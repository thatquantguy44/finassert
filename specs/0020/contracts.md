# 0020 — Performance and backtest integrity contracts

[spec.md](spec.md) is the normative source for the proposed contracts.

- [Architecture](spec.md#proposed-architecture) and [public interfaces](spec.md#public-api-design)
  cover reference calculation, rule registration, and audit entry points.
- [Data contracts](spec.md#data-contracts) cover period coverage, row identity,
  assumptions, and reference calculations.
- [Numeric edge cases](spec.md#financial-and-numerical-edge-cases) and
  [failure semantics](spec.md#failure-semantics) cover applicability and outcomes.
- [Acceptance criteria](spec.md#acceptance-criteria) define evidence for delivery.

Review the policy assumptions round-trip, source row identity, unit conversion,
and the calculation/audit boundary before publishing interfaces. Changes to
existing contracts require an amendment and migration note in the owning spec.
