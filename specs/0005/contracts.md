# 0005 — Reporting and diagnostics: contracts

[Spec](spec.md) · [Plan](plan.md) · [Tasks](tasks.md) · [Roadmap](roadmap.md) ·
[Contracts](contracts.md) · [Handoff](handoff.md) · [Agent instructions](AGENTS.md)

[spec.md](spec.md) is the normative requirements source. This file indexes the contracts
and review focus; it does not introduce a second definition.

## Contract references

- [Public API](spec.md#public-api-design)
- [Data contracts](spec.md#data-contracts)
- [Failure semantics](spec.md#failure-semantics)
- [Acceptance criteria](spec.md#acceptance-criteria)

## Review focus

- Formatters are views over canonical results and do not change validation truth.
- Decimal precision is retained as text, and output is strict-JSON compatible.
- Diagnostic counts remain complete even when row/group details are capped.
- Artifact policy descriptors expose all explicitly configured parameters and
  all effective values used after defaults and schema normalization.

Unresolved implementation gaps and contract decisions are tracked in
[tasks.md](tasks.md). Changes to outcomes, IDs, tolerance mathematics, serialization, or
row identity require a spec amendment and migration note.

## Migration note — 2026-11-13

Results gain an additive `diagnostics` field containing bounded collections with
`kind`, `count`, `limit`, `observations`, and `truncated`. Legacy metadata is
retained, with missing/invalid weight lists now honoring `max_violations`.
Consumers should use source row labels rather than legacy filtered positions.
NaN/infinite floats now serialize to explicit text rather than raising or
emitting invalid JSON. Artifact schema 1 and main's severity-based blocking are
preserved. Naive explicit artifact timestamps are rejected instead of assuming
the host timezone. Redaction hooks remain a separate milestone.

## Compatibility note — 2026-11-15

0016 E-04 reads the native canonical diagnostic collections for a private live
Excel navigation response. Collection counts, limits, truncation, retained samples
and artifact schema 1 are unchanged. Session targets resolve physical source rows
before serialization and never enter the artifact. No full failed population is
reconstructed; ambiguous business keys require a unique key and rerun.

## Migration note — 2026-11-15 E-05

Optional `input.excel` source schema 1 is additive under artifact schema 1; only
the verified live bridge supplies it. Source IDs/address, date interpretation,
parsed/physical counts, captured/verified UTC times and the evaluated snapshot
digest are allowlisted. No full records, navigation maps or formula source enter
the artifact. Each export refreshes verified_at after preflight, not generated_at
or financial results. Live HTML/sheet views use canonical retained diagnostics
and complete cap/count summaries. Legacy artifacts and file/CLI rendering without
input.excel retain their previous behavior. See 0016 R-05 for output failure rules.

## Presentation migration — 2026-11-20

HTML and add-in sheet/editor views explain configured severity using the human
failure actions in [0011](../0011/spec.md#data-contracts). Third-column sheet text
is now **If check fails** with action labels, while **Result** remains the actual
outcome. Artifact/policy severity, technical CLI XLSX fields, diagnostics, counts,
precision, blocking and source identity remain unchanged. Existing saved evidence
is historical; it is not silently rewritten.

## Policy parameter artifact amendment — 2026-11-20

The user confirmed full policy traceability for the 0020 performance audit.
Under artifact schema 1, every rule descriptor carries `parameters` exactly as
configured and `effective_parameters` with the complete typed values used after
registered defaults and schema normalization. Decimal values remain exact text;
defaults are included, and the fields are present for pass, fail, skip, and
evaluation error outcomes. The existing configured-policy digest and version-1
policy input remain unchanged. This is additive; older artifacts remain valid.
See [0020 decisions](../0020/decisions.md).
