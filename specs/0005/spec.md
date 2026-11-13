# 0005 — Reporting and diagnostics

**Status:** Text, JSON-compatible, artifact envelope, and HTML views implemented (initial)

## Problem statement

A validation boolean is insufficient for incident response, audit artifacts, and
machine gating; diagnostics must be useful without leaking unbounded data.

## Motivation and use cases

Humans need terminal explanations, while CI and orchestrators need stable records
containing identifiers, observations, expectations, and failure locations.

## Goals

Specify terminal and JSON output now, stable IDs and source context, bounded
failing observations, deterministic serialization, and future HTML separation.

## Non-goals

Log shipping, artifact storage, dashboards, alert delivery, PII discovery, and a
universal observability schema are not reporter responsibilities.

## Proposed architecture

Results are canonical; formatters are pure views. `to_dict` produces JSON-ready
primitives and Decimal strings. Text prints an aggregate header and failed/error
details. The artifact envelope carries a top-level `schema_version` without changing
rule IDs.

## Public API design

```python
report.summary()
report.to_dict()
to_json(report, indent=2)
```

Future report context may include run ID, source URI, as-of time, dataset version,
and configuration digest supplied by the caller—not guessed by the library.

## Data contracts

Required fields are those in 0001. Row diagnostics contain label/value pairs,
count, configured cap, and truncation flag. Metadata keys are strings; arbitrary
objects stringify rather than make serialization fail.

`check` attaches `ValidationResult.diagnostics`, a tuple of `DiagnosticCollection`
objects for rules declaring `max_violations`. Each collection has `kind`, exact
`count`, configured `limit`, bounded `observations`, and `truncated`. Kinds name
the legacy metadata collection (for example `missing_rows`, `violations`, or
`failed_groups`); scalar labels become `{"row": label}` observations. Counts are
per collection, so a blank-column observation may describe several cells. Existing
metadata keys remain available. Direct/custom results may supply collections
explicitly; arbitrary custom metadata is not interpreted without an opt-in limit.

Non-finite float values serialize as the explicit strings `NaN`, `Infinity`, or
`-Infinity`, matching Decimal text behavior. They never become JSON numeric
tokens or null. The version-1 artifact envelope already carries tool identity,
UTC generation time, caller-supplied input context, and policy digest. Explicit
generation timestamps must be timezone-aware. New diagnostic fields are additive.

## Financial and numerical edge cases

Preserve Decimal text and explicit currency/unit metadata. Do not emit NaN JSON.
Very large, sensitive, duplicated, or composite row keys require caps and caller
redaction before persistence.

## Failure semantics

Formatter failure must not change validation truth. An errored rule includes the
exception class but avoids traceback or sensitive data by default. Skips explain
the unmet precondition.

## Implementation milestones

1. Text and dictionary/JSON. 2. Versioned artifact envelope and source context.
3. Redaction hooks. 4. HTML only after accessibility and security design.

## Acceptance criteria

Output is deterministic and strict-JSON compatible; all outcomes are distinct;
diagnostics are bounded; Decimal precision is not represented as binary float.

## Testing requirements

Golden-test text and JSON, all outcomes, Decimal, composite labels, truncation,
unusual metadata, serialization determinism, and exception sanitization.

## Dependencies on other specifications

Consumes 0001 and 0003; adapter row identity comes from 0004; CLI artifacts use
0007; units come from 0008.

## Explicit deferred work

HTML is implemented initially on main. Charts, localization, remote sinks,
tracebacks, signing, encryption, and artifact retention policy remain deferred.
