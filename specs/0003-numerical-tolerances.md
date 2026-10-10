# 0003 — Numerical tolerances

**Status:** Implemented (initial)

## Problem statement

Exact equality is unsuitable for many computations, while implicit rounding and
float coercion can conceal financially meaningful discrepancies.

## Motivation and use cases

Reconciliations, allocation totals, returns, and converted values need reviewable
materiality semantics across float, integer, and Decimal inputs.

## Goals

Provide explicit nonnegative absolute and relative tolerances, inclusive
boundaries, Decimal preservation, and predictable non-finite behavior.

## Non-goals

Global rounding, significant-figure policy, unit conversion, arbitrary precision
float libraries, and automatic tolerance selection are excluded.

## Proposed architecture

`Tolerance` is immutable. Values are close exactly when
`abs(a-e) <= absolute + relative * max(abs(a), abs(e))`. If either operand is
Decimal, other numeric operands and tolerances convert through decimal strings;
Decimal is never converted to binary float.

## Public API design

```python
Tolerance(absolute=Decimal("0.01"), relative=Decimal("0.0001")).is_close(a, e)
```

A numeric rule parameter is shorthand for absolute-only tolerance.

## Data contracts

Supported scalars are `int`, `float`, and `Decimal`, excluding booleans. Tolerance
components are finite and nonnegative. Serialization preserves Decimal as text.

## Financial and numerical edge cases

The boundary is inclusive. NaN and positive/negative infinity never compare
close, including infinity to itself. Signed zero compares normally. Relative
scale uses the larger operand magnitude and is symmetric.

## Failure semantics

Invalid configuration raises immediately. Non-finite observations normally
produce a rule failure; an unsupported object produces failure or evaluation
error according to the rule's documented input contract.

## Implementation milestones

1. Scalar comparisons. 2. Rule integration and Decimal tests. 3. Unit-aware
materiality policies after 0008. 4. Optional array kernels after benchmarks.

## Acceptance criteria

Boundary tests pass exactly; mixed Decimal/int/float avoids Decimal-to-float
conversion; invalid tolerance construction fails; no global data rounding occurs.

## Testing requirements

Test zero, boundary ± one representable step, negative values, large magnitudes,
mixed numeric types, NaN, infinities, signed zero, and invalid configuration.

## Dependencies on other specifications

Consumed by 0001, 0002, 0005, and 0008; optimized only under 0010.

## Explicit deferred work

ULP comparison, configurable Decimal contexts, arrays, uncertainty propagation,
and currency-specific materiality defaults are deferred.
