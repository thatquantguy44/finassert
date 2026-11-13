# 0002 — Financial invariants: tasks

[Spec](spec.md) · [Plan](plan.md) · [Tasks](tasks.md) · [Roadmap](roadmap.md) ·
[Contracts](contracts.md) · [Handoff](handoff.md) · [Agent instructions](AGENTS.md)

Baseline recorded 2026-11-13. Checked items identify existing implementation, not full
acceptance certification.

## Existing baseline

- [x] Weight-sum and explicit nonnegative rules are public.
- [x] A private grouped cash-reconciliation prototype exists; it is not public API.

## Remaining work, in order

- [ ] Specify cash-rule signs, FIRST/LAST ordering, currency/date preconditions,
  null/empty policies, and diagnostic limits.
- [ ] Promote cash reconciliation only after adapter parity and reconciliation property
  tests.
- [ ] Specify and implement NAV reconciliation with explicit liability signs and
  materiality.
- [ ] Design returns and exposure rules, followed by collateral and financing rules,
  after their contracts are specified.

Record evidence in [handoff.md](handoff.md) before checking off work.
