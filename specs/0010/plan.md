# 0010 — Performance and batch validation: plan

[Spec](spec.md) · [Plan](plan.md) · [Tasks](tasks.md) · [Roadmap](roadmap.md) ·
[Contracts](contracts.md) · [Handoff](handoff.md) · [Agent instructions](AGENTS.md)

1. Establish reproducible timing and peak-memory baselines for ordinary check.
2. Profile the measured bottlenecks and choose the smallest justified private
   optimization.
3. Verify parity across numeric types and adapters before considering batch APIs or
   parallel execution.

Implementation areas:
[src/finassert/core/engine.py](../../src/finassert/core/engine.py),
[src/finassert/adapters](../../src/finassert/adapters),
[src/finassert/rules](../../src/finassert/rules).

Dependencies and acceptance requirements remain in
[spec.md](spec.md#dependencies-on-other-specifications).

Verification from the repository root:

```bash
PYTHONPATH=src .venv/bin/python -m pytest -q
```

This command covers the existing baseline. Add focused coverage for new behavior as
tasks are implemented.

## Bounded diagnostic evaluation

1. Capture the merged scalar reference results before changing evaluation.
2. Use a private count-and-prefix sample in arithmetic, scalar weights, shared
   row/group evaluators, integrity checks, and nested exposure/alignment examples.
   Track blank/invalid classification across the entire input. Keep numeric
   reduction operands and required grouping state in their existing order.
3. Compare direct and normalized results with the captured reference on mapping
   and pandas inputs, including zero caps, corrupt tails, stable ranks, duplicate
   labels/keys, null policies, and errors after sample saturation.
4. Rerun the original 48-case corpus; compare every complete report fingerprint
   and retain memory/timing evidence. Investigate timing outliers with paired
   reference/optimized runs before interpreting them.
5. Run the full suite, Ruff, mypy, strict docs, package build and installed flows.

```bash
PYTHONPATH=src .venv/bin/python -m pytest -q tests/integration/test_bounded_diagnostics.py tests/unit/test_bounded_samples.py
PYTHONPATH=src .venv/bin/python scripts/benchmark_validation.py --sizes 1000 10000 100000 --repeats 3 --output specs/0010/artifacts/bounded-diagnostics-2026-11-13.json
```

Keep the original baseline artifact unchanged. Reproduction and measured limits
are documented in [artifacts/README.md](artifacts/README.md).

## Shared column reads

1. Retain the merged scalar baseline before runtime changes, using policies of
   1/10/50 rules sharing a column on mapping/pandas and float/Decimal inputs.
   Separate construction, validation timing, tracemalloc and cProfile. Record
   extraction calls and profiled extraction time as well as whole-check costs.
2. Use measured extraction cost to decide whether a private prototype is useful.
   Start with consecutive built-in arithmetic/weight rules and one retained
   column: bound retention rather than keeping every distinct policy column.
3. Share only within one check on plain list/tuple-backed dictionaries or native
   pandas frames. Custom rules/subclasses, lazy rule iterables, arbitrary column
   sources, one-shot columns, overloaded scalars/configurations and unit-aware
   sources keep scalar behavior. Clear
   state around unsupported rules and at call exit, including exceptions.
4. Verify complete reports against uncached execution and captured pre-change
   fingerprints. Cover Decimal boundaries, unusual labels, errors, mutations
   between rules/calls, nested checks and per-rule financial-unit/FX provenance.
5. Retain optimized measurements alongside the immutable reference; ship only
   measured gains with no result regression and documented workload limits.
