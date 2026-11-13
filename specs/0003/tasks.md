# 0003 — Numerical tolerances: tasks

[Spec](spec.md) · [Plan](plan.md) · [Tasks](tasks.md) · [Roadmap](roadmap.md) ·
[Contracts](contracts.md) · [Handoff](handoff.md) · [Agent instructions](AGENTS.md)

Baseline recorded 2026-11-13. Checked items identify existing implementation, not full
acceptance certification.

## Existing baseline

- [x] Scalar absolute/relative tolerances and rule integration exist.
- [x] Initial inclusive-boundary and non-finite tests exist.

## Remaining work, in order

- [ ] Audit mixed Decimal/int/float boundaries, signed zero, and adjacent representable
  values.
- [ ] Add shared generative tolerance properties with 0009.
- [ ] Design unit-aware materiality only after 0008; consider array kernels only after
  0010 measurements.

Record evidence in [handoff.md](handoff.md) before checking off work.
