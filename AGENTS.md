# Repository instructions

Read the current state and newest entry in [the master handoff](docs/handoff.md)
and the [spec catalog](specs/README.md) before starting project work.

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

Use the verification commands in [CONTRIBUTING.md](CONTRIBUTING.md) and the
relevant spec plan. For documentation-only changes, verify links, anchors, and
the strict docs build; rerun runtime checks when implementation changes.
