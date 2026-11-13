# 0010 — Performance and batch validation: handoff

[Spec](spec.md) · [Plan](plan.md) · [Tasks](tasks.md) · [Roadmap](roadmap.md) ·
[Contracts](contracts.md) · [Handoff](handoff.md) · [Agent instructions](AGENTS.md)

## Current state

- **Branch:** `feature/bounded-diagnostic-memory`, based on merged PR #17 (`5ec9959`).
- **Latest delivered work:** Count every failure while retaining bounded diagnostic
  samples throughout built-in scalar evaluation.
- **Evidence:** 2,144 tests pass, including 1,322 complete scalar-reference
  comparisons. All 48 benchmark fingerprints match; dense 100,000-row failure
  peak fell from 22.88 to 4.58 MiB. Paired grouped timings show no sustained
  regression. See [artifacts](artifacts/README.md).
- **Next step:** Review this branch and its retained evidence before choosing
  further measured optimizations. Batch APIs remain proposed.

## Entries

### 2026-11-13 — Bounded diagnostic memory during scalar evaluation

- **Branch:** `feature/bounded-diagnostic-memory`, from merged PR #17 (`5ec9959`).
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
