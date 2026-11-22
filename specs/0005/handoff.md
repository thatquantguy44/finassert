# 0005 — Reporting and diagnostics: handoff

[Spec](spec.md) · [Plan](plan.md) · [Tasks](tasks.md) · [Roadmap](roadmap.md) ·
[Contracts](contracts.md) · [Handoff](handoff.md) · [Agent instructions](AGENTS.md)

## Current state

- **Branch:** `spec/0020-quant-model-assurance` for the local cross-spec amendment.
- **Latest work:** Implemented the additive policy `parameters` and
  `effective_parameters` artifact contract through JSON, HTML and XLSX reports.
- **Evidence:** Full suite 3,785 passed and 111 bundled Excel browser-job tests
  skipped; [P-04 tests](../0020/handoff.md#2026-11-21-verify-p-03-and-implement-p-04).
- **Next step:** Follow the [master handoff](../../docs/handoff.md#next-up),
  beginning with full E-06 Mac acceptance. Redaction hooks remain a separate
  future milestone.

## Entries

### 2026-11-21 — Implement policy parameter artifact export

Every configured rule now records its explicit policy values and complete
effective values after catalog defaults and schema normalization. Exact Decimal
values remain strings, unsupported parameters fail serialization, and the
configured policy digest is unchanged. JSON/HTML/XLSX report tests, the full
3,785-test suite and mypy pass; 111 Excel browser-job tests were skipped. The
additive schema-1 requirement is implemented; E-06 remains the project pickup.

### 2026-11-20 — Add configured and effective policy parameter contract

The user selected one composite 0020 audit check and complete parameter
traceability. Artifact schema 1 now requires configured `parameters` and
fully resolved `effective_parameters`, including defaults and exact Decimal
text, for rules that pass, fail, skip, or error. The existing policy digest and
policy input format are unchanged. Runtime implementation remains pending.
Strict MkDocs build, 136 local/repository links across 19 changed Markdown files,
and `git diff --check` pass.

### 2026-11-20 — Human failure-action wording preserves canonical results

Human-facing HTML and add-in sheet views now explain configured severity as
**If check fails** with **Block validation**, **Show warning**, or **Show information**.
Passed/failed/could-not-run outcomes remain separate. Embedded JSON, policy values,
technical CLI XLSX severity fields, numerical results and blocking are unchanged.
Existing output/escaping tests now cover the new labels and passing blocking rules;
warning/info labels preserve their original canonical severity. Full runtime 3,743
and browser 111 pass, as do smoke/quality/docs/distributions. The native saved demo
has three passed checks with Block validation. E-06 remains the master pickup.

### 2026-11-15 — E-05 optional live context and canonical views

Optional scalar input.excel schema 1 is validated in the private live bridge,
without public signature or file/CLI artifact changes. Live HTML and worksheet
views consume canonical retained observations and complete counts/caps/truncation,
with no hidden second sample cap. Report, policy and generation time stay fixed;
only verified_at refreshes after preflight. 22 focused parity/context tests,
3,697 full runtime and 106 browser cases pass. Follow the master's E-06 pickup.

### 2026-11-15 — E-04 diagnostic compatibility

Recorded the private navigation response boundary. E-04 uses only canonical
retained samples, resolves labels before serialization, preserves complete counts
and caps, and leaves artifact schema 1 unchanged. Identity tests compare samples
to exported canonical diagnostics and cover collisions/zero caps. No financial
semantics or formatter rewrite. Current project ordering is the master handoff.

### 2026-11-13 — Gate 3: Bounded structured diagnostics and strict versioned artifacts

- **Branch / PR:** `feature/seven-priority-roadmap`, [draft PR #17](https://github.com/thatquantguy44/finassert/pull/17).
- **Done:** Bounded structured diagnostics and strict versioned artifacts.
- **Evidence:** 754 full-suite tests passed; the remaining MCP subprocess passed after repairing the macOS hidden flag on the editable-install path; Ruff and mypy passed.
- **Next step:** Gate 4: verify existing public cash and NAV contracts across adapters.

### 2026-11-13 — Numbered spec workspace created

- **Branch:** `docs/spec-0011-excel`.
- **Done:** Moved the original spec verbatim from
  `specs/0005-reporting-and-diagnostics.md` to `spec.md`; added plan, task, roadmap,
  contract, agent, and handoff files.
- **Not done / partial:** Runtime implementation and existing spec status are unchanged.
  Open tasks are not claimed complete.
- **Decisions:** Requirements remain canonical in `spec.md`; companion files track
  execution and evidence. Earlier project history remains in the [master
  handoff](../../docs/handoff.md).
- **Verify with:** Use [plan.md](plan.md) for baseline checks; documentation migration
  checks are recorded in the master handoff.
- **Next step:** Start with the first unchecked item in [tasks.md](tasks.md).
