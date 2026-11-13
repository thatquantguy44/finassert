# 0010 — Performance and batch validation: tasks

[Spec](spec.md) · [Plan](plan.md) · [Tasks](tasks.md) · [Roadmap](roadmap.md) ·
[Contracts](contracts.md) · [Handoff](handoff.md) · [Agent instructions](AGENTS.md)

Baseline recorded 2026-11-13. Checked items identify existing implementation, not full
acceptance certification.

## Existing baseline

No runtime implementation is claimed; the capability remains proposed.

## Remaining work, in order

- [ ] Create a reproducible synthetic corpus and scalar baselines recording hardware,
  software, shape, dtypes, and group skew.
- [ ] Measure cold/warm runtime and peak memory for allocation and nonnegative rules.
- [ ] Profile materialization and diagnostic allocation before selecting optimization
  work.
- [ ] Prototype vector kernels or shared column reads only if measurements justify them.
- [ ] Require reference-result parity and deterministic reduction before any batch or
  parallel API is public.

Record evidence in [handoff.md](handoff.md) before checking off work.
