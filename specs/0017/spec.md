# 0017 — Canonical master handoff enforcement

**Status:** Implemented and locally verified. Updated 2026-11-14.

## Problem statement

The master handoff can fall behind commits despite repository instructions.
Author-only hooks do not require updates, preserve history or identify a pickup.

## Motivation and use cases

Every project commit leaves a reviewable checkpoint. New sessions start from
docs/handoff.md for work state and priorities, then consult the owning spec.

## Goals

- Make docs/handoff.md canonical for project status, ordered future priorities,
  last work, stopping point and next pickup. Numbered spec.md remains canonical
  for requirements; local handoffs and the roadmap defer to the master on order.
- Block commits and pushes without a matching staged/committed checkpoint.
- Generate Git context from actual Git objects, without inventing work/priorities.
- Preserve historical entries; allow corrections only through new entries.
- Run the same integrity checks in CI, including when local hooks are bypassed.

## Non-goals

Hooks cannot judge the truth of prose, select priorities or prevent every
intentional bypass. Required remote branch protection is an administrative
setting outside this change. No financial/runtime API change is involved.

## Proposed architecture

One standard-library script, scripts/check_handoff.py, owns validation and an
explicit --refresh operation for the Git-owned Commit context section. The
pre-commit hook validates the index, never the unstaged working copy. Pre-push
validates every outgoing branch commit. A separate CI workflow checks PR/push
ranges with full history. Existing author checks remain active.

## Public API design

No public finassert API. Developer CLI modes: --staged, --refresh, --commit REV,
--range BASE TIP, --history TIP and --pre-push (Git's ref-update stdin).
Refresh writes the working document only, never stages prose or changes commits.

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

## Implementation milestones

H-01 validator and meaningful Git fixtures; H-02 hook/CI integration and operating
instructions; H-03 initial checkpoint, verification and delivery. See [plan](plan.md),
[tasks](tasks.md) and [roadmap](roadmap.md).

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

## Testing requirements

Use disposable local repositories with actual staged and committed Git objects
and real hook processes. Test failures and passing recovery, multi-ref pushes,
bootstrap/legacy history, deletion/rename, merge/squash and missing objects.
Run focused pytest, Ruff, strict docs, local links/anchors, whitespace and a dry
run against this repository. No browser/financial behavior changes need rerunning.

## Dependencies on other specifications

Repository AGENTS.md and the numbered-spec workflow remain intact. This tooling
wraps every spec without changing its requirements or existing public contracts.
[0016](../0016/spec.md) remains the highest product priority after this guard work.

## Explicit deferred work

Automatic semantic summaries, priority ranking, scheduled updates without commits,
remote branch-protection changes, signed attestations and immutable audit storage.
