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
