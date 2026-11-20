# 0017 — Canonical master handoff: handoff

## Current state

- **Status:** Git safeguards remain implemented; the explicit filesystem-only
  baseline/checkpoint workflow is now implemented and covered by non-Git fixtures.
- **Branch:** `feature/excel-e06-mac-acceptance`; filesystem work is uncommitted
  beside the current add-in work.
- **Next step:** Follow the master's highest priority: 0016 E-06 full Mac
  acceptance and regressions. Required remote status administration remains
  separate from this implementation.

## Entries

### 2026-11-19 — Complete non-Git filesystem checkpoint workflow

The portable prompt's previously missing filesystem mode is now implemented in
`check_handoff.py`. A non-Git project can explicitly initialize a versioned local
baseline, refresh only generated Filesystem checkpoint context, run a read-only
check and atomically accept a fresh checkpoint. State retains configured content
hashes and the accepted master snapshot under ignored `.finassert-handoff/`.
Damaged/missing state fails closed; recovery requires an explicit confirmation and
does not claim prior local history was verified. The seven new filesystem fixtures
run with Git absent from `PATH`; Git hooks, CI and Git-mode behavior remain intact.
The master still owns project priority, so E-06 remains the next product pickup.

### 2026-11-15 — Save portable prompt on main

PR #25 merged at 32cf4ab. The user requested saving the existing untracked
[reusable prompt](../../prompts/master_handoff.md) directly on main. Its Git and
filesystem-mode requirements are prompt content for other repositories; this
documentation commit does not add a filesystem backend to finassert's checker.
The master records the merge and keeps E-04 as the next pickup. Links/anchors,
strict docs, whitespace and the real staged handoff/author checks are verified;
runtime evidence is carried forward because implementation code is unchanged.

### 2026-11-15 — PR opened for the delivered guards

Commit e8d3526 passed its real author/checkpoint commit hooks, pre-push history
guard and [push CI](https://github.com/thatquantguy44/finassert/actions/runs/43675401872).
[PR #25](https://github.com/thatquantguy44/finassert/pull/25) now includes this
implementation together with Excel E-01–E-03. The current update records delivery;
documentation/guard checks are repeated, with runtime evidence carried forward.
Remote branch protection and merging remain separate; the master still names
E-04 as the highest product priority and pickup.

### 2026-11-14 — Initial master checkpoint verified

The actual index failed validation when project changes were staged without the
master. Explicit Git-context refresh/restaging then passed both direct staged
validation and the full author/handoff pre-commit hook. Full suite: 3,662 passed,
72 browser cases skipped; the focused Git suite's 38 tests pass. Ruff/format,
mypy across 62 source files, strict docs and 100 local links/anchors pass.
The master now owns status/order/pickup and has actual recent commit/path context;
historical entries remain untouched. The product pickup remains E-04. Delivery
will use the installed guarded commit/push path; see the enclosing Git commit.

### 2026-11-14 — Implement staged, push and CI checkpoint guards

- **Done:** Standard-library validator; explicit generated-context refresh;
  author-preserving pre-commit and new pre-push hooks; full-history CI check;
  canonical authority and checkpoint instructions; initial complete master entry.
- **Evidence:** 38 tests pass using disposable actual Git repositories and hooks.
  A missing checkpoint fails commit, a bypassed commit fails push, invalid author
  still fails, and a corrected checkpoint commits/pushes. Tests include stage
  isolation, immutable history, matching priority/pickup, fresh Git metadata,
  root/subdirectory/shallow cases, unknown remote fetch requirements, multiple
  refs, safe force updates and rejection of history-dropping force rewinds.
  Identical project snapshots pass merge/squash transport, including archived
  context after source objects are pruned; integration changes fail verification.
- **Decision:** Require known remote/base history rather than accepting a local
  fallback that could discard a newer published priority/checkpoint.
- **Limits:** Semantic correctness needs contributor review; remote branch
  protection must require the new check for server merge enforcement. It was
  not changed here. No financial/runtime behavior or product-priority change.
- **Next:** Verify the real staged checkpoint/delivery, then follow the master.

### 2026-11-14 — Scope canonical checkpoint enforcement

The user requested hooks to keep the master authoritative and current with work,
priorities, commits and pickup. Defined staged/index checks, pre-push/CI history,
explicit Git-context refresh and preservation of old entries. Semantic review
remains the contributor's responsibility; requirements stay in numbered specs.
