# 0010 — Performance and batch validation: handoff

[Spec](spec.md) · [Plan](plan.md) · [Tasks](tasks.md) · [Roadmap](roadmap.md) ·
[Contracts](contracts.md) · [Handoff](handoff.md) · [Agent instructions](AGENTS.md)

## Current state

- **Branch:** `feature/shared-column-reads`, from merged PR #18 (`28388d7`).
- **Latest delivered work:** All four multi-rule measurement/shared-read items.
  Private sharing retains one column across eligible consecutive built-in rules;
  custom/lazy/unit-aware inputs retain scalar behavior.
- **Evidence:** 24 reference/optimized cases preserve complete fingerprints;
  50-rule reads fall from 50 to 1, with essentially flat peak memory. Alternating
  timings show 5.0–7.2% wall gains in three workloads and neutral Decimal pandas.
  Full suite: 3,484 passed, including 2,644 captured-reference tests.
- **Next step:** Review this branch and the scoped fallbacks. Further kernels and
  public batch/concurrent APIs remain proposed.

## Entries

### 2026-11-13 — Multi-rule benchmarks and bounded shared reads

- **Branch:** `feature/shared-column-reads`, from merged PR #18 (`28388d7`).
- **Done:** Retained policies with 1/10/50 rules, two sizes, float/Decimal and
  mapping/pandas. Measured materialization calls, profiled extraction time,
  first/warm validation time, tracemalloc and RSS separately. Prototyped and
  verified private one-column sharing within an ordinary check call.
- **Decision:** Ship the scoped optimization: 50 shared-column rules read once
  instead of fifty times. Alternating uninstrumented timing pairs show 4.99%
  float mapping, 6.82% float pandas and 7.22% Decimal mapping wall gains. Decimal
  pandas is neutral (+0.53% wall, -1.68% CPU). Matrix timing variability and alternating raw samples remain retained; no universal speedup is claimed. Peak memory is flat.
- **Scope:** Exact built-in nonnegative/range/weights rules and native pandas or
  plain list/tuple-backed dictionaries; one retained column, evicted on a new
  column. Custom rules/subclasses and custom tolerances are barriers. Lazy rule iterables, one-shot
  columns, arbitrary sources and MoneySource keep scalar reads. Overloaded scalar cells/labels disable reuse. Reset hooks clear
  cached values; nested/concurrent checks and strict errors isolate/release state.
- **Verification:** 3,484 tests passed. Complete fingerprints match all 24 matrix
  cases and all timing follow-ups. 2,644 captured-reference tests check standalone
  and repeated policies. Focused tests cover Decimal, labels, errors, mutations,
  read counts, context resets and per-rule unit/FX provenance. Ruff lint/format,
  mypy (59 modules), strict docs, wheel/sdist build and isolated installed CLI/unit/FX/workbook
  flows pass.
- **Evidence:** Raw samples, exact source digests and reproduction commands are in
  [artifacts/README.md](artifacts/README.md#shared-column-reads).
- **Limits:** Numerical scans/aggregation remain dominant; public check signatures
  and report schemas are unchanged. No batch API, merge or release is included.
- **Next step:** Review the branch and scoped fallbacks before further optimization.

### 2026-11-13 — Bounded diagnostic memory during scalar evaluation

- **Branch / PR:** `feature/bounded-diagnostic-memory`, [draft PR #18](https://github.com/thatquantguy44/finassert/pull/18), from merged PR #17 (`5ec9959`).
- **Done:** Added a private count-and-prefix sample; applied it to arithmetic,
  scalar weights, shared row/group evaluators, integrity, and nested exposure /
  alignment diagnostics. Stable turnover top-five selection replaces a full
  diagnostic sort. Numeric operands and required grouping state keep their
  original order. All existing output limits and public behavior are preserved.
- **Evidence:** 661 scenarios captured from the unchanged scalar reference and
  checked on mapping and pandas inputs; 1,322 comparisons include direct
  evaluation and complete reports. Retention tests verify discarded observations
  are released. Full regression: 2,144 passed. Ruff lint/format, mypy (58 modules),
  strict docs, wheel/sdist build, and isolated installed CLI/unit/FX/workbook
  flows pass.
- **Measurement:** All 48 original benchmark report fingerprints match. At
  100,000 dense failures, peak Python validation allocations fell 80.0%, from
  22.88 to 4.58 MiB. Three alternating-order grouped timing pairs with nine warm
  repeats each show no sustained regression (reference 102.62 ms vs bounded
  93.20 ms pooled medians). Raw samples and reproduction are in
  [artifacts/README.md](artifacts/README.md).
- **Limits:** Input/label materialization and semantic aggregation state still
  scale with input size; duplicate detection retains state per distinct key.
  No public batch, vector, or concurrent API is introduced.
- **Next step:** Review the bounded-diagnostic branch, then use measured profiles
  to choose further optimizations only for demonstrated workloads.

### 2026-11-13 — Gate 7: Retained reproducible scalar timing, memory, and CPU profiles

- **Branch / PR:** `feature/seven-priority-roadmap`, [draft PR #17](https://github.com/thatquantguy44/finassert/pull/17).
- **Done:** Retained reproducible scalar timing, memory, and CPU profiles.
- **Evidence:** 48 cases across three sizes, two numeric domains, two adapters, and four populations retained; repeated/cross-adapter fingerprints and the delivered-source digest match; benchmark smoke test passed.
- **Next step:** Finish final regression, package, and draft PR verification.

### 2026-11-13 — Numbered spec workspace created

- **Branch:** `docs/spec-0011-excel`.
- **Done:** Moved the original spec verbatim from
  `specs/0010-performance-and-batch-validation.md` to `spec.md`; added plan, task,
  roadmap, contract, agent, and handoff files.
- **Not done / partial:** Runtime implementation and existing spec status are unchanged.
  Open tasks are not claimed complete.
- **Decisions:** Requirements remain canonical in `spec.md`; companion files track
  execution and evidence. Earlier project history remains in the [master
  handoff](../../docs/handoff.md).
- **Verify with:** Use [plan.md](plan.md) for baseline checks; documentation migration
  checks are recorded in the master handoff.
- **Next step:** Start with the first unchecked item in [tasks.md](tasks.md).
