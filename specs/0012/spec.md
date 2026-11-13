# 0012 — Seven-priority delivery

**Status:** In progress; tracking workspace, not a new runtime API

## Scope

Deliver the seven priorities from the 2026-11-13 implementation review in order.
The branch is `feature/seven-priority-roadmap`. Existing numbered specs remain
canonical for their public contracts; this workspace records integration order,
completion gates, and evidence.

1. Excel input correctness: trailing uncached formulas and error-cell outcomes.
2. Adapter contract enforcement and a shared cross-adapter test suite.
3. Bounded diagnostics, source row identity, and versioned strict JSON artifacts.
4. Public cash and NAV reconciliation with explicit financial preconditions.
5. Excel report output and a strict, noninteractive policy-driven CLI.
6. Typed money/ratio units and explicit direct FX with provenance.
7. Reproducible runtime and peak-memory baselines before optimization.

## Acceptance criteria

Each gate has implementation, documented contracts/migration notes, focused
regression or property coverage where appropriate, and passing project checks.
Benchmarks retain the corpus definition, environment, command, and measured
results. No deferred vectorization or concurrency is implied by baseline work.

## Dependencies on other specifications

- [0002](../0002/spec.md): financial equations and applicability.
- [0004](../0004/spec.md), [0009](../0009/spec.md): adapters and properties.
- [0005](../0005/spec.md): diagnostics and artifact serialization.
- [0006](../0006/spec.md), [0007](../0007/spec.md): factory policies and CLI.
- [0008](../0008/spec.md): dimensions and FX provenance.
- [0010](../0010/spec.md): benchmark-first performance work.
- [0011](../0011/spec.md): workbook input and report output.

## Explicit deferred work

Hosted services, live Excel automation, live FX acquisition, Polars, Parquet
loaders, distributed execution, vectorization, and concurrency remain deferred.
The initial CLI supports JSON, CSV, and XLSX; format expansion is separate work.
