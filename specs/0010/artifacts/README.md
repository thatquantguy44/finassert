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

## Optimization decision

Profiles identify scalar scans/numeric classification in allocation/nonnegative
checks and group collection in grouped checks. Dense negative inputs allocate
substantially more temporary Python memory than sparse failures despite the same
20-example output cap. The next candidate is bounded sampling while retaining
full counts during evaluation, verified against the reference results. No batch,
vectorized, or concurrent execution API is introduced by these baselines.
