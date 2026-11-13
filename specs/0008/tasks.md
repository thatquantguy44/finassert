# 0008 — Financial units and currencies: tasks

[Spec](spec.md) · [Plan](plan.md) · [Tasks](tasks.md) · [Roadmap](roadmap.md) ·
[Contracts](contracts.md) · [Handoff](handoff.md) · [Agent instructions](AGENTS.md)

Baseline recorded 2026-11-13. Checked items identify existing implementation, not full
acceptance certification.

## Existing baseline

No runtime implementation is claimed; the capability remains proposed.

## Remaining work, in order

- [ ] Review and specify the dimensional model and currency-code extension mechanism.
- [ ] Implement immutable Money and ratio units with Decimal-preserving operations.
- [ ] Implement explicit direct FX with base/quote direction, UTC as-of time, source,
  and age validation.
- [ ] Integrate unit/FX provenance with adapters, financial rules, and artifacts.
- [ ] Add property and boundary coverage for conversion, stale rates, bps/percent
  distinctions, and incompatible units.

Record evidence in [handoff.md](handoff.md) before checking off work.
