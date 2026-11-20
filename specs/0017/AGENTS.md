# Spec 0017 agent instructions

Follow [the shared spec instructions](../AGENTS.md). Read the local [spec](spec.md),
[contracts](contracts.md), [tasks](tasks.md), and newest [handoff](handoff.md)
before related implementation work.

Scope: `scripts/check_handoff.py`, tracked Git hooks, CI, the explicit non-Git
filesystem checkpoint workflow and repository working instructions. Use
standard-library Python, actual Git fixtures for Git behavior, and isolated
non-Git fixtures for filesystem behavior. Never stage unrelated work, invent
semantic summaries/priorities, rewrite commit history or replace historical
master entries. Index checks must use staged content; filesystem state must stay
local, ignored and explicit about its recovery limits. Keep the existing author
policy. Document enforcement limits honestly. Follow the [plan](plan.md); record
evidence in [tasks](tasks.md) and [handoff](handoff.md). No sub-agent delegation
is requested.
