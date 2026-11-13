# 0006 — Rule registry and custom rules: contracts

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

- Registries are caller-owned; duplicate registration requires explicit replacement.
- Callable results preserve rule identity and engine error semantics.
- Configuration lookup does not imply permission to load arbitrary external code.

Unresolved implementation gaps and contract decisions are tracked in
[tasks.md](tasks.md). Changes to outcomes, IDs, tolerance mathematics, serialization, or
row identity require a spec amendment and migration note.

## Verified factory boundary — 2026-11-13

Main's policy layer already separates `RuleFactorySpec`/`ParameterSpec` descriptors
from configured instances in `RuleRegistry`. `RuleCatalog` is a caller-owned
allowlist with deterministic name/ID lookup, collision checks, typed parameters,
and explicit replacement. `default_catalog()` creates a fresh built-in catalog;
policy loading rejects unknown fields and never imports user-named Python code.
The CLI and workbook workflow reuse this existing boundary.
