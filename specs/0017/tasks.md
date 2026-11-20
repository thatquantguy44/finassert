# 0017 — Canonical master handoff: tasks

- [x] Define scope, master/spec authority, staged boundaries and merge semantics.
- [x] H-01: implement refresh/validation, history protection and real Git tests.
  Evidence: 38 passing tests in tests/unit/test_handoff.py, including actual hooks,
  bypassed commits, staged versus unstaged data, force rewind rejection, archived
  squash context, shallow history, root commits, conflicts and unchanged priorities.
- [x] H-02: wire hooks/CI and document setup and checkpoint workflow.
  Existing author checks retained; pre-push executable added; dedicated full-history
  workflow and contributor/agent instructions define master/spec authority.
- [x] H-03: bootstrap the master and verify the real staged checkpoint.
  Actual repository check rejected staged work without a staged master, then
  passed after explicit refresh/restaging. Both the author and handoff pre-commit
  checks passed. Full suite: 3,662 passed / 72 browser cases skipped; Ruff/format,
  mypy (62 files), strict docs and 100 local links/anchors passed. Delivery uses
  the same guarded commit/push path; the enclosing commit is available in Git.
- [x] H-04: implement an explicit filesystem baseline/checkpoint workflow for
  non-Git directories. State retains configured hashes and prior handoff text;
  refresh is context-only, check is read-only, checkpoint advances atomically and
  recovery requires confirmation. Evidence: seven non-Git fixture cases cover init,
  no-Git execution, add/delete/rename, rules/exclusions, history/stale rejection,
  read-only checks and damaged-state recovery.

Remote branch-protection administration and a main-branch merge are outside this
implementation; require the new CI status there to enforce server-side merging.
