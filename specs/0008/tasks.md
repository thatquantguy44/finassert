# 0008 — Financial units and currencies: tasks

[Spec](spec.md) · [Plan](plan.md) · [Tasks](tasks.md) · [Roadmap](roadmap.md) ·
[Contracts](contracts.md) · [Handoff](handoff.md) · [Agent instructions](AGENTS.md)

Baseline recorded 2026-11-13. Checked items identify existing implementation, not full
acceptance certification.

## Existing baseline

Money/Price/Notional, ratio units, direct FX, and the opt-in MoneySource adapter are implemented initially.

## Remaining work, in order

- [x] Review and specify the dimensional model and currency-code extension mechanism.
- [x] Implement immutable Money and ratio units with Decimal-preserving operations.
- [x] Implement explicit direct FX with base/quote direction, UTC as-of time, source,
  and age validation.
- [x] Integrate unit/FX provenance with adapters, financial rules, and artifacts.
- [x] Add property and boundary coverage for conversion, stale rates, bps/percent
  distinctions, and incompatible units.

Record evidence in [handoff.md](handoff.md) before checking off work.
