# 0006 — Rule registry and custom rules: tasks

[Spec](spec.md) · [Plan](plan.md) · [Tasks](tasks.md) · [Roadmap](roadmap.md) ·
[Contracts](contracts.md) · [Handoff](handoff.md) · [Agent instructions](AGENTS.md)

Baseline recorded 2026-11-13. Checked items identify existing implementation, not full
acceptance certification.

## Existing baseline

- [x] Callable rules and caller-owned instance registries exist.

## Remaining work, in order

- [ ] Audit coverage for rich/invalid callable results, duplicate/replacement
  registration, sorted IDs, and registry independence.
- [x] Specify factory descriptors and parameter schemas needed by allowlisted CLI
  configuration in 0007.
- [x] Implement factory lookup only after separating configured rule instances from
  factory metadata.

Record evidence in [handoff.md](handoff.md) before checking off work.
