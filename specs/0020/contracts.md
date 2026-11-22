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

P-02 review and the user's confirmed decisions are recorded in
[decisions](decisions.md): use one composite audit rule and preserve complete
policy parameter traceability. The version-1 policy carries typed rule
parameters and its digest identifies the configured policy. Artifacts expose
both explicitly configured `parameters` and complete resolved
`effective_parameters`, with defaults and exact Decimal text, under the additive
schema-1 contract owned by [0005](../0005/spec.md#data-contracts) and
[0007](../0007/spec.md#data-contracts). P-04 implements this contract with the
monthly audit rule. Independent source and expected values live in
[fixtures](artifacts/fixtures/expected.json).
