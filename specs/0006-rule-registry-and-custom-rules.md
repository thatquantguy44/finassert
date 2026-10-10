# 0006 — Rule registry and custom rules

**Status:** Implemented (initial)

## Problem statement

Organizations need local invariants and discovery without mutable global state,
ambiguous names, or plugins that silently replace trusted rules.

## Motivation and use cases

Applications compose built-ins with desk policies, reuse configured instances,
and eventually resolve rules named in configuration artifacts.

## Goals

Support callable rules, explicit registration, stable namespacing, deterministic
lookup, documented collisions, and future version negotiation.

## Non-goals

Remote code loading, automatic package scanning, sandboxing, dynamic installation,
and a hosted marketplace are excluded.

## Proposed architecture

`FunctionRule` adapts a callable returning bool or a complete result. Each
`RuleRegistry` is caller-owned and maps identifier to instance. Registration
rejects duplicates unless `replace=True`; listing is sorted. No process-global
registry is populated on import.

## Public API design

```python
rule = custom_rule("acme.cash.present", "Cash exists", evaluator)
registry = RuleRegistry()
registry.register(rule)
registry.get("acme.cash.present")
```

Third parties should use an owned namespace. Built-ins reserve unqualified family
prefixes such as `portfolio` and `accounting`.

## Data contracts

Callable booleans receive the dataset once. False becomes failed; true becomes
passed. Rich evaluators return a `ValidationResult` with exactly the rule's ID.
Future registry descriptors separate factory metadata from configured instances.

## Financial and numerical edge cases

Custom rules own units, tolerances, null policy, and applicability. Registries
must not infer them or coerce configurations.

## Failure semantics

Unsupported callable return types error during evaluation. Identifier mismatch is
an engine error. Duplicate registration raises synchronously unless replacement
is explicit.

## Implementation milestones

1. Function adapter and local registry. 2. Factory descriptors and configuration
schema. 3. Entry-point discovery with allowlists. 4. Version constraints.

## Acceptance criteria

No global mutation; collision behavior is deterministic; evaluator executes once;
custom exceptions follow engine error semantics; identifiers survive reporting.

## Testing requirements

Test true/false/rich/invalid returns, thrown exceptions, duplicate and replacement
registration, sorted IDs, identifier mismatch, and independent registries.

## Dependencies on other specifications

Uses 0001 and 0005; configuration lookup supports 0007; versioned units may depend
on 0008.

## Explicit deferred work

Entry points, plugin trust policy, code signing, remote registries, hot reload,
dependency resolution, and rule schema migration are deferred.
