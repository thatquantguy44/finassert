# 0011 — Contracts

[spec.md](spec.md) remains canonical. Preserve explicit financial assumptions, bounded diagnostics, dependency isolation, and unchanged caller data. Record API or outcome changes with migration notes.

The next live-workbook workflow is proposed in [0016](../0016/spec.md). Its
[compatibility notes](../0016/contracts.md) describe source/freshness/date/output
changes to make during implementation. Scoping that milestone does not change
the current task-pane behavior, public policy schema or financial outcomes.

E-02 now implements explicit table/fixed-range binding and a required 1900/1904
choice under 0016. Single-cell/whole-sheet inference is removed. Table totals are
excluded; range totals follow the selected bounds. Range mode needs ExcelApi 1.13
for merged-header rejection. Rebinding/date changes clear the snapshot/result,
and Run rereads the bound source; Python/file APIs and financial outcomes stay
compatible. E-03 now adds session-configurable monitoring/captures, calculation
guards, generation-safe operations and current-result export preflight. Shared
file results are cleared on input/policy changes. Financial outcomes, policy
serialization and artifact schemas stay compatible. E-04 adds live-only bounded
diagnostic navigation, resolving retained native row identities before JSON and
reverifying before selection. Its private response does not enter exported
artifacts or file/browser results. Versioned source provenance and
owned-output/collision handling remain pending under E-05.
