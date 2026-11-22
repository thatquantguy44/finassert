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
- Artifacts preserve both explicitly configured policy parameters and the
  complete effective values used by evaluation, including defaults.

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

## E-05 compatibility — 2026-11-15

0016's private live bridge adds optional input.excel under artifact schema 1 and
canonical live HTML/sheet views. CLI/file artifacts do not supply this context;
their shape, rendering, atomic writes, options and exit codes remain unchanged.
No CLI provenance flag or public evaluation parameter was added.

## Policy parameter artifact amendment — 2026-11-20

Following the user's 0020 decision, each rule in an evaluation artifact exposes
explicit `parameters` and complete `effective_parameters` after registered
defaults and schema normalization. Decimal values remain exact strings. Export
these fields for pass, fail, skip, and evaluation error outcomes. Artifact
schema 1 is extended additively; input policy version 1, configured-policy
digest semantics, atomic CLI output, and exit codes are unchanged. Because all
policy parameters appear in reports, credentials must not be policy values.
See [0020 decisions](../0020/decisions.md).
