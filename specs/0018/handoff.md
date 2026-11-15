# 0018 — Handoff

## Current state

The local reader, pinned Git API and Excel panel are implemented on
`feature/quantsmith-readonly-docs`. Draft PR #28 now targets main after the
earlier stacked PR merged into the already-merged Excel branch. The full Linux runtime and bundled browser
suites pass, including synthetic Git/API and panel coverage. A private QuantSmith
checkout is unavailable in this execution workspace, so no live private-file service or Mac Excel observation
is claimed. Follow the master handoff for overall priority.

## Entries

### 2026-11-15 — Direct delivery PR after stacked merge

PR #26 merged Excel into main before PR #27 merged this reference into the
Excel branch. Draft PR #28 now compares the same QuantSmith reader directly to
main: 27 changed files, mergeable. No reader code changed in this
checkpoint. Private-checkout and native Mac inspection remain pending.

### 2026-11-15 — Initial local pinned reader

- **Work:** Added the commit lock, bounded Git blob catalog, opt-in localhost
  API, and on-demand Excel reference panel. Private content stays in the
  separate checkout. The pane displays raw text and never executes agent files.
- **Verification:** 3,700 runtime tests and 107 bundled browser tests pass;
  the reference checks use a synthetic Git checkout and mocked browser API.
  Both Excel smoke modes and shared web smoke pass. No live private checkout
  or native Mac Excel run was available.
- **Next:** Obtain a local QuantSmith checkout and Mac Excel host to verify
  the real add-in, then decide separately whether authenticated shared hosting
  is needed.
