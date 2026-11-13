# 0005 — Reporting and diagnostics: tasks

[Spec](spec.md) · [Plan](plan.md) · [Tasks](tasks.md) · [Roadmap](roadmap.md) ·
[Contracts](contracts.md) · [Handoff](handoff.md) · [Agent instructions](AGENTS.md)

Baseline recorded 2026-11-13. Checked items identify existing implementation, not full
acceptance certification.

## Existing baseline

- [x] Text summaries, report dictionaries, and deterministic JSON formatting exist.

## Remaining work, in order

- [x] Define structured row/group observations with labels, total count, configured cap,
  and truncation flag.
- [x] Cap missing-weight diagnostics and preserve source labels for invalid values.
- [x] Specify and implement JSON-safe treatment of non-finite observations and row
  labels; a NaN pandas index currently makes to_json raise.
- [x] Define a versioned artifact envelope and caller-supplied source context for 0007.
- [x] Add golden coverage for all outcomes, unusual metadata, truncation, and exception
  sanitization.
- [ ] Design redaction hooks after the artifact and diagnostic contracts are settled.

Record evidence in [handoff.md](handoff.md) before checking off work.
