# Staged consumer specification — QuantMeridian and finassert

**Status:** Proposed; stored temporarily in finassert. Move to QuantMeridian
before consumer implementation. No downstream change is authorized by the
mere existence of this file.
**Updated:** 2026-10-17
**Upstream requirements:** [Treasury rules](../SPEC.md)
**Upstream delivery plan:** [PLAN.md](../PLAN.md)
**Staging ledger:** [TASKS.md](../TASKS.md)

## Goal and boundary

QuantMeridian consumes an immutable finassert build through a Python companion
service, displays financial validation evidence, and receives proposed pin
updates automatically. Deployed execution remains reproducible. The integration
uses latest *tested and promoted* code, not an unpinned branch fetched at runtime.

The initial application workflow validates uploaded/mapped weekly cash
forecasts; it does not generate forecasts or execute funding. Existing CASH,
LIQ, COLL, REINV and other desk modules may adopt additional packs later. New
upstream rules do not automatically become enabled application policies.

At reviewed QuantMeridian commit
`66b218a030ebc0b2922fc6657aa92dad92e79eeb`, the app has a Node API registry,
server-side provider proxies, DATAOPS health, feature flags, and an
InventoryBallast companion-service pattern. Its README describes internal book
modules as fixtures. Do not treat their fixture checks as validation of live
treasury data. Reinspect these facts at migration rather than treating paths or
deployment assumptions as permanent.

## Proposed architecture and ownership

```text
Browser: Treasury validation workspace / exception report
             |
QuantMeridian Node /api/validation/* (auth, bounds, proxy)
             |
Python financial_validation_api (application-owned policies and mapping)
             |
Pinned finassert wheel / exact source revision (pure rule execution)

Scheduled/manual updater -> candidate pin PR -> compatibility CI
                       -> merge -> normal build/deploy -> readiness gate
```

Suggested service path: `services/financial_validation_api/`. Suggested proxy:
`src/lib/server/financialValidationProxy.ts`. Paths and route placement are
working names to finalize in the destination spec. A Node serverless deployment
calls a separately deployed Python service; do not assume Python runs inside
the Vite client or existing Node function. The initial UX can live as a panel
in CASH; the migration review chooses panel versus separate module based on the
then-current navigation. Validation computation must remain independent of that
choice.

Only application mapping/preflight and strict coverage aggregation belong in
the service. Do not duplicate upstream financial equations in TypeScript.
Finassert's browser/Pyodide path is a possible future offline mode with its own
identity and parity tests, not an implicit fallback for service failure.

## Proposed API v1

Node mirrors the following bounded service operations:

| Service operation | Node surface | Behavior |
| --- | --- | --- |
| `GET /health` | Integrated into `/api/dataops/health` | Sanitized readiness and engine/contract identities only |
| `GET /v1/capabilities` | `GET /api/validation/capabilities` | Enabled packs, supported mappings, required checks, limits and pinned engine identity |
| `POST /v1/validate` | `POST /api/validation/check` | Synchronous request-lifetime validation; no persisted job or pollable run |

All `/v1/*` calls require a server-held bearer token and correlation ID. The
Node route enforces existing application authentication/authorization and body
limits before forwarding. Token presence alone is not end-user authorization.
Do not expose a general remote policy executor or arbitrary custom Python.

Request schema, to become machine-readable JSON Schema at implementation:

- `contractVersion`: `"1"`; reject unsupported versions.
- `packId`, `packVersion`: exact reviewed application pack; nonempty required
  rule list comes from the server's manifest, never the submitted file.
- `source`: `USER_UPLOAD`, `DB`, or `SIM`, with source as-of time and opaque
  dataset identity; the server owns DB/SIM provenance and treats uploaded
  provenance as user supplied. Fixture mode is explicitly labelled.
- `expectedScope`: explicit vintage/entity/currency/scenario tuples, anchor,
  horizon and period grain; not inferred from submitted rows alone.
- `mapping`: approved column-role mapping, sign/unit declarations, materiality
  and caller-selected limits; included in the effective policy digest.
- `datasets`: cash and optional facility rows, stable string row IDs, ISO dates,
  finite decimal strings for financial amounts. Cross-file mapping rejects
  duplicate joins, unmatched required keys and missing financing tie-outs.
- `actualsCutoff` and metric selection when the accuracy pack is supported.

Response schema:

- `contractVersion`, `runId`, `correlationId`, server `evaluatedAt` UTC.
- `engine`: package/version, exact source commit, wheel SHA-256 and pack digest;
  `policyDigest` covers the effective policy including expected scope/mappings.
- `source`: provenance, source-as-of and completeness information; validation
  cannot upgrade SIM into live or make old inputs fresh.
- `evaluationState`: `COMPLETE`, `INCOMPLETE`, or `ERROR`.
- `decision`: `PASS`, `FAIL`, or `UNDETERMINED`; only complete evaluation can
  yield PASS/FAIL. `failOn` records the applied severity threshold.
- `coverage`: required/evaluated/errored/skipped/missing check counts and scope
  counts; counts refer to the explicit required check/scope matrix.
- `report`: lossless finassert JSON results plus derived counts under `failOn`;
  preserve upstream outcome/severity and default `blocking` fields unchanged.
- `diagnosticsTruncated`, total violation count and displayed count; no silent
  success when diagnostic examples are capped.

No `GET /runs/{id}` endpoint is promised. `runId` correlates an in-memory
response and export; refresh or restart loses it unless the user saved a report.
Durable storage/retention is separate future scope. HTML/JSON export may be
generated from the returned immutable report and verified effective policy,
using existing rendering code and escaping untrusted text.

### Aggregation truth table

| Condition | evaluationState | decision |
| --- | --- | --- |
| Every required check and scope evaluated; no failures at `failOn` | COMPLETE | PASS |
| Every required check and scope evaluated; blocking financial failures | COMPLETE | FAIL |
| Missing rows/groups with evaluated coverage failures and prerequisite evaluation errors | ERROR | UNDETERMINED |
| Any required check missing or skipped | INCOMPLETE | UNDETERMINED |
| Required evaluation error or incompatible engine/contract | ERROR | UNDETERMINED |
| No rows, no rules, or empty expected scope | Rejected before evaluation | No report/decision |

For mixed states, ERROR takes precedence over INCOMPLETE, which takes
precedence over COMPLETE. Proven financial failures stay visible even when the
overall decision is undetermined. Optional skips are counted and explained but
do not change required coverage. A warning failure can coexist with COMPLETE
PASS at `failOn=error`; display it. Never label incomplete input as validated
because `ValidationReport.passed` permits empty or skipped reports.

### Failure and resource contract

Completed validation, including ordinary financial failures, returns HTTP 200.
Malformed/schema-invalid requests return 422; oversized bodies 413; missing or
invalid service credentials 401; insufficient app permissions 403; service
unready/unavailable 503; deadline exceeded 504. Invalid policy/configuration is
422. Unexpected faults return a sanitized 500 and correlation ID. Expected
per-rule errors are represented in a 200 response with ERROR/UNDETERMINED.

Proposed initial hard bounds: 10 MiB request, 20,000 total rows, 5,000 expected
scope/bucket combinations, 100 enabled checks, 50 displayed diagnostics per
check and 500 total, 10-second Python evaluation deadline, 15-second proxy
deadline. The Cartesian check/scope product must also be capped at 100,000.
Exceeding an input bound rejects the request; only diagnostic lists truncate.
Prove deadline cancellation or process isolation in implementation: a timed-out
HTTP coroutine must not leave unbounded CPU work running. Benchmark synthetic
maximum-size requests before finalizing deployment limits.

The browser holds data for the active session. Python/Node must not log or
persist row data, report amounts, or effective policies; telemetry contains
correlation IDs, engine identity, durations, counts and sanitized error codes.
No third-party model or external data provider receives submitted forecasts.
The destination spec must identify the app's real access boundary and hosting
region before operational data is enabled. These are application decisions,
not new finassert core restrictions.

## Exact dependency pin and capability manifest

Bootstrap candidate reviewed here:
`19be7eda7400412b2d46bf3e5cd6c4bfc8f537c5`. It supplies existing rules only;
it is not claimed to implement this treasury pack or to have passed consumer CI.

A direct-source requirement can initially be:

```text
finassert @ git+https://github.com/thatquantguy44/finassert.git@19be7eda7400412b2d46bf3e5cd6c4bfc8f537c5
```

The consumer build resolves this exact revision, builds/verifies a wheel, and
installs the same wheel into an immutable service image. Record source commit,
package version, wheel SHA-256, policy-pack digest, contract version, and image
digest in the application manifest. Version 0.1.0 alone cannot identify source
revisions. No editable install, floating `main`, or startup `pip install` in
deployed services. Later PyPI use requires an exact published version and
verified hashes plus a release-to-source identity record.

Readiness checks the installed artifact/source fingerprint, installed metadata,
contract version and required exported rule capabilities against the manifest.
A package-version match alone is insufficient. Missing or mismatched engine
blocks validation and displays an unavailable/incompatible state. Pack adoption
is explicit: an updated engine can expose extra capabilities without changing
which reviewed checks the application executes.

## Automatic update design

Default: a daily scheduled workflow in QuantMeridian plus `workflow_dispatch`.
Poll only public finassert metadata; no finassert-side cross-repository write
credential is required. Initially compare against finassert main's full commit
SHA. When a stable release process exists, change the candidate policy explicitly
to latest eligible release rather than silently mixing release and branch modes.

1. Resolve the configured source ref once to a full candidate SHA and record it.
   Verify repository identity and skip if it equals the recorded pin. Build and
   test that SHA even if main advances during the run.
2. Serialize updater runs. Maintain one updater-owned branch and one open PR;
   update it only with a lease on its known head. Never rewrite a human branch.
3. Build candidate artifacts using a read-only job with no write credentials.
   Use synthetic data only. Treat upstream code/tests as code execution; no
   production secrets enter that job.
4. Run smoke imports, expected catalog checks, serialization/Decimal snapshots,
   all required pass/fail/error/skip fixtures, API contract tests, policy-pack
   parity, service readiness, TypeScript checks, existing unit/build suites, and
   focused browser integration tests. Block unsupported API or semantic changes.
5. If compatible, a separate minimal write job opens/updates the PR with old/new
   SHAs, source compare URL, rule/catalog changes, artifact/manifest changes,
   contract version and test evidence. A failed candidate is recorded in the
   workflow summary and must not update the deployable pin or leave stale green
   evidence attached to a new head. No-change runs create no commit.
6. Merge/deploy uses QuantMeridian's existing repository policy. This proposal
   does not enable auto-merge, bypass checks, or deploy directly from finassert.
   Pin updates require a rebuild and deployment; a running service does not
   acquire new code just because upstream advanced.

GitHub Actions detail: PRs/commits created using `GITHUB_TOKEN` ordinarily do not
trigger ordinary downstream push/PR workflows. Implementation must deliberately
solve this: use an appropriately scoped installation token for the updater PR,
or explicitly dispatch reusable verification against the exact PR head and
publish the required check results through the approved workflow. A workflow
summary from the updater alone must not be mistaken for required PR checks.
Keep permissions minimal and write credentials out of candidate build jobs.
Never use a privileged `pull_request_target` run to execute untrusted head code.

Track current deployed pin, latest checked candidate and check time separately
in operations metadata. A pending/failed update is not engine-health success.
Source advances without a compatible candidate should remain visible as a
pending update, with no promise of immediate adoption.

## UX and operational acceptance

The workspace offers sample versus uploaded input, explicit field mapping and
assumptions, validation action, summary, exceptions table, and report export.
Show entity/currency/scenario/week, observed/expected/difference, severity and
rule explanation. User-facing text leads with the financial issue. Engine
commit and policy digests live in report/diagnostic details, not the primary
workflow. Stale data, incomplete coverage, service unavailable, timeout, and
incompatible engine have distinct states. No simulated fallback creates a green
validation state for an uploaded book.

For initial synthetic acceptance, one row has opening 100, receipts 20,
payments 30, financing inflows 5, financing outflows 0, adjustments 0, closing
95, restricted 10 and minimum buffer 90. Identity passes; available cash is
85 and buffer shortfall is 5. A separate facility with commitment 100,
unavailable 10, opening drawn 80, draw 15 and repayments 0 closes at 95 and
exceeds available commitment by 5. These independent examples use one declared
currency and must not be presented as a cross-file reconciled pair.

Acceptance also covers service down, wrong identity, malformed monetary input,
all required checks skipped, empty rules, partial scope, warning severity,
diagnostic caps, HTML escaping, token redaction, correct DB/upload/SIM labels,
and no-change/failed/successful update PRs with checks on the exact candidate.

## Rollout and rollback

1. Migrate/reconcile this spec with active QuantMeridian changes.
2. Bootstrap service with a manual exact pin and existing cash checks; label
   unavailable proposed checks instead of advertising the treasury pack.
3. Adopt the upstream treasury pack after its required capabilities exist and
   synthetic contract/UX tests pass. Enable behind an application feature flag.
4. Prove generated QuantMeridian-Core excludes the treasury service, routes,
   pack and updater where outside Core's boundary. Shared DATAOPS/nav changes
   need downstream transforms/patches so generated builds still pass. Decide
   whether any future generic macro-validation subset belongs in Core separately.
5. Pilot approved operational input; document mappings, source freshness and
   limits. Enable the normal application deployment path after readiness checks.
6. Enable updater PR creation after manual pin promotion is proven.

Rollback restores the previous service image, pin manifest, policy pack and
compatible Node/UI bundle together. Keep the last known working artifacts.
If contracts differ, disable the feature until the matched bundle is restored;
do not mask mismatch by returning a prior report as a new validation. No DB
migration is required for the request-lifetime v1 design.

## Move plan

At the owner's chosen time, create a new QuantMeridian spec branch from its
current main and reinspect instructions, existing integration services,
authorization, routes, CI, generated-Core boundaries and deployment model.
Choose its next free spec number. Move this document into that spec's WHAT/WHY
and HOW documents, and move Q-01–Q-06 from the staging ledger into its task file.
Update all upstream links to immutable finassert revisions or durable spec URLs.
Record a field/path/decision reconciliation rather than applying stale paths.

After the destination spec PR merges, replace this staged document in finassert
with a pointer to its actual URL, PR and migrated revision. Keep general rule
semantics and U tasks here. Do not create a bidirectional synchronization bot
or maintain duplicate sources of truth. No QuantMeridian branch, service, secret,
workflow, or deployment is created by this documentation change.
