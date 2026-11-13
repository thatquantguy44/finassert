# Specification workspace instructions

- Every spec lives in `specs/NNNN/`, using a permanent four-digit number.
- Each numbered folder must contain `spec.md`, `plan.md`, `tasks.md`, `roadmap.md`,
  `AGENTS.md`, `contracts.md`, and `handoff.md`. Use `_template/` for new specs
  and update the catalog in `README.md`.
- Read the local instructions, spec, contracts, tasks, and newest handoff before
  related implementation work. Use the plan for approach and verification.
- Keep `spec.md` as the normative source. Companion files reference contracts
  instead of defining conflicting copies. Preserve explicit proposed/deferred
  labels until implementation and acceptance evidence support a status change.
- Changes to outcomes, rule identity, tolerance mathematics, serialization, or
  adapter row identity require a spec amendment and migration note.
- Update tasks only with evidence. Keep local handoff entries factual, newest
  first, and append-only; update its current-state summary separately.
- Reflect project-wide decisions and cross-spec effects in `docs/handoff.md`
  and `docs/roadmap.md`. Preserve historical master handoff entries, including
  old paths when they describe the state at the time.
- When reorganizing documents, update active links and verify local targets and
  anchors plus the strict documentation build. Runtime checks are needed when
  implementation changes, not merely when documentation moves.
