# 0007 — CLI and pipeline integration: contracts

[Spec](spec.md) · [Plan](plan.md) · [Tasks](tasks.md) · [Roadmap](roadmap.md) ·
[Contracts](contracts.md) · [Handoff](handoff.md) · [Agent instructions](AGENTS.md)

[spec.md](spec.md) is the normative requirements source. This file indexes the contracts
and review focus; it does not introduce a second definition.

## Contract references

- [Public API](spec.md#public-api-design)
- [Data contracts](spec.md#data-contracts)
- [Failure semantics](spec.md#failure-semantics)
- [Acceptance criteria](spec.md#acceptance-criteria)

## Review focus

- Exit codes distinguish pass/skip, invariant failure, evaluation error,
  usage/configuration error, and I/O failure.
- Configuration is versioned, unknown keys fail, and rule factories are allowlisted.
- Evaluation artifacts use 0005 and are written atomically; no interactive prompts are
  required.

Unresolved implementation gaps and contract decisions are tracked in
[tasks.md](tasks.md). Changes to outcomes, IDs, tolerance mathematics, serialization, or
row identity require a spec amendment and migration note.

## Verified file workflow — 2026-11-13

Retain main's strict version-1 YAML/JSON policies, allowlisted factory descriptors,
Decimal-sensitive parameters, existing loaders, and exit codes 0-4. JSON and HTML
artifacts remain available. `--xlsx` adds an atomic Excel report without changing
`--output` from JSON. Explicit Excel header/last-row bounds are recorded in run
context. Errors and invariant failures still produce artifacts after evaluation;
input/configuration failures do not create a falsely passing report.
