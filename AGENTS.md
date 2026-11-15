# Repository instructions

Read the current state and newest entry in [the master handoff](docs/handoff.md)
and the [spec catalog](specs/README.md) before starting project work.
The master is canonical for project status, highest priorities, work history and
the next pickup. Local handoffs and the roadmap defer to its project ordering;
numbered spec.md files remain canonical for requirements.

Each specification lives in a permanent four-digit folder, `specs/NNNN/`, with
`spec.md`, `plan.md`, `tasks.md`, `roadmap.md`, `AGENTS.md`, `contracts.md`, and
`handoff.md`. Use `specs/_template/` for new specs and update the catalog. Do not
create new flat spec files.

For implementation work, consult the relevant spec folder's agent instructions,
requirements, contracts, tasks, and newest handoff even when editing code outside
that folder. Keep proposed and deferred capabilities explicitly labeled.

Keep requirements canonical in `spec.md`. Record task completion with verification
evidence and add a local handoff entry when work finishes. Reflect cross-spec
decisions and overall next steps in the master handoff and project roadmap.
Preserve historical handoff entries; append corrections instead of rewriting them.

Every nonempty commit requires a new master checkpoint. Keep its Current state
fields and newest entry aligned, and review the ordered Next up priorities.
Stage intended work and master prose, run
`python3 scripts/check_handoff.py --refresh`, then explicitly stage
`docs/handoff.md` again. Refresh generates Git context only; never invent priorities
or claim unperformed verification. Commit/push hooks and CI check the actual
index/history. See [the checkpoint workflow](CONTRIBUTING.md#master-handoff-checkpoints).

Use the verification commands in [CONTRIBUTING.md](CONTRIBUTING.md) and the
relevant spec plan. For documentation-only changes, verify links, anchors, and
the strict docs build; rerun runtime checks when implementation changes.
