# Contributing

Thank you for improving `finassert`. Open an issue before substantial API or
financial-semantics changes. A rule proposal should state the invariant, units,
sign convention, null policy, tolerance basis, failure diagnostics, and cases in
which the rule is inappropriate.

## Specification workspaces

Create each spec in its own permanent four-digit directory, `specs/NNNN/`, with
`spec.md`, `plan.md`, `tasks.md`, `roadmap.md`, `AGENTS.md`, `contracts.md`, and
`handoff.md`. Start from `specs/_template/` and update the
[spec catalog](specs/README.md). Additional decision records or artifacts belong
inside that spec's folder.

Keep requirements canonical in `spec.md`; use the companion files for execution,
contract references, and evidence. Update local tasks and handoffs as work
progresses, and record cross-spec decisions in the master handoff.

## Development

Install [uv](https://docs.astral.sh/uv/), then run:

```bash
uv sync --all-extras --dev
git config --local core.hooksPath .githooks
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy src/finassert
uv run mkdocs build --strict
uv build
uv run python scripts/verify_dist.py dist
```

## Master handoff checkpoints

[docs/handoff.md](docs/handoff.md) is canonical for project status, ordered future
priorities, recent work, stopping point and next pickup. Local handoffs and the
roadmap link back to that ordering; requirements stay in numbered spec.md files.
Every nonempty project commit, including docs/tooling, needs a new checkpoint.

1. Update Current state: Last worked on, Stopping point, Highest priority,
   Next pickup and Verification. Highest priority must match the title of Next up
   item 1. Keep the numbered list ordered; unchanged priorities can be reaffirmed.
2. Prepend a dated entry with Worked on, Stopping point, Priorities, Next pickup
   and Verification matching those current fields. Preserve older Entries verbatim;
   append corrections in the new entry. If no active pickup exists, explain that
   explicitly instead of leaving a placeholder.
3. Stage the intended changes and handoff prose, then run:

   ```bash
   python3 scripts/check_handoff.py --refresh
   git add -- docs/handoff.md
   python3 scripts/check_handoff.py --staged
   git commit
   git push
   ```

Refresh updates only the Git-owned Commit context section and never stages files.
It records actual prior commits, staged paths and snapshot digests. Restaging is
explicit; later staged changes require refresh again. Unstaged edits do not count.
Run the helper from any directory inside the checkout.

Activate tracked hooks in each clone with
`git config --local core.hooksPath .githooks`. The commit hook retains the author
check and adds staged handoff validation. The push hook inspects every outgoing
branch commit, including commits made with a bypass; new/force-updated branches
are checked and deletions/tag-only updates do not fabricate new work.
Force updates must preserve published checkpoint history. Fetch first if the
remote commit is unavailable locally; the guard will not guess its priorities.
CI's **Master handoff / checkpoint** check repeats validation with full Git history.
Require that status check in remote branch protection when enabling repository-wide
merge enforcement; this change does not modify remote administrative settings.

The enclosing commit cannot contain its own SHA. Commit context lists the actual
commits before that checkpoint; `git log -5 --oneline` or GitHub's file history
shows the current commit. Unchanged complete snapshots can carry through server
merge/squash commits. Integration that changes source content requires a refreshed
checkpoint. Rebase/amend also requires refreshing after the changed Git context.
Older pre-policy commits are historical; deleting an active checkpoint fails.
If push/CI names an earlier invalid commit, repair that unpublished commit and
refresh its checkpoint. A later valid handoff does not repair a missing entry in
an earlier commit. The guard never rewrites history on your behalf.

Hooks can be bypassed locally and cannot judge whether prose is true. Contributors
must review priorities, describe the actual work and report verification honestly;
the checks enforce checkpoint presence, consistency and snapshot integrity.
See [spec 0017](specs/0017/spec.md) for the exact contract.

Maintainers: see [releasing](docs/releasing.md).

Public APIs require type annotations and Google-style docstrings. Tests should
cover boundaries, nulls, empty data, non-finite values, and Decimal behavior as
applicable. Use synthetic data and do not commit credentials or proprietary data.

Commits must satisfy the configurable identity rules in `.author-policy.toml`.
The tracked `.githooks/pre-commit` hook checks the effective Git author, and CI
checks every author in repository history. Activate the tracked hooks with the
command above. Update the policy through review when maintainers or accepted
identities change; common AI-agent identities remain blocked.

By participating, you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).
