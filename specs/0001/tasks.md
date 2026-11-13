# 0001 — Core validation engine: tasks

[Spec](spec.md) · [Plan](plan.md) · [Tasks](tasks.md) · [Roadmap](roadmap.md) ·
[Contracts](contracts.md) · [Handoff](handoff.md) · [Agent instructions](AGENTS.md)

Baseline recorded 2026-11-13. Checked items identify existing implementation, not full
acceptance certification.

## Existing baseline

- [x] Initial result models, outcome/severity enums, and sequential engine exist.
- [x] Strict exception mode and captured evaluation errors exist.

## Remaining work, in order

- [ ] Audit acceptance coverage for execute-once behavior, identifier mismatch,
  exception chaining, and every outcome.
- [ ] Review whether nested result metadata satisfies the documented immutability
  contract.

Record evidence in [handoff.md](handoff.md) before checking off work.
