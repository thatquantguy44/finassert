# 0010 — Roadmap

## Current milestone

Bounded scalar diagnostic evaluation implemented and compared with the retained
48-case reference. Dense 100,000-row failure peak fell from 22.88 to 4.58 MiB;
complete report fingerprints match. See [measurements](artifacts/README.md).

## Next and deferred work

Review the bounded-diagnostic change, then use the updated profiles to select
shared reads or private vector kernels only when a workload justifies them.
Input materialization and aggregation memory remain; batch APIs stay proposed.

See [tasks.md](tasks.md), [plan.md](plan.md), and the [project roadmap](../../docs/roadmap.md).
