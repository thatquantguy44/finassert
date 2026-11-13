# 0007 — CLI and pipeline integration

**Status:** Proposed

## Problem statement

Pipelines need noninteractive validation, stable exit codes, and artifacts without
embedding bespoke Python in every GitHub Actions, Dagster, Mage, or Airflow job.

## Motivation and use cases

Teams validate files during CI, gate ETL stages, retain JSON diagnostics, and
separate policy failures from configuration or runtime errors.

## Goals

Specify a small CLI, optional YAML configuration, explicit loaders, stable exit
codes, deterministic JSON, and orchestrator-neutral invocation.

## Non-goals

Scheduling, secret management, file discovery, remote execution, alerting, or
orchestrator-specific operator packages are excluded initially.

## Proposed architecture

An optional `cli` extra provides `finassert check`. A loader registry handles only
explicit input format and path. YAML resolves allowlisted rule factories through
a caller-selected registry. The CLI invokes the ordinary engine and reporter.

## Public API design

```text
finassert check --config policy.yml --input positions.parquet --format parquet \
  --output report.json
```

Proposed exit codes: `0` all pass/skip; `1` invariant failure; `2` evaluation
error; `3` configuration/usage error; `4` input/output failure. If failures and
errors coexist, `2` wins.

## Data contracts

Config version is required. Each rule entry includes ID/factory and parameters;
unknown keys fail. Artifacts use specification 0005 and include config digest,
input locator supplied by user, timestamps in UTC, and tool version.

## Financial and numerical edge cases

YAML numeric spelling can lose Decimal intent, so Decimal-sensitive values accept
quoted strings and declared numeric type. Currency and as-of context are explicit.

## Failure semantics

Malformed configuration never becomes a skipped rule. Partial reports are written
atomically when evaluation began. Secrets and full records are not printed.

## Implementation milestones

1. Freeze artifact envelope. 2. JSON/CSV loader and YAML schema. 3. CLI and exit
tests. 4. Parquet optional extra. 5. Orchestrator recipes without SDK coupling.

## Acceptance criteria

Runs without prompts, documents all exit codes, validates config strictly, emits
the same rule results as Python API, and works in GitHub Actions and plain shell.

## Testing requirements

Subprocess-test every exit code, malformed/unknown config, paths with spaces,
atomic output, signals, empty rules, mixed outcomes, Decimal config, and help text.

## Dependencies on other specifications

Requires 0001, 0005, and 0006; dataframe formats use 0004; unit config uses 0008.

## Explicit deferred work

Airflow/Dagster/Mage packages, remote URIs, SQL, watch mode, interactive prompts,
parallel files, policy servers, and automatic plugin installation are deferred.
