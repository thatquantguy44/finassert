# Roadmap

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
4. Introduce typed financial units and explicit FX provenance.
5. Benchmark batch execution before selecting vectorization or concurrency work.

Polars, distributed execution, hosted services, generated rules, interactive
dashboards, and live currency conversion remain explicitly deferred.
