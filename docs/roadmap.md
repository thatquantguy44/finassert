# Roadmap

Each spec has a numbered `specs/NNNN/` workspace with its own roadmap, plan,
tasks, contracts, agent instructions, and handoff. See the
[spec catalog](https://github.com/thatquantguy44/finassert/blob/main/specs/README.md)
for the required layout. This page tracks the project-wide sequence.

Immediate corrective work covers Excel formula/error-cell handling (0011),
adapter value/label alignment (0004), and bounded diagnostics and JSON output
(0005). The [master handoff](handoff.md) and local spec task files record the
known gaps. The feature sequence is:

1. Harden dataframe adapters, column mappings, grouped rules, and diagnostic row
   identity under specification 0004.
2. Add cash and NAV reconciliation rules with documented sign and materiality
   conventions.
3. Complete Excel report output under specification 0011.
4. Add stable CLI/JSON artifacts, optional YAML policy configuration, and Excel
   flags under specifications 0005, 0006, 0007, and 0011.
5. Introduce typed financial units and explicit FX provenance.
6. Benchmark batch execution before selecting vectorization or concurrency work.

Polars, distributed execution, hosted services, generated rules, HTML dashboards,
and live currency conversion remain explicitly deferred.
