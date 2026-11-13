# 0016 — Excel add-in validation workflow: tasks

**Status:** Scope prepared; all implementation tasks pending.

## Scoping delivery

- [x] Audit current snapshot reading, stored results, date payload and diagnostic output.
- [x] Define one-source Mac-first scope, compatibility boundaries and acceptance criteria.
- [x] Sequence implementation and identify meaningful automated/manual evidence.
- [x] Verify documentation links/anchors, workspace completeness, whitespace and strict build.

Scope evidence: 16 Markdown files and 80 local links/anchors checked; all seven
required files, six requirements/tasks and ten acceptance rows present. Strict
MkDocs and git diff --check passed. Runtime tests were not rerun for this
documentation-only proposal; no new runtime capability is claimed.

## Ordered implementation

Each E task is one intended reviewable commit; split a commit further when needed
without skipping its dependencies. Check completion only with recorded evidence.

- [ ] **E-01 — Host baseline and contracts** (R-06, AC-08/09): open proposal issue;
  add a regression reproducing stale data/policy results; record real Mac version,
  install route, capability/requirement matrix, calculation behavior and date
  fallback. Attach baseline diagnostics; refine the estimate and host support floor.
- [ ] **E-02 — Source binding and dates** (R-01/04, AC-01/05): one table/range picker,
  exact geometry/identity, table totals exclusion, hidden/filtered inclusion,
  pre-read size guard, malformed/empty regions and explicit 1900/1904 choice.
  Verify offsets, date equality and selection changes that preserve binding.
- [ ] **E-03 — Freshness and stable capture** (R-02, AC-02/03/08): define canonical
  snapshot encoding/digest vectors; single operation/generations; rereads and
  calculation guards; edit/recalc/structure/policy invalidation; event disposal;
  delayed events, concurrent edits, failed runs and obsolete callbacks. Verify
  shared browser/file paths after changes to the common application.
- [ ] **E-04 — Diagnostic navigation** (R-03, AC-04/06): canonical sampled findings,
  complete totals/caps; physical row/cell targets; business-key ambiguity, group
  context and missing targets; source verification and keyboard navigation.
  Test malicious text, quoted sheet names, sort/delete and changed row mappings.
- [ ] **E-05 — Evidence and export** (R-05, AC-03/06/08): optional input.excel source
  contract, current-result preflight, JSON/HTML/results-sheet parity, collision and
  source-overlap guards, text safety, protected destinations and partial-write
  reporting. Preserve valid policy-only export/save independently of freshness.
- [ ] **E-06 — Mac acceptance and regressions** (R-06, AC-07/09/10): execute
  acceptance.md, retain synthetic fixture/policy identities and actual results;
  run 50,000 rows, all repository checks and both runtime smoke modes; update user
  docs/support claims and the local/master handoffs. Record review status separately.

## Acceptance ledger

| Criterion | State | Evidence required |
| --- | --- | --- |
| AC-01 | pending | Source/bounds/visibility/totals fixtures and live table capture |
| AC-02 | pending | Source/policy/date/calculation invalidation and fresh rerun |
| AC-03 | pending | Interleaved edits, missing events and pre-action rejection |
| AC-04 | pending | Row/cell/ambiguous/group/missing navigation evidence |
| AC-05 | pending | Both epochs with explicit interpretation and matching dates |
| AC-06 | pending | Canonical JSON/HTML/sheet counts and unchanged source cells |
| AC-07 | pending | Recorded real Mac correction/rerun/export and CLI comparison |
| AC-08 | pending | Capability/calculation/input/write failure recovery |
| AC-09 | pending | Full checks and CDN/bundled/offline regression runs |
| AC-10 | pending | 50,000-row planted findings, timings, bounds and integrity |

No acceptance row is complete merely because the baseline tests passed previously.
