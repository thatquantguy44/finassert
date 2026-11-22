# 0007 — CLI and pipeline integration: tasks

[Spec](spec.md) · [Plan](plan.md) · [Tasks](tasks.md) · [Roadmap](roadmap.md) ·
[Contracts](contracts.md) · [Handoff](handoff.md) · [Agent instructions](AGENTS.md)

Baseline recorded 2026-11-13. Checked items identify existing implementation, not full
acceptance certification.

## Existing baseline

Current main implements the policy catalog, strict YAML/JSON configuration, CLI, and JSON/CSV/XLSX/Parquet loaders.

## Remaining work, in order

- [x] Freeze the versioned artifact envelope with 0005 and factory/configuration
  contracts with 0006.
- [x] Specify strict versioned YAML configuration, unknown-key rejection, and
  Decimal-sensitive parameter spelling.
- [x] Implement explicit JSON/CSV loaders and a CLI invoking the ordinary
  engine/reporters.
- [x] Subprocess-test exit codes 0-4, mixed outcomes, paths with spaces, atomic partial
  output, and malformed inputs.
- [x] Add Excel flags with 0013; add optional Parquet support after the initial loaders.
- [x] Document plain-shell and CI recipes without coupling to orchestrator SDKs.
- [x] Export configured and effective rule parameters in JSON/HTML/XLSX report
  artifacts, including catalog defaults and exact Decimal text; preserve the
  version-1 input schema, digest semantics, atomic writes, and exit codes; full
  suite passes 3,785 tests with 111 Excel browser-job tests skipped (2026-11-21).

Record evidence in [handoff.md](handoff.md) before checking off work.
