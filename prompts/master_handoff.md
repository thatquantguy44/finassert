# Implement Canonical Handoff and Documentation Enforcement

Implement a canonical handoff and documentation enforcement workflow in this repository. Complete the implementation and verification, not just a plan.

First inspect repository instructions, existing handoffs, documentation conventions, Git hooks, local tasks and CI. Preserve existing checks, author policies and unrelated work.

Use the existing master handoff path. If none exists, use `docs/handoff.md`. Avoid creating competing master documents.

## Operating Modes

Support both Git mode and local filesystem mode.

- **Git mode:** Use when Git is available and the directory is a valid repository. Git can operate entirely locally without a remote or network access.
- **Filesystem mode:** Support operation without Git using explicit local checkpoint commands and filesystem snapshots.
- Record the selected mode clearly. Do not fabricate Git references in filesystem mode.
- Do not silently switch modes to bypass Git conflicts, shallow history, unknown remote history or failed validation.
- Do not initialize Git or replace the repository’s existing workflow merely to avoid implementing filesystem mode.
- A filesystem checkpoint must not be represented as satisfying Git commit, push or CI checks.

Prefer the repository’s existing runtime and tooling. Keep the checker dependency-free where practical.

## 1. Canonical Authority

Make the master handoff authoritative for:

- Current project status.
- Work completed and items worked on.
- Current stopping point.
- Ordered future priorities.
- Verification results and limitations.
- The next actionable pickup point.

Local handoffs and roadmaps must defer to the master’s project ordering. Keep specifications authoritative for requirements and contracts.

Update contributor and agent instructions so future work starts by reading the master’s current state and newest entry.

Do not invent priorities, task completion, commit references or verification evidence.

## 2. Complete Checkpoints

In Git mode, require every nonempty project commit—including code, tests, configuration, tooling and documentation—to update the master and prepend a dated checkpoint entry.

In filesystem mode, detect project changes since the accepted baseline and require a complete new checkpoint before accepting the next baseline.

Require meaningful fields for:

- Work performed.
- Stopping point.
- Highest priority.
- Next pickup.
- Verification.

Current-state fields must agree with the newest checkpoint entry. The highest priority must match the title of item 1 in the ordered `Next up` list.

Reject empty fields, template placeholders, duplicate required sections and inconsistent fields.

Allow unchanged priorities to be explicitly reaffirmed. If no active pickup exists, require an explanation rather than an empty field or unexplained placeholder.

Do not fabricate work for genuinely empty commits or no-op checkpoints.

## 3. Preserve History

Preserve previous handoff entries verbatim. Record corrections in new entries instead of rewriting historical records.

Bootstrap enforcement without retroactively rejecting legitimate pre-policy history.

In filesystem mode, retain the previous accepted handoff snapshot so historical changes can be detected.

Missing, damaged or incompatible baseline state must require explicit recovery. Never silently reset the baseline and claim history was verified.

## 4. Generated Checkpoint Context

Keep generated context in a clearly marked machine-owned section. Human-owned status, priorities and explanations must remain manually reviewed.

### Git Mode

Provide an explicit refresh command that generates context from actual Git objects, including:

- Prior HEAD.
- Recent commits and their subjects.
- Changed paths.
- A digest of the staged project snapshot.
- A digest of the reviewed handoff sections.

Validate staged objects, not unstaged working files. Respect partial staging.

Refresh must update only generated context. It must not automatically stage files, overwrite unstaged prose, rewrite commits or invent summaries.

Require explicit restaging after refresh. Detect staged changes made afterward.

Avoid circular hashes by excluding the master from the project snapshot digest and validating its reviewed content separately.

Explain that a commit cannot contain its own SHA. Record actual preceding commits and use Git/file history to identify the enclosing checkpoint.

### Filesystem Mode

Provide explicit `init`, `check`, `refresh-context` and `checkpoint` commands, or equivalent commands consistent with repository conventions.

Use:

- Configured project-file inclusion and exclusion rules.
- Relative paths and content hashes.
- Versioned baseline state.
- Previous accepted handoff snapshots.
- Explicit checkpoint IDs and timestamps.

Exclude generated state, dependency directories and build outputs through documented configuration.

Keep `check` read-only. Refresh only machine-owned context. Advance the accepted baseline only through an explicit checkpoint command after successful validation.

Update machine-owned state atomically and detect project changes occurring after context generation.

Never fabricate commit SHAs, branches, remotes or PR links.

## 5. Enforcement

### Git Mode

Integrate with existing pre-commit hooks to reject missing, incomplete or stale staged checkpoints. Preserve existing author, formatting and other checks.

Add pre-push validation of every outgoing branch commit, including bypassed intermediate commits—not merely the latest tip.

Handle:

- New branches and root commits.
- Force updates.
- Branch deletions and tag-only updates.
- Unknown remote/base history.
- Merge and squash workflows.
- Shallow repositories.

Reject updates that discard published handoff history. Require fetching unknown remote/base history rather than guessing its contents.

Support transport of unchanged complete checkpoint snapshots through merge/squash operations. Integration that changes the project snapshot requires refreshed context.

Add equivalent full-history CI checks using the repository’s existing CI platform.

Give actionable recovery instructions. A later valid checkpoint must not silently excuse an earlier invalid outgoing commit.

### Filesystem Mode

Run validation through explicit commands and integrate it with existing local test, build or task commands where practical.

Reject changed project content without a complete, current checkpoint.

Document that enforcement occurs when these commands or integrations run. Do not claim filesystem mode can block every arbitrary file edit.

## 6. Tests and Verification

Use temporary real Git repositories and actual hook processes for Git-mode tests.

Cover:

- Valid checkpoint creation and recovery.
- Missing checkpoints and required fields.
- Placeholders and inconsistent priorities/pickup fields.
- Unstaged edits and partial staging.
- Changes after refresh.
- Historical-entry modifications.
- Bypassed intermediate commits.
- Multiple pushed refs.
- Force rewinds and unknown remote history.
- Root and shallow repositories.
- Merge/squash behavior.
- Preservation of existing checks.

Test filesystem mode with Git unavailable. Cover:

- Baseline initialization.
- Changed, added, deleted and renamed files.
- Inclusion/exclusion rules.
- Missing or damaged state.
- Historical-entry changes.
- Stale context.
- Read-only validation.
- Atomic state updates and failed checkpoint recovery.

Run appropriate repository tests, formatting, documentation link/anchor checks and strict documentation builds.

Report actual results and distinguish carried-forward evidence from checks performed during this task.

## 7. Documentation and Delivery

Document:

- Canonical document ownership.
- Mode selection.
- Hook activation where applicable.
- Exact checkpoint and refresh commands.
- Baseline storage and exclusions.
- Recovery procedures.
- CI enforcement and its limitations.

Update contributor/agent instructions and the PR checklist where applicable.

Bootstrap the master with truthful status, reviewed priorities, verification and an actionable next pickup.

Delivery depends on available infrastructure:

- **Git with an authorized writable remote:** Work on a feature branch, commit, push and create a PR after verification.
- **Git without a remote:** Complete and commit locally; report the commit and remaining remote-delivery steps.
- **Without Git:** Complete a validated local checkpoint and report its identity, changed files and next pickup. Do not attempt branch, commit, push or PR operations.

Do not merge or change remote branch protection automatically. Where CI exists, report the exact check administrators should require for remote merge enforcement.

Finish by reporting the implemented safeguards, verification results, delivery references, remaining limitations and next pickup.

Be explicit: these checks enforce checkpoint integrity, freshness and consistency. Humans remain responsible for semantic accuracy, honest verification claims and priority decisions.