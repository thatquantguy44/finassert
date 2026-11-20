# 0017 — Canonical master handoff enforcement

**Status:** Implemented in Git and filesystem modes. Updated 2026-11-19.

## Problem statement

The master handoff can fall behind commits despite repository instructions. A
Git-only checker also leaves local, non-Git project work without a way to retain
the same reviewed status, history and pickup discipline.

## Motivation and use cases

Every project commit or explicitly accepted non-Git filesystem checkpoint leaves
a reviewable handoff state. New sessions start from docs/handoff.md for work state
and priorities, then consult the owning spec.

## Goals

- Make docs/handoff.md canonical for project status, ordered future priorities,
  last work, stopping point and next pickup. Numbered spec.md remains canonical
  for requirements; local handoffs and the roadmap defer to the master on order.
- Block commits and pushes without a matching staged/committed checkpoint.
- Generate Git context from actual Git objects, without inventing work/priorities.
- Preserve historical entries; allow corrections only through new entries.
- Run the same integrity checks in CI, including when local hooks are bypassed.
- Provide a local filesystem mode when Git is unavailable, with explicit baseline,
  refresh, read-only check, checkpoint and recovery commands.

## Non-goals

Hooks cannot judge the truth of prose, select priorities or prevent every
intentional bypass. Required remote branch protection is an administrative
setting outside this change. No financial/runtime API change is involved.

## Proposed architecture

One standard-library script, scripts/check_handoff.py, owns validation in two
modes. In Git mode, an explicit --refresh operation updates the Git-owned Commit
context section. The pre-commit hook validates the index, never the unstaged
working copy. Pre-push validates every outgoing branch commit. A separate CI
workflow checks PR/push ranges with full history. Existing author checks remain
active.

Filesystem mode works without invoking Git. It stores one versioned accepted
baseline in the excluded `.finassert-handoff/state.json`, including configured
file hashes and the exact prior master-handoff text. `--filesystem-refresh-context`
updates only a separate machine-owned Filesystem checkpoint context in the master;
`--filesystem-check` is read-only; `--filesystem-checkpoint` atomically advances
the baseline only after a fresh check. `--filesystem-recover` requires explicit
confirmation and starts a new baseline rather than claiming old local history was
verified.

## Public API design

No public finassert API. Git-mode developer CLI modes are --staged, --refresh,
--commit REV, --range BASE TIP, --history TIP and --pre-push (Git's ref-update
stdin). Filesystem mode provides --filesystem-init, --filesystem-check,
--filesystem-refresh-context, --filesystem-checkpoint and --filesystem-recover
--confirm-filesystem-recovery. `--filesystem-root`, `--filesystem-state-dir`, and
repeatable `--filesystem-include` / `--filesystem-exclude` select the local
snapshot at initialization. Git refresh writes the working document only and
never stages prose or changes commits; filesystem refresh writes only its generated
context and does not advance the accepted baseline.

## Data contracts

The master requires unique Current state, Next up, Commit context and Entries
sections. Current state requires Last worked on, Stopping point, Highest priority,
Next pickup and Verification. Next up is a nonempty sequential numbered list;
its first item's title matches Highest priority. The newest dated entry requires
Worked on, Stopping point, Priorities, Next pickup and Verification, matching the
corresponding current fields. Empty/template placeholders are rejected.

Every nonempty commit must change the master and prepend a dated entry while
retaining the previous Entries body verbatim as a suffix. Historical pre-policy
commits are grandfathered; removing an activated checkpoint is an error. An empty
Git commit with an unchanged tree does not represent new project work.

Commit context v1 records prior HEAD, up to five actual recent first-parent
commits, changed paths, a SHA-256 of the project manifest excluding the master,
and a digest of reviewed current/priority/newest-entry text. The manifest covers
paths, modes and Git blob IDs, not unstaged files. Refresh requires staged prose
to equal working prose, then updates only this generated section. Restaging the
master is explicit. Checks never auto-stage or rewrite commits.

The enclosing commit cannot contain its own SHA. Recent commits therefore mean
commits before this checkpoint; the enclosing commit is available in Git/file
history. Staged checks require prior HEAD exactly. Committed checks allow merge
or squash transport of an unchanged complete project/checkpoint snapshot, with
the original Git context retained. References are checked against actual objects
when available; rewritten/deleted source histories can leave archived references
unavailable. Full-history checkout is required. Integration changing the project
snapshot requires a refreshed checkpoint, rather than trusting old source context.

Filesystem state v1 records `mode: filesystem`, configured include/exclude rules,
an opaque `fs-` checkpoint ID and UTC acceptance time, content hashes for every
included relative file (including the master), the master snapshot digest and its
complete accepted text. The project digest excludes the self-referential master;
the file snapshot and changed-path list still include it. Default exclusions cover
version-control metadata, virtual environments, caches, build/distribution/site
outputs, dependency directories and the state directory itself. A user may narrow
or extend rules only during initialization or explicit recovery; the saved rules
are hashed into each refreshed context. Symlinks are recorded by link target rather
than followed outside the project root.

Filesystem context v1 contains no Git references. It records its pending ID,
accepted baseline ID, UTC generation time, changed relative paths, project and
configuration digests, and a digest of the human-reviewed master sections. A
changed local project must have a new complete handoff entry and a fresh context
before it can become the next baseline. A missing, damaged or incompatible state
file fails closed. Recovery is deliberate and retains no claim that discarded local
history was checked.

Push checks handle multiple refs, new branches, force updates and deletions.
Only branch updates contain new work; tag-only/deletion updates do not require a
new handoff. Nonzero remote/base objects must be available: otherwise require a
fetch instead of guessing remote priorities. Even force updates must retain the
remote/base master entry history; rewinding to an older checkpoint is rejected.

## Financial and numerical edge cases

Not applicable: no financial calculations, data adapters or outcome changes.

## Failure semantics

Fail with recovery instructions for missing updates, placeholders, mismatched
fields, modified history, stale generated context, unresolved index conflicts,
shallow history or unreadable Git state. No silent exemption or auto-generated
priority text. Valid unchanged priorities may be reaffirmed in a new checkpoint.
Filesystem checks are read-only and likewise fail for missing/damaged baseline
state, configuration drift, rewritten entries, changed paths after refresh or an
unaccepted pending checkpoint. They do not block arbitrary file edits unless the
explicit commands are run.

## Implementation milestones

H-01 validator and meaningful Git fixtures; H-02 hook/CI integration and operating
instructions; H-03 initial checkpoint, verification and delivery; H-04 filesystem
baseline/checkpoint enforcement. See [plan](plan.md), [tasks](tasks.md) and
[roadmap](roadmap.md).

## Open questions

None for this scope. Local hooks need core.hooksPath=.githooks in each clone.
Remote enforcement depends on retaining the workflow and requiring its check.

## Acceptance criteria

1. Code/spec/docs changes without a new master checkpoint fail local commit/push
   and committed-range validation; unstaged handoff edits cannot satisfy a commit.
2. Missing fields, reordered first priority, modified old entries and stale Git
   context fail with actionable messages. Honest unchanged priorities pass.
3. Recent commits/paths correspond to Git; partial staging, filenames with spaces,
   root/new branches and transport through unchanged merge/squash snapshots work.
4. A deliberately bypassed commit is rejected on push/CI; hooks preserve author
   enforcement and do not stage unrelated work. Full history is checked.
5. The initial master checkpoint names the stopping point and E-04 pickup;
   docs/roadmap and local records defer to that project ordering.
6. In a non-Git directory, initialize a filesystem baseline, detect changed,
   added, deleted and renamed configured files, reject stale/re-written/damaged
   checkpoints, and accept a fresh checkpoint atomically. Filesystem state never
   claims a Git commit, push or CI result.

## Testing requirements

Use disposable local repositories with actual staged and committed Git objects
and real hook processes. Test failures and passing recovery, multi-ref pushes,
bootstrap/legacy history, deletion/rename, merge/squash and missing objects.
Run focused pytest, Ruff, strict docs, local links/anchors, whitespace and a dry
run against this repository. No browser/financial behavior changes need rerunning.
Use non-Git temporary directories for filesystem init/check/refresh/checkpoint and
recovery. Cover configured inclusion/exclusion, additions/deletions/renames,
master-history preservation, post-refresh changes, read-only checks, damaged state
and explicit recovery. Do not call a Git helper in those tests.

## Dependencies on other specifications

Repository AGENTS.md and the numbered-spec workflow remain intact. This tooling
wraps every spec without changing its requirements or existing public contracts.
[0016](../0016/spec.md) remains the highest product priority after this guard work.

## Explicit deferred work

Automatic semantic summaries, priority ranking, scheduled updates without explicit
Git commits or filesystem checkpoints, remote branch-protection changes, signed
attestations and immutable audit storage.
