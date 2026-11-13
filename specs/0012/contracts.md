# 0012 — Contracts

[spec.md](spec.md) remains canonical. Preserve explicit financial assumptions, bounded diagnostics, dependency isolation, and unchanged caller data. Record API or outcome changes with migration notes.

## R-04 public API — 2026-11-13

`minimum_cash_buffer` now ships with the canonical shared weekly schedule and
three required column mappings. Default zero tolerance preserves equality;
restricted/minimum negatives and invalid numeric values fail. Missing/ambiguous
schedules error, and tolerated shortfalls remain visible in bounded diagnostics.
Existing cash/coverage behavior is unchanged.

## R-05 public API — 2026-11-13

`facility_capacity` is now public with required facility/amount/maturity mappings.
Expected scope includes the separate facility key. Principal identity, effective
capacity and adjacent principal continuity are independent findings; all components
are nonnegative. Missing/duplicate periods and invalid/intraperiod maturity error.
Maturity at/before period start requires zero draw/closing within explicit amount
tolerance; maturity at the final end does not invent a subsequent period.
Headroom is never clamped. Earlier coverage/continuity APIs remain unchanged.
