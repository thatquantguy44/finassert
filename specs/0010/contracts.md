# 0010 — Performance and batch validation: contracts

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

- The scalar result contract remains the reference for every optimization.
- Decimal behavior, rule order, total failure counts, and diagnostic bounds remain
  deterministic.
- Performance claims require retained benchmark evidence; proposed batch APIs remain
  private.

Unresolved implementation gaps and contract decisions are tracked in
[tasks.md](tasks.md). Changes to outcomes, IDs, tolerance mathematics, serialization, or
row identity require a spec amendment and migration note.

## Retained measurement contract — 2026-11-13

[artifacts/README.md](artifacts/README.md) documents the 48-case baseline and exact
reproduction command. Timings exclude input construction and instrumentation;
tracemalloc and cProfile use separate calls. RSS includes the whole worker.
Repeated and cross-adapter report fingerprints must match; no deadline or speedup
assertion is part of correctness tests. The source digest includes every runtime
Python module and the runner. Optimized execution remains proposed.
