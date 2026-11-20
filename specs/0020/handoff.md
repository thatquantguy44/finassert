# 0020 — Performance and backtest integrity handoff

## Current state

- **Status** Proposed. The workspace and acceptance scope are ready for review.
- **Branch** `spec/0020-quant-model-assurance`, based on `origin/main` at `8f14c66`.
- **Open design items** Resolve policy metadata, rule signatures, and reference
  precision before publishing an interface. See the [open questions](spec.md#open-questions).
- **Next spec task** P-02 prepares the monthly fixtures and reviews the proposed
  contract. The [master handoff](../../docs/handoff.md#next-up) owns project order.

## Entries

### 2026-11-20 — Scope the quant modeling workflow

- **Done** Defined the monthly performance workbook, reference calculation and
  audit paths, worked example, and acceptance criteria. Sequenced point-in-time
  backtest evidence and minimum-variance validation plus reference implementation.
- **Decisions** Use one monthly strategy and benchmark pair and the existing
  one-source Excel workflow for the first milestone. Carry the declared window,
  methodology, units, and original rows into the report.
- **Verified** Seven required files, 46 local links and anchors, exact decimal
  arithmetic for the worked return example, strict documentation build, and
  whitespace checks.
- **Next** Resolve P-02 and retain independent expected values before runtime work.
