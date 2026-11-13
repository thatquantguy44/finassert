# 0009 — Property-based testing: tasks

[Spec](spec.md) · [Plan](plan.md) · [Tasks](tasks.md) · [Roadmap](roadmap.md) ·
[Contracts](contracts.md) · [Handoff](handoff.md) · [Agent instructions](AGENTS.md)

Baseline recorded 2026-11-13. Checked items identify existing implementation, not full
acceptance certification.

## Existing baseline

- [x] A bounded Decimal normalized-allocation property exists.
- [x] CI includes Python 3.11-3.13 test jobs.

## Remaining work, in order

- [ ] Create shared bounded financial-numeric, grouped-record, null, and duplicate-label
  strategies.
- [ ] Add exact tolerance-boundary and scaling properties.
- [ ] Add cash/NAV identity properties as 0002 is promoted.
- [x] Add cross-adapter equivalence properties with 0004 and Excel header/row-label
  properties with 0013.
- [ ] Define explicit offline Hypothesis profiles and retain named regressions for fixed
  defects.
- [x] Add unit/FX round trips after 0008.

Record evidence in [handoff.md](handoff.md) before checking off work.
