# 0018 — Handoff

## Current state

The local-default reader, explicit pinned-GitHub API and Excel panel are
implemented on `feature/excel-e06-mac-acceptance`. The supplied checkout at
`/Users/joshualutkemuller/Documents/Quant Sandbox/agentic_workflows/qf_workflow_sdk_public`
is pinned at `d090cc3e7ddd6066fdef14bdfa76262f37c5ff50` and serves 1,426
allowlisted documents through localhost HTTPS. The full runtime and bundled
browser suites pass. Native pane inspection remains a separate E-06 task.
Follow the master handoff for overall priority.

## Entries

### 2026-11-20 — Local default and GitHub-selectable reference

- **Work:** Repointed the reviewed lock to the supplied local QuantSmith commit,
  made that checkout the default for the local server, and added an explicit
  GitHub Git-object source for local owners.
- **Verification:** The local HTTPS catalog returns 1,426 pinned allowlisted
  documents. Synthetic GitHub-source coverage verifies token forwarding, tree
  filtering, exact blob verification and raw-text reader behavior. Full runtime
  (3,744) and browser (111) suites pass.
- **Boundary:** GitHub is never the default, runs only through the local
  loopback server, accepts credentials only from the local process environment,
  and never receives workbook or policy data. No native pane acceptance or
  shared-hosting claim is made.

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
