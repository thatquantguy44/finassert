# 0017 — Canonical master handoff: contracts

[spec.md](spec.md) is the normative source. Reference contracts here instead of
maintaining conflicting definitions.

- [Public API](spec.md#public-api-design)
- [Data contracts](spec.md#data-contracts)
- [Failure semantics](spec.md#failure-semantics)
- [Acceptance criteria](spec.md#acceptance-criteria)

The master owns project status/order/pickup; each numbered spec still owns its
requirements. Older master entries and pre-activation commits remain historical.
Refresh updates generated Git context only, without auto-staging or committing.
Local author checking remains mandatory. No financial or artifact API migration.

Filesystem mode is an explicit local alternative when Git is unavailable. Its
versioned state is excluded from the project snapshot and retains the last accepted
master text plus configured file hashes. It neither invokes Git nor satisfies a
commit, push, hook or CI requirement. Missing or damaged state requires explicit,
confirmed recovery after human review.
