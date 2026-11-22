# 0020 — Performance and backtest integrity roadmap

## Current milestone

Proposed. The first milestone is a monthly performance workbook and audit for
one strategy and benchmark. It delivers reference calculations, audit findings,
and a reproducible Excel-to-CLI example under [R-01 through R-05](spec.md#goals).
P-02 design and fixtures are complete; see the [decisions](decisions.md) and
[independent expected values](artifacts/fixtures/expected.json). The P-03
calculator and preflight pass AC-01/AC-02 fixture acceptance. P-04 implements
the confirmed composite audit rule, fixture-backed starter policy and full
configured/effective parameter export in JSON, HTML and XLSX. Specifications
0005 and 0007 own the additive artifact contract. P-05 remains the next spec
task; full AC-04/AC-05 Excel acceptance is still open.

## Next milestone

Proposed. Add point-in-time decision-log and historical-universe checks, with
a worked walk-forward example that records the evidence it uses.

## Later milestones

Proposed. Validate minimum-variance inputs and submitted weights, then provide
a reference Python implementation that computes and independently audits a
candidate. Follow with richer constraints and cost modeling as use cases justify
them. See [implementation milestones](spec.md#implementation-milestones).

## Deferred scope

See [explicit deferred work](spec.md#explicit-deferred-work). The
[master handoff](../../docs/handoff.md#next-up) owns project-wide sequencing.
