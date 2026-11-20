# Roadmap

The [master handoff](handoff.md#next-up) is canonical for current project ordering
and the next pickup. This roadmap supplies longer-term context. Spec 0017 adds
Git commit/push/CI guards plus an explicit non-Git filesystem checkpoint workflow.
PR #25 merged Excel E-01–E-03 and the original Git guards
into main at 32cf4ab. E-04 navigation is implemented on
feature/excel-diagnostic-navigation with focused native/automated evidence.
E-05 now adds verified source provenance, canonical outputs, saved ownership and
partial-write recovery. Both slices and the QuantSmith reference reader are
merged into main. E-06 now has synthetic fixtures, retained-export/CLI tooling
and Mac automated preflight. Native scale, verified capture, exports/CLI parity
and source integrity now pass. The small native 1900 correction/Stale/reread/pass/
export/CLI loop is also verified. The native 1904 repeat and full automated
regressions passed on 2026-11-20. Finish the table/hidden/failure/race/keyboard rows from the
[current pickup](https://github.com/thatquantguy44/finassert/blob/main/specs/0016/acceptance.md#current-pickup-and-retained-native-files).
The task pane also has a workbook-first visual refresh and a schema-valid Home
ribbon launcher: validation opens the normal workflow and Settings opens a focused
in-pane settings view. Native Home visibility and both launch actions were
observed on 2026-11-20; full E-06 remains open. The shared run summary now
links directly to **Open Full Validation Report**, opening/focusing/scrolling
the displayed report without new workbook reads or changes to export guards.
Spec 0018 adds an optional, read-only QuantSmith reference in the Excel pane.
It defaults to the supplied local checkout and offers an explicit pinned GitHub
source for the local owner; neither mode changes E-06's priority or claims
shared hosting support.
Spec 0019 now supplies the comprehensive [user guide](user-guide.md), a reviewed
47-page PDF with all 20 built-in rules and 10 templates, and a local read-only
download API in the existing Excel server. Its pane link and HTTPS downloads are
verified; this delivery leaves the E-06 host-acceptance gate and priority unchanged.

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
   E-01's native 50,000-row baseline and E-02's explicit source/date binding are
   verified on feature/excel-source-binding-dates. E-03 now adds configurable
   session capture/freshness, calculation/event/policy guards and export preflight.
   E-04 now adds guarded bounded diagnostic navigation with native F8 evidence.
   E-05 adds verified evidence/safe output. E-06's native 1900 correction loop
   now passes with actual export/CLI/integrity evidence, including the native
   1904 repeat. Next are clean table/hidden/filtered and remaining
   failure/race/keyboard cases.
   Range mode requires stable ExcelApi 1.13; table mode keeps the 1.7 floor.
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

The named Validation/Settings host panes and first headings are now verified
on the recorded Mac build. Human failure-action wording is verified in the saved
native demo, with canonical severity/outcomes unchanged. Full E-06 remains the
next priority under the master handoff; this UI delivery does not close that gate.
