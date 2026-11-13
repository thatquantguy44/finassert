# 0010 — Performance and batch validation: tasks

[Spec](spec.md) · [Plan](plan.md) · [Tasks](tasks.md) · [Roadmap](roadmap.md) ·
[Contracts](contracts.md) · [Handoff](handoff.md) · [Agent instructions](AGENTS.md)

Baseline recorded 2026-11-13. Checked items identify existing implementation, not full
acceptance certification.

## Existing baseline

A scalar corpus, isolated measurements, profiles, and a retained 48-case baseline are implemented. Optimized batch APIs remain proposed.

## Remaining work, in order

- [x] Create a reproducible synthetic corpus and scalar baselines recording hardware,
  software, shape, dtypes, and group skew.
- [x] Measure cold/warm runtime and peak memory for allocation and nonnegative rules.
- [x] Profile materialization and diagnostic allocation before selecting optimization
  work.
- [ ] Prototype vector kernels or shared column reads only if measurements justify them.
- [ ] Require reference-result parity and deterministic reduction before any batch or
  parallel API is public.

Record evidence in [handoff.md](handoff.md) before checking off work.
