# 0007 — CLI and pipeline integration: handoff

[Spec](spec.md) · [Plan](plan.md) · [Tasks](tasks.md) · [Roadmap](roadmap.md) ·
[Contracts](contracts.md) · [Handoff](handoff.md) · [Agent instructions](AGENTS.md)

## Current state

- **Branch:** `spec/0020-quant-model-assurance` for the local cross-spec amendment.
- **Latest work:** Implemented configured/effective policy parameter export in
  JSON/HTML/XLSX through the ordinary engine, CLI and report path.
- **Evidence:** Full suite 3,785 passed; 111 Excel browser-job tests skipped.
  See [P-04 evidence](../0020/handoff.md#2026-11-21-verify-p-03-and-implement-p-04).
- **Next step:** Follow the master E-06 acceptance pickup; workbook/CLI/native
  Excel parity for spec 0020 remains in P-05/P-06.

## Entries

### 2026-11-21 — Implement policy parameter exports

CLI artifacts now retain configured parameters and complete effective
parameters, including catalog defaults and exact Decimal text, for every rule
outcome. JSON/HTML/XLSX tests and the full suite pass (3,785 passed, 111 Excel
browser-job tests skipped). Policy version 1, digest semantics, atomic writes
and exit codes are unchanged. P-05/P-06 own the remaining workbook/native Excel
parity; the master E-06 priority is unchanged.

### 2026-11-20 — Add configured and effective policy parameter contract

The user requested complete traceability for the 0020 policy. Each rule's
artifact descriptor now has an additive contract for explicit `parameters` and
complete `effective_parameters`, including defaults and exact Decimal text.
These appear for pass, fail, skip, and evaluation error outcomes. Policy version
1, its configured-policy digest, atomic CLI output, and exit codes stay unchanged.
Credentials must not be stored in policy documents. Runtime implementation is
pending; see [0020 decisions](../0020/decisions.md). Strict MkDocs build, 136
local/repository links across 19 changed Markdown files, and `git diff --check`
pass.

### 2026-11-15 — E-05 live artifact compatibility

Recorded optional input.excel under artifact schema 1 and canonical live views.
No CLI flag, public evaluation signature, exit-code, file-rendering or atomic
file-write change. Legacy/file regressions pass in the 3,697-test runtime suite;
full native output/CLI tie-out is an E-06 acceptance task. Follow the master order.

### 2026-11-13 — Gate 5: Atomic Excel reports and complete CLI file workflow

- **Branch / PR:** `feature/seven-priority-roadmap`, [draft PR #17](https://github.com/thatquantguy44/finassert/pull/17).
- **Done:** Atomic Excel reports and complete CLI file workflow.
- **Evidence:** 200 workbook, CLI, loader, and strict-policy tests passed; Ruff, mypy, and strict documentation build passed.
- **Next step:** Gate 6: typed money and ratios plus direct FX provenance.

### 2026-11-13 — Numbered spec workspace created

- **Branch:** `docs/spec-0011-excel`.
- **Done:** Moved the original spec verbatim from
  `specs/0007-cli-and-pipeline-integration.md` to `spec.md`; added plan, task, roadmap,
  contract, agent, and handoff files.
- **Not done / partial:** Runtime implementation and existing spec status are unchanged.
  Open tasks are not claimed complete.
- **Decisions:** Requirements remain canonical in `spec.md`; companion files track
  execution and evidence. Earlier project history remains in the [master
  handoff](../../docs/handoff.md).
- **Verify with:** Use [plan.md](plan.md) for baseline checks; documentation migration
  checks are recorded in the master handoff.
- **Next step:** Start with the first unchecked item in [tasks.md](tasks.md).
