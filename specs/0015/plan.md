# 0015 — Verified upstream release bundles: plan

1. Build and verify producer manifests, checksums, code/metadata parity and workflow integration.
2. Run shared bounded property/tolerance/scaling/accounting coverage under 0009.
3. Harden workbook visibility and formula/date/merged-header cases under 0013.
4. Add minimum available-cash buffer under 0012 U-05.
5. Add facility identity/capacity, continuity and maturity under 0012 U-06.
6. Publish a reviewed treasury policy pack with Python/CLI/MCP/report parity under 0012 U-07.

Each step has its own commit, focused evidence and owning-spec handoff before the
next. Final verification follows CONTRIBUTING.md, installed distribution checks,
strict docs and remote CI. No package publication, tag or downstream change.
