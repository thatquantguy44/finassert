# Roadmap

The seven-priority delivery now provides corrected workbook input, shared
adapter contracts, bounded diagnostics, verified cash/NAV parity, Excel report
output, typed quantities/direct FX, and retained scalar performance evidence.
See the [units guide](financial-units.md), [CLI guide](command-line.md), and
[master handoff](handoff.md). Each numbered spec has its own plan, tasks,
contracts, roadmap, agent instructions, and handoff.

Remaining project work:

1. Harden dataframe adapters and diagnostic row identity under specification
   0004 (grouped rules, the ordering column, and per-portfolio weights are in
   place), and add grouped variants of the remaining rules.
2. Add collateral and financing rules (specification 0002, milestone 4), and
   exposure rules that need classification data or notional. Cash and NAV
   reconciliation, market values, simple returns, and gross, net, and position
   limits are available now.
3. Add policy templates as rules are added, and integration inside Excel
   (specification 0011): an initial task pane exists ([add-in](excel-add-in.md)); run
   the [spike](design/excel-integration.md) in real Excel next.
4. Extend the initial typed units and direct FX contracts only for demonstrated
   use cases; providers and conversion paths remain deferred.
5. Bounded diagnostic sampling under spec 0010 now counts all failures while
   retaining capped examples during evaluation. Use the updated scalar profiles
   before selecting shared-read, vectorization, or concurrency work. No optimized
   batch API is public.

Polars, distributed execution, hosted services, generated rules, interactive
dashboards, and live currency conversion remain explicitly deferred.
