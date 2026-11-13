# 0010 — Performance and batch validation: tasks

[Spec](spec.md) · [Plan](plan.md) · [Tasks](tasks.md) · [Roadmap](roadmap.md) ·
[Contracts](contracts.md) · [Handoff](handoff.md) · [Agent instructions](AGENTS.md)

Baseline recorded 2026-11-13. Checked items identify existing implementation, not full
acceptance certification.

## Existing baseline

A scalar corpus, isolated measurements, profiles, retained 48-case baseline and
bounded scalar diagnostic evaluation are implemented. Multi-rule measurement and
private one-column sharing are implemented; batch APIs remain proposed.

## Remaining work, in order

- [x] Create a reproducible synthetic corpus and scalar baselines recording hardware,
  software, shape, dtypes, and group skew.
- [x] Measure cold/warm runtime and peak memory for allocation and nonnegative rules.
- [x] Profile materialization and diagnostic allocation before selecting optimization
  work.
- [x] Count every failure while sampling diagnostic prefixes during evaluation,
  including zero caps and nested/grouped populations, without changing reports.
- [x] Capture scalar-reference parity and rerun all 48 benchmarks; retain the
  memory comparison and investigate timing outliers. See [evidence](handoff.md).
- [x] Benchmark policies of 1/10/50 rules sharing columns on mapping/pandas inputs.
- [x] Retain extraction counts/time and validation peak-memory measurements.
- [x] Implement private shared reads within one check if measurements justify them.
- [x] Verify complete report parity, Decimal behavior, row identity and per-rule
  unit/FX provenance for shared and scalar execution.
- [ ] Prototype vector kernels only if measurements justify them.
- [ ] Require reference-result parity and deterministic reduction before any batch or
  parallel API is public.

Record evidence in [handoff.md](handoff.md) before checking off work.
