# Scalar validation baseline — 2026-11-13

The [retained JSON artifact](baseline-2026-11-13.json) contains 48 reference cases:
1,000/10,000/100,000 rows, float/Decimal, mapping/pandas, and four deterministic
populations. Allocation and skewed grouped allocations pass; sparse and dense
nonnegative cases deliberately fail. Diagnostic examples are capped at 20.

Reproduce from the repository root after installing the development environment:

```bash
PYTHONPATH=src .venv/bin/python scripts/benchmark_validation.py \
  --sizes 1000 10000 100000 --repeats 3 \
  --output specs/0010/artifacts/baseline-2026-11-13.json
```

Each case runs in a fresh process. First-call validation time and three warm
measurements exclude input construction. Separate runs collect tracemalloc and
cProfile evidence so profiling overhead does not contaminate the timing samples.
Peak RSS covers the whole worker, including imports and input construction;
tracemalloc covers Python allocations during validation only. Group skew places
90% of rows in one group and distributes the remainder across up to 100 groups.
The runner currently measures RSS on macOS/Linux.

All repeated result fingerprints match, and mapping/pandas results match for each
size/domain/case. The artifact records Python/package/platform/CPU information,
the pre-commit revision and dirty flag, and an exact runtime-plus-runner source
SHA-256 digest. That digest was verified against the delivered source. The dirty
flag records collection before the benchmark commit, not an omitted code state.

## Inspectable measurements

The machine was arm64 macOS 26.5.1, CPython 3.11.17, pandas 3.0.6, with 15 logical
CPUs. These are environment-specific observations, not speedup claims or service
objectives. The table shows 100,000-row mapping cases; the JSON includes every
adapter/size, individual timing sample, RSS measurement, and CPU profile.

| Case | Float median ms | Decimal median ms | Float Python peak MiB | Decimal Python peak MiB |
|---|---:|---:|---:|---:|
| `allocation` | 32.15 | 28.65 | 6.86 | 6.86 |
| `nonnegative_sparse` | 34.16 | 37.24 | 4.76 | 4.76 |
| `nonnegative_dense` | 37.90 | 42.50 | 22.88 | 22.88 |
| `grouped_skew` | 90.81 | 94.52 | 9.14 | 9.14 |

## Baseline optimization decision

Profiles identify scalar scans/numeric classification in allocation/nonnegative
checks and group collection in grouped checks. Dense negative inputs allocate
substantially more temporary Python memory than sparse failures despite the same
20-example output cap. The selected next candidate was bounded sampling while retaining
full counts during evaluation, verified against the reference results. No batch,
vectorized, or concurrent execution API is introduced by these baselines.

## Bounded diagnostic evaluation

The [optimized 48-case artifact](bounded-diagnostics-2026-11-13.json) uses the
same corpus, sizes, adapters, numeric domains, cap, and instrumentation as the
original baseline. All 48 complete report fingerprints match their reference;
repeated calls and cross-adapter fingerprints also match. The environment is
unchanged. The source digest identifies the measured runtime and benchmark runner
exactly; revision `5ec9959` plus the dirty flag identifies the branch's pre-commit
state.

Reproduce the optimized corpus without overwriting the original baseline:

```bash
PYTHONPATH=src .venv/bin/python scripts/benchmark_validation.py \
  --sizes 1000 10000 100000 --repeats 3 \
  --output specs/0010/artifacts/bounded-diagnostics-2026-11-13.json
```

100,000-row mapping observations (before → after):

| Case | Float median ms | Decimal median ms | Float Python peak MiB | Decimal Python peak MiB |
|---|---:|---:|---:|---:|
| `allocation` | 32.15 → 27.93 | 28.65 → 27.29 | 6.86 → 5.34 | 6.86 → 5.34 |
| `nonnegative_sparse` | 34.16 → 19.59 | 37.24 → 35.28 | 4.76 → 4.58 | 4.76 → 4.58 |
| `nonnegative_dense` | 37.90 → 26.18 | 42.50 → 33.24 | 22.88 → 4.58 | 22.88 → 4.58 |
| `grouped_skew` | 90.81 → 107.81 | 94.52 → 94.46 | 9.14 → 9.14 | 9.14 → 9.14 |

Dense-failure Python peak fell **80.0%** for both numeric domains. Sparse and
dense failures now have the same validation peak: diagnostic retention depends
on the cap rather than the number of failures. Both still materialize input
columns/labels; numeric reductions and grouping retain necessary state. These
measurements do not establish constant memory for the whole validator.

### Grouped timing follow-up

The slower float grouped median above prompted a
[retained paired check](grouped-timing-check-2026-11-13.json): three pairs of fresh
reference/optimized processes, alternating execution order, with nine warm
repeats per process. Input construction is excluded; memory/CPU profiling remain
separate. The reference source digest was checked against the original baseline.
All six workers return the same report fingerprint.

| Implementation | Worker medians ms | Median of all 27 warm samples ms |
|---|---|---:|
| Reference | 100.37, 113.21, 100.32 | 102.62 |
| Bounded | 93.03, 97.13, 93.08 | 93.20 |

This follow-up does not show a sustained grouped regression. Timing variability
is visible in the retained samples; no deadline or universal speedup is claimed.
To repeat a pair with the unchanged worker, extract the merged reference and use
its source path, then the current source path. Repeat three times, reversing
reference/current order for the middle pair:

```bash
reference_dir=$(mktemp -d)
git archive 5ec995984037f26255ee10895b4d4bb37838a179 src | tar -x -C "$reference_dir"
PYTHONPATH="$reference_dir/src" PYTHONHASHSEED=0 .venv/bin/python scripts/benchmark_validation.py \
  --worker --sizes 100000 --case grouped_skew --domain float --adapters mapping --repeats 9
PYTHONPATH=src PYTHONHASHSEED=0 .venv/bin/python scripts/benchmark_validation.py \
  --worker --sizes 100000 --case grouped_skew --domain float --adapters mapping --repeats 9
```

### Correctness and retention evidence

[Reference parity tests](../../../tests/integration/test_bounded_diagnostics.py)
compare 661 pre-optimization scenarios on both mapping and pandas inputs (1,322
comparisons). The [reference fixture](../../../tests/fixtures/bounded-diagnostics-reference.json)
was captured from `5ec9959` before runtime changes. Fingerprints cover direct rule
results/exceptions and complete normalized reports: messages, values, row labels,
counts, truncation flags, and diagnostics. Cases include caps 0/1/20, Decimal and
float, empty inputs, null-policy precedence, invalid tails, late blank group keys,
duplicate-key order, duplicate composite row labels, stable ranked turnover ties,
and a numerical error after the sample fills.

[Retention tests](../../../tests/unit/test_bounded_samples.py) use weak references
to verify that only the sampled observations remain alive after 10,000 additions,
including cap zero. Exact-boundary tests distinguish empty, full and truncated
populations. The complete suite passes 2,144 tests; performance assertions remain
outside correctness tests.

## Shared column reads

The [pre-change reference](shared-reads-reference-2026-11-13.json) and
[optimized corpus](shared-reads-optimized-2026-11-13.json) each contain 24 cases:
1,000/100,000 rows × 1/10/50 rules × float/Decimal × mapping/pandas. Policies
alternate nonnegative, range and sum-to-one checks over the same column. Every
case passes; complete report fingerprints match across both implementations,
both adapters and all repeated/instrumented calls. Rule count remains part of
the fingerprinted report; comparisons are between identical policy shapes.

The reference was collected before runtime changes from merged PR #18
(`28388d7`), with the new runner in the working tree. The optimized artifact
records the same base revision and a dirty flag; each source digest identifies
the exact runtime modules plus `scripts/benchmark_shared_reads.py`. Old artifacts
remain unchanged. Both use CPython 3.11.17, arm64 macOS 26.5.1, pandas 3.0.6 and
15 logical CPUs. Input construction is excluded. First/warm timing, tracemalloc,
and cProfile use separate calls. RSS covers the whole process.

Reproduce the reference by running this runner against the runtime source from
`28388d7`, before applying the optimization; reproduce the optimized corpus on
this branch. The private uncached mode also remains available for current-source
comparisons:

```bash
PYTHONPATH=src .venv/bin/python scripts/benchmark_shared_reads.py \
  --sizes 1000 100000 --rule-counts 1 10 50 --repeats 3 \
  --execution scalar --output /tmp/shared-reads-scalar.json
PYTHONPATH=src .venv/bin/python scripts/benchmark_shared_reads.py \
  --sizes 1000 100000 --rule-counts 1 10 50 --repeats 3 \
  --execution shared --output /tmp/shared-reads-shared.json
```

### Extraction and memory

The table shows 100,000-row cases. Extraction time is **profiled cumulative CPU
wall time in the raw materializer**, including list/label creation; profiler
overhead applies and these values are not ordinary validation timings. The JSON
also retains uninstrumented first/warm validation timings and top CPU functions.

| Rules | Domain | Adapter | Materializations before → after | Profiled extraction ms before → after | Python peak MiB before → after |
|---:|---|---|---:|---:|---:|
| 1 | float | mapping | 1 → 1 | 0.74 → 0.79 | 4.572 → 4.573 |
| 1 | float | pandas | 1 → 1 | 1.05 → 1.75 | 6.861 → 6.862 |
| 1 | decimal | mapping | 1 → 1 | 0.76 → 0.72 | 4.572 → 4.573 |
| 1 | decimal | pandas | 1 → 1 | 0.70 → 0.73 | 4.573 → 4.573 |
| 10 | float | mapping | 10 → 1 | 5.89 → 0.62 | 5.346 → 5.344 |
| 10 | float | pandas | 10 → 1 | 11.05 → 1.16 | 7.636 → 7.633 |
| 10 | decimal | mapping | 10 → 1 | 7.33 → 0.58 | 5.347 → 5.345 |
| 10 | decimal | pandas | 10 → 1 | 8.54 → 1.13 | 5.348 → 5.345 |
| 50 | float | mapping | 50 → 1 | 31.98 → 0.74 | 5.380 → 5.380 |
| 50 | float | pandas | 50 → 1 | 57.28 → 1.16 | 7.680 → 7.669 |
| 50 | decimal | mapping | 50 → 1 | 29.58 → 0.75 | 5.383 → 5.382 |
| 50 | decimal | pandas | 50 → 1 | 36.80 → 1.63 | 5.394 → 5.383 |

Fifty shared-column rules materialize once rather than fifty times (98% fewer
materializations). Validation peak remains effectively flat: only one column is
retained, and a different column evicts it. The prototype does not cache numeric
classification or aggregation, which still dominate profiles. This reduces
repeated allocation work without claiming constant memory for the whole check.

### Timing variability and decision

Separate matrix runs show mixed timing differences, including slower cases.
The final
[alternating within-process check](shared-reads-alternating-2026-11-13.json)
warms both paths and alternates execution order over seven timed pairs in each
fresh adapter/domain worker. GC, construction and serialization are excluded;
there is no profiler or tracemalloc. Process CPU time separately excludes time
the process is not scheduled. Every report fingerprint matches the original
50-rule corpus. Its source digest includes runtime modules and both runners.

100,000 rows and 50 rules, medians of seven samples per mode:

| Domain | Adapter | Scalar wall ms | Shared wall ms | Wall change | Scalar CPU ms | Shared CPU ms |
|---|---|---:|---:|---:|---:|---:|
| float | mapping | 1248.31 | 1186.03 | -4.99% | 1191.08 | 1150.84 |
| float | pandas | 1289.26 | 1201.38 | -6.82% | 1244.09 | 1153.27 |
| decimal | mapping | 1485.62 | 1378.36 | -7.22% | 1372.55 | 1309.94 |
| decimal | pandas | 1399.90 | 1407.26 | +0.53% | 1361.75 | 1338.83 |

The scoped prototype ships: the alternating check shows useful wall-time gains
in three workloads (5.0–7.2%), with Decimal pandas essentially neutral (+0.53%
wall time, -1.68% CPU time). These are local measurements, not universal speedup
or deadline guarantees. Retaining all raw runs makes variability inspectable.

```bash
PYTHONPATH=src .venv/bin/python scripts/benchmark_shared_timing.py \
  --repeats 7 --output /tmp/shared-reads-alternating.json
```

### Scope and parity

The ordinary `check` signature is unchanged. Only consecutive exact built-in
nonnegative, range and weights rules share one retained column, for plain
dictionaries with list/tuple columns and native pandas frames, with a list/tuple
of rules. Custom rules/subclasses and custom tolerance/configuration subclasses clear
sharing. Overloaded/custom scalar cells or labels suspend reuse for the rest of
the call after one inspection. Lazy rule iterables, one-shot
columns, arbitrary ColumnSource and MoneySource use scalar reads. Context-reset
hooks clear values before running. Nested/concurrent calls and strict exceptions
release or isolate state; nothing survives the call. Unsupported inputs keep
existing behavior and custom rules receive the original input object.

[Captured reference tests](../../../tests/integration/test_bounded_diagnostics.py)
now check each of 661 scenarios on both adapters as standalone and repeated
policies (2,644 tests), including full reports and direct results/exceptions.
[Focused sharing tests](../../../tests/unit/test_shared_reads.py) verify actual
read counts, one-column eviction, mutations across rules/calls, lazy iterables,
subclasses, errors, Decimal boundaries, unusual labels, nested/concurrent checks,
and per-rule FX provenance. Context-reset and custom tolerance/cell mutation regressions were found and
fixed before final measurement. [Runner smoke coverage](../../../tests/integration/test_benchmarks.py)
checks 1/10/50-rule read counts and scalar/shared fingerprints without timing
thresholds. Full regression: **3,484 tests pass**.
