# 0018 — Handoff

## Current state

The local reader, pinned Git API and Excel panel are implemented on
`feature/quantsmith-readonly-docs`. The full Linux runtime and bundled browser
suites pass, including synthetic Git/API and panel coverage. A private QuantSmith
checkout is unavailable in this execution workspace, so no live private-file service or Mac Excel observation
is claimed. Follow the master handoff for overall priority.

## Entries

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
