# 0012 — Seven-priority delivery: plan

1. Commit the numbered-spec migration and this ordered delivery tracker as the
   branch foundation; open a draft PR against `main`.
2. Implement the seven gates in [tasks.md](tasks.md), verifying each gate before
   beginning its successor. Keep separate commits for reviewable milestones.
3. Amend the owning spec before publishing new APIs or changing serialized
   behavior; keep migration notes in the owning contracts file.
4. Update local handoffs, the master handoff, and the draft PR as gates complete.

Run focused regression/property tests during each gate. Before final delivery,
run the full tests, Ruff lint/format, mypy, strict docs build, package build, author
policy check, and whitespace check. Exercise the CLI through real subprocesses
and retain benchmark results. Do not merge or publish a release.
