# 0002 — Financial invariants: tasks

[Spec](spec.md) · [Plan](plan.md) · [Tasks](tasks.md) · [Roadmap](roadmap.md) ·
[Contracts](contracts.md) · [Handoff](handoff.md) · [Agent instructions](AGENTS.md)

Baseline recorded 2026-11-13. Checked items identify existing implementation, not full
acceptance certification.

## Existing baseline

- [x] Weight-sum and explicit nonnegative rules are public.
- [x] Current main exports public cash/NAV rules with explicit ordering and signs.

## Remaining work, in order

- [x] Specify cash-rule signs, FIRST/LAST ordering, currency/date preconditions,
  null/empty policies, and diagnostic limits.
- [x] Verify existing public cash reconciliation with adapter parity and reconciliation property
  tests.
- [x] Verify existing NAV reconciliation with explicit liability signs and
  materiality.
- [x] Current main implements initial returns and exposure rules.
- [ ] Design collateral and financing rules after their contracts are specified.

Record evidence in [handoff.md](handoff.md) before checking off work.
