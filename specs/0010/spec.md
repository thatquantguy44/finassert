# 0010 — Performance and batch validation

**Status:** Scalar benchmarks and bounded diagnostic evaluation implemented; batch APIs proposed

## Problem statement

Thousands of rules or millions of observations may make scalar materialization
slow or memory-heavy, but premature concurrency can break determinism and Decimal
correctness.

## Motivation and use cases

End-of-day controls, large position books, many grouped portfolios, and historical
backfills need predictable resource use and bounded diagnostics.

## Goals

Define benchmark-first optimization, vectorized adapter kernels, streaming-safe
diagnostic caps, memory budgets, batching, and deterministic future parallelism.

## Non-goals

Claiming speedups before measurement, distributed computing in core, GPU support,
automatic cluster provisioning, and approximate validation are excluded.

## Proposed architecture

Rules may advertise an optional adapter-specific execution plan while retaining
the scalar protocol as reference semantics. A batch runner groups compatible
column reads, caps diagnostics during evaluation, and returns results in original
rule order. Parallel workers receive immutable configurations and independent data
partitions; reduction order is defined for numerically sensitive aggregates.

## Public API design

Proposed additions are `BatchOptions(max_diagnostics, memory_budget, workers=1)`
and `check_batch`. They remain private until benchmarks show a real need and the
result contract matches ordinary `check`.

## Data contracts

The initial corpus lives in `scripts/benchmark_validation.py`; retained evidence
and methodology live in this workspace's `artifacts/` directory. Each case runs
in a fresh process, with separate first/warm timing, tracemalloc, and cProfile
runs. Input construction is excluded from validation timing. Peak RSS describes
the entire worker, while tracemalloc describes validation allocations only.
The artifact records environment, revision/dirty state, exact source digest,
dataset shape, numeric domain, group skew, and repeated result fingerprints.
Mapping/pandas fingerprints must match for each corpus variant. Benchmark
runner memory/RSS collection currently targets macOS and Linux.

Execution plans declare required columns, grouping, reducibility, numeric domain,
and estimated materialization. Partial aggregate states must define associative
merge behavior; non-associative float reductions use a documented stable order.

## Bounded diagnostic evaluation

Built-in scalar rules count every failure while retaining only the configured
prefix of each diagnostic population during evaluation. A zero example limit
still produces the same outcome and complete totals. Sampling must preserve row
identity and input order, existing nested example limits, messages, observed and
expected values, severity, null-policy precedence, empty behavior, serialization,
and truncation flags. Ranked turnover examples retain their stable tie order.
Every row and group is evaluated even after its sample fills: invalid values,
aggregation errors, and numerical errors beyond the prefix must remain visible.

Numeric operands and grouping state needed to evaluate an invariant remain
available in the original reduction order. This bounds diagnostic retention, not
all input materialization or aggregation memory. Duplicate detection still keeps
state per distinct key, with bounded row examples per key; required-field column
summaries remain complete. No public API or result schema changes are required.

## Financial and numerical edge cases

Parallel summation can change float results; Decimal context may be thread-local;
group skew can exhaust memory; null masks differ by adapter; truncation must retain
total failure count even when row details are dropped.

## Failure semantics

Resource limit, worker, and adapter errors are evaluation errors with affected rule
IDs. Cancellation yields no false pass. A batch optimization that cannot preserve
reference semantics must fall back or reject execution explicitly.

## Implementation milestones

1. Reproducible benchmark corpus and scalar baselines. 2. Profile allocation and
nonnegative rules and bound diagnostic retention. 3. pandas vector kernels behind private interface. 4. Batch
column sharing. 5. Parallel prototype only if measurement justifies complexity.

## Acceptance criteria

Publish hardware/software and dataset shape with results; optimized and reference
results match; memory peak is measured; ordering stays deterministic; no marketing
performance claim appears without retained benchmark evidence.

## Testing requirements

Contract-test scalar/vector equality across sizes and dtypes; benchmark cold/warm
runs; measure peak memory; test skew, cancellation, worker errors, diagnostic caps,
and deterministic repeated execution.

## Dependencies on other specifications

Builds on 0001, 0003, 0004, and 0005; uses 0009 generators for equivalence data.

## Explicit deferred work

Distributed engines, GPU kernels, remote object stores, approximate checks,
streaming windows, autoscaling, and performance service-level objectives are
deferred until evidence and use cases exist.
