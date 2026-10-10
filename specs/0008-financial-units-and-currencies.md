# 0008 — Financial units and currencies

**Status:** Proposed

## Problem statement

Numerically valid operations can be economically invalid when currencies, basis
points, percentages, prices, notionals, and returns are confused.

## Motivation and use cases

Rules must prevent unconverted aggregation, distinguish 50 bps from 50%, and
retain the provenance and timestamp of any FX conversion.

## Goals

Design optional typed quantities, dimension-safe operations, ISO currency codes,
explicit conversion, rate provenance, as-of time, and serialization.

## Non-goals

Fetching live rates, pricing instruments, maintaining holiday calendars, deciding
accounting functional currency, or providing a full units algebra are excluded.

## Proposed architecture

An optional `units` module defines immutable `Money(amount, currency)`,
`BasisPoints`, `Percentage`, `Return`, `Price`, and `Notional`. Amounts prefer
Decimal. `FxRate(base, quote, rate, as_of, source)` performs explicit conversion;
no global FX table exists.

## Public API design

```python
usd = Money(Decimal("100"), "USD")
rate = FxRate("EUR", "USD", Decimal("1.08"), as_of, source="approved-close")
converted = rate.convert(Money(Decimal("50"), "EUR"))
```

Rules either require homogeneous currency or accept a caller-provided converter
and maximum rate age.

## Data contracts

Currencies use normalized ISO 4217 codes plus an explicit extension mechanism for
fund units. Rates state base/quote direction, positive finite value, aware UTC
timestamp, source, and optional identifier. Serialization never drops these.

## Financial and numerical edge cases

Cover zero/negative money where semantically valid, non-decimal currencies,
inverse rates, triangular paths, stale rates, same-currency identity, percentage
points versus percent changes, and bps conversion (`1 bp = 0.0001`).

## Failure semantics

Adding unlike currencies errors. Missing, stale, nonpositive, or directionally
incompatible FX errors; it never silently skips or assumes parity. Rule-level
materiality remains distinct from currency minor-unit rounding.

## Implementation milestones

1. Review dimensional model. 2. Money and ratio units. 3. Explicit direct FX.
4. Adapter metadata integration. 5. Optional path conversion only with provenance.

## Acceptance criteria

Impossible mixed-unit operations fail; conversions are explicit and reproducible;
bps/percentage boundaries are tested; artifacts retain rate source and as-of time.

## Testing requirements

Property-test conversion/inversion within tolerance, code normalization, stale and
missing rates, Decimal preservation, serialization, bps/percent conversions, and
invalid cross-unit arithmetic.

## Dependencies on other specifications

Uses 0003 tolerances, 0004 adapter metadata, and 0005 reporting; financial rules
in 0002 consume the units.

## Explicit deferred work

Rate providers, triangulation policy, calendars, crypto precision policy, pricing,
inflation, tax, and accounting translation are deferred.
