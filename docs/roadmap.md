# Roadmap

The seven-priority delivery now provides corrected workbook input, shared
adapter contracts, bounded diagnostics, verified cash/NAV parity, Excel report
output, typed quantities/direct FX, and retained scalar performance evidence.
See the [units guide](financial-units.md), [CLI guide](command-line.md), and
[master handoff](handoff.md). Each numbered spec has its own plan, tasks,
contracts, roadmap, agent instructions, and handoff.

The six-slice upstream branch adds verified package/capability bundles, shared
bounded property profiles, workbook visibility metadata, minimum cash buffers,
facility controls and the versioned cash/funding pack. Full acceptance evidence
is recorded in the [master handoff](handoff.md).

Next engineering work:

1. Build the Mac-first Excel validate → navigate → correct → rerun workflow under
   [specification 0016](https://github.com/thatquantguy44/finassert/blob/main/specs/0016/spec.md).
   Explicit source binding, stale-result handling, diagnostic navigation and date
   interpretation are proposed; real Excel acceptance is required for completion.
   E-01 has regression reproductions, an API audit and a diagnostic probe; finish
   the disabled native add-in loading baseline before E-02 source/date binding.
   PR #24 is merged; feature/excel-source-binding-dates is prepared from main for
   that next code slice, without promoting the outstanding native acceptance.
2. Implement paired forecast accuracy under specification 0012 U-08, with explicit
   matching/vintage/cutoff, zero-actual and limit-combination contracts.
3. Implement debt principal and issuance proceeds under 0012 U-09; finalize the
   conventions and extend 0002 before promoting new public financial rules.
4. Extend platform pilots and remaining adapter/grouped-rule requests based on
   demonstrated inputs. Local QuantSmith installation/orchestration belongs in its
   own repository and consumes the verified finassert bundle.

Additional project work:

1. Harden dataframe adapters and diagnostic row identity under specification
   0004 (grouped rules, the ordering column, and per-portfolio weights are in
   place), and add grouped variants of the remaining rules.
2. Add collateral and financing rules (specification 0002, milestone 4), and
   exposure rules that need classification data or notional. Cash and NAV
   reconciliation, market values, simple returns, and gross, net, and position
   limits are available now.
3. Add policy templates as rules are added. The initial task pane under 0011
   ([add-in](excel-add-in.md)) is the baseline for 0016's scoped workflow; its
   [real-host runbook](design/excel-spike.md) supplies the first Mac acceptance gate.
4. Extend the initial typed units and direct FX contracts only for demonstrated
   use cases; providers and conversion paths remain deferred.
5. Spec 0010 provides bounded diagnostic sampling and private one-column sharing
   across eligible built-in rules. Scalar/multi-rule benchmarks preserve report
   parity and retain timing/memory evidence. Use numerical-scan profiles before
   choosing further kernels; public batch/concurrent APIs remain proposed.

Polars, distributed execution, hosted services, generated rules, interactive
dashboards, and live currency conversion remain explicitly deferred.
