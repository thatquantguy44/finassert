# Roadmap

1. Harden dataframe adapters and diagnostic row identity under specification
   0004 (grouped rules and the ordering column are in place), and add grouped
   variants of the portfolio rules, such as weights per portfolio.
2. Add returns and exposure rules, then collateral and financing rules
   (specification 0002, milestones 3–4). Cash and NAV reconciliation are
   available now.
3. Add policy templates as rules are added, and integration inside Excel
   (specification 0011).
4. Introduce typed financial units and explicit FX provenance.
5. Benchmark batch execution before selecting vectorization or concurrency work.

Polars, distributed execution, hosted services, generated rules, interactive
dashboards, and live currency conversion remain explicitly deferred.
