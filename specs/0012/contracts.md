# 0012 — Contracts

[spec.md](spec.md) remains canonical. Preserve explicit financial assumptions, bounded diagnostics, dependency isolation, and unchanged caller data. Record API or outcome changes with migration notes.

## R-04 public API — 2026-11-13

`minimum_cash_buffer` now ships with the canonical shared weekly schedule and
three required column mappings. Default zero tolerance preserves equality;
restricted/minimum negatives and invalid numeric values fail. Missing/ambiguous
schedules error, and tolerated shortfalls remain visible in bounded diagnostics.
Existing cash/coverage behavior is unchanged.
