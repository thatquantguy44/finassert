# 0001 — Core validation engine

**Status:** Implemented (initial)

## Problem statement

Financial checks need a shared execution contract; ad hoc booleans cannot explain
failure, distinguish broken evaluation, or support durable automation.

## Motivation and use cases

Research notebooks, ETL jobs, optimizers, and CI need the same deterministic way
to run several invariants and retain inspectable evidence.

## Goals

- Execute typed rules in caller order without changing data.
- Represent passed, failed, errored, and skipped evaluations distinctly.
- Aggregate results deterministically and support strict exception behavior.

## Non-goals

Parallel execution, policy configuration, dependency injection, caching, and
distributed scheduling are not core-engine responsibilities.

## Proposed architecture

`Rule` is a structural protocol. `check` iterates the supplied iterable once and
calls each rule once. Results are immutable dataclasses. Default mode captures an
exception as an error result and continues; strict mode raises a
`RuleEvaluationError` chained from the cause.

## Public API design

```python
report = check(data, rules, raise_on_error=False)
```

Rules expose `rule_id`, `name`, `severity`, and `evaluate(data)`. Execution order
and result order are identical. A result with a mismatched identifier is an error.

## Data contracts

`ValidationResult` contains identifier, name, outcome, severity, message,
observed, expected, tolerance, and metadata. `ValidationReport.results` is a
tuple. `passed` is true only when every result is passed or skipped. An empty set
passes vacuously.

## Financial and numerical edge cases

The engine performs no numeric coercion, rounding, normalization, currency
conversion, dataframe copying, or null interpretation. Rules own those semantics.

## Failure semantics

A violated invariant is `failed`; inability to evaluate is `error`; a declared
precondition that prevents evaluation is `skipped`. Errors never pass. Severity
classifies impact but does not alter truth.

## Implementation milestones

1. Immutable models and enums. 2. Sequential engine and strict mode. 3. Context
and policy hooks only after a separate approved specification.

## Acceptance criteria

Order is stable; rules execute once; empty semantics are documented; captured
exceptions retain type information; core imports with no optional dependencies.

## Testing requirements

Test every outcome, empty and multiple rule sets, exception capture and chaining,
identifier mismatch, serialization, ordering, and input non-mutation.

## Dependencies on other specifications

Tolerance behavior is 0003; diagnostics are 0005; registry behavior is 0006;
batch execution is 0010.

## Explicit deferred work

Async rules, cancellation, retries, parallelism, dependency graphs, and policy
severity thresholds are deferred.
