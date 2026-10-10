# 0009 — Property-based testing

**Status:** Implemented (initial)

## Problem statement

Example tests miss combinations near tolerance boundaries, pathological numeric
inputs, and transformations that should preserve financial identities.

## Motivation and use cases

Allocation, reconciliation, scaling, unit conversion, and adapter equivalence all
have generative properties that reveal defects more effectively than fixtures.

## Goals

Create bounded Hypothesis strategies for financial numerics and assert allocation
consistency, reconciliation identities, scaling invariance, exact tolerance
boundaries, adapter equivalence, and safe behavior on adversarial values.

## Non-goals

Generating realistic markets, forecasting, performance benchmarking, replacing
example tests, or accepting mathematically valid but economically nonsensical data.

## Proposed architecture

Reusable strategies live under tests and generate finite Decimals with controlled
places, currencies, grouped records, and explicit invalid variants. Every property
documents its preconditions and avoids `assume`-heavy rejection.

## Public API design

This specification adds no runtime API. A representative property normalizes a
nonzero Decimal allocation and asserts that weight summation passes within a bound
derived from Decimal division precision.

## Data contracts

Strategies cap magnitudes, row counts, and decimal places. Seeds are reported by
Hypothesis. Regression examples discovered by shrinking become named unit tests
when they explain a distinct failure mode.

## Financial and numerical edge cases

Generate zeros, negatives, extreme finite magnitudes, Decimal exponents, NaN and
infinity in adversarial suites, nulls, duplicated row labels, zero denominators,
and values exactly inside/on/outside tolerance.

## Failure semantics

A property failure is a test failure with the minimal counterexample. Health-check
suppression requires justification. Flaky deadlines are disabled only for tests
whose correctness does not depend on time.

## Implementation milestones

1. Decimal normalized-allocation property. 2. Shared strategies and tolerance
properties. 3. Accounting identity and scaling properties. 4. Cross-adapter
contract suite. 5. Unit/FX round trips after 0008.

## Acceptance criteria

CI runs offline with deterministic profiles; properties have finance-specific
invariants; ranges remain computationally bounded; failures are reproducible.

## Testing requirements

Run properties on Python 3.11–3.13. Persist Hypothesis examples only as CI cache,
not required state. Include explicit regression tests for every fixed issue.

## Dependencies on other specifications

Tests 0002, 0003, 0004, and future 0008; performance properties are benchmarks
under 0010, not deadline assertions.

## Explicit deferred work

Stateful portfolio simulations, market generators, solver models, distributed
fuzzing, and statistical distribution claims are deferred.
