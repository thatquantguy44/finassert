# Tasks — treasury rules and deferred QuantMeridian integration

**Status:** Proposed implementation backlog; specification prepared.
**Updated:** 2026-10-17
**Spec:** [SPEC.md](SPEC.md) · **Plan:** [PLAN.md](PLAN.md)

Implementation tasks: **0 of 16 done**. Writing this specification is not
implementation completion. All unassigned work below has owner `unassigned`.

## Ledger protocol

Allowed states: `todo`, `in-progress`, `blocked`, `done`. Each implementation PR
updates state, actual owner, completion evidence, test results, and acceptance
coverage. A task is done only when implementation, relevant tests, documentation,
and review evidence exist. Record failures/skips rather than claiming broad
test coverage. Amend the specification with intentional contract changes.

| ID | Repository | Task | Dependencies | Acceptance | State |
| --- | --- | --- | --- | --- | --- |
| U-01 | finassert | Open proposal issue; finalize treasury IDs, API signatures, prerequisite and currency contracts | — | AC-07–09 | todo |
| U-02 | finassert | Add synthetic forecast/facility fixtures, expected scope and explicit assumptions | U-01 | AC-01–05 | todo |
| U-03 | finassert | Implement coverage and period validation, including wholly absent series | U-02 | AC-03, AC-07 | todo |
| U-04 | finassert | Implement continuity with prior/current row diagnostics | U-03 | AC-02, AC-07 | todo |
| U-05 | finassert | Implement minimum available-cash buffer | U-02 | AC-04, AC-07 | todo |
| U-06 | finassert | Implement facility identity, capacity, continuity and maturity behavior | U-03 | AC-05, AC-07 | todo |
| U-07 | finassert | Publish cash pack: existing cash identity mapping, catalogs, policies, examples and interfaces | U-04–06 | AC-01, AC-08–09 | todo |
| U-08 | finassert | Implement paired forecast-error rule and matching/vintage example | U-07 | AC-06–09 | todo |
| U-09 | finassert | Implement debt principal and issuance proceeds rules with final 0002 amendment | U-01, U-07 | AC-07–10 | todo |
| U-10 | finassert | Verify distributions; record immutable source and pack artifacts for consumers | U-07 | AC-08–09 | todo |
| Q-01 | QuantMeridian later | Migrate staged consumer spec, reinspect active repository and assign current paths/spec number | This specification exists; migration timing chosen by owner | AC-13 | todo |
| Q-02 | QuantMeridian later | Implement service/Node proxy contracts, exact initial pin and strict coverage wrapper | Q-01; existing cash rule available | AC-11 | todo |
| Q-03 | QuantMeridian later | Add treasury mapping/upload and exception UI, DATAOPS readiness and report export | Q-02, U-07, U-10 | AC-01–05, AC-11 | todo |
| Q-04 | QuantMeridian later | Add one-PR updater with workflow-trigger solution and candidate compatibility checks | Q-02, U-10 | AC-12 | todo |
| Q-05 | QuantMeridian later | Validate generated-Core exclusions, deployment bundle and rollback | Q-03–04 | AC-11–13 | todo |
| Q-06 | QuantMeridian later | Run acceptance pilot on approved real data, document limitations and enable rollout | Q-05 | AC-01–05, AC-11–12 | todo |

Q tasks are planning records only. This branch must not create downstream
services, secrets, workflows, or deploy anything. R-09–R-11 are follow-up design
candidates, not implicitly included implementation commitments in U-09.

## Acceptance coverage and evidence

| Criteria | Owner tasks | Required evidence |
| --- | --- | --- |
| AC-01 | U-02, U-07, Q-03 | Independent weekly cash equations; sign/offset cases; consumer mapping tie-out |
| AC-02 | U-04 | Continuity fixtures, missing-precondition and ordering tests |
| AC-03 | U-03 | Missing whole scope, duplicate/overlap/gap/extra-period fixtures |
| AC-04 | U-05 | Exact boundary, restricted cash, currencies, Decimal tests |
| AC-05 | U-06 | Facility roll-forward, maturity boundaries, headroom tests |
| AC-06 | U-08 | Pairing, zero/negative actual, limit combination, cutoff/vintage tests |
| AC-07–09 | U-01–10 as mapped above | Relevant core regressions, catalog/policy parity, build/distribution checks |
| AC-10 | U-09 | Debt and issuance equation/convention fixtures; later rules need separate design |
| AC-11 | Q-02–03, Q-05 | Empty/skipped/error/partial handling, identities and sanitized failure tests |
| AC-12 | Q-04–06 | Changed/no-change/failed-candidate updater tests, checks triggered, rollback rehearsal |
| AC-13 | Q-01, Q-05 | No downstream change now; explicit document move and generated-Core verification later |

## Completion evidence

No implementation evidence yet. Add actual PRs/commits and commands/results here
as tasks complete. Do not copy proposed commands into this section as if run.

## Document migration protocol

When Q-01 starts, follow [the staged consumer move plan](quantmeridian/SPEC.md#move-plan).
Move the current consumer design and Q task details into a QuantMeridian spec PR.
After that PR merges, replace the staged file with a short pointer containing
the actual destination/PR and migrated revision. Keep U tasks authoritative here
and Q execution status authoritative in QuantMeridian; do not maintain two
independently editable integration specifications.

## Change log

- 2026-10-17: Drafted upstream scope, implementation plan, and deferred consumer
  handoff in finassert at the user's direction. No integration or rule added.
