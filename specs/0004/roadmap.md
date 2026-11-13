# 0004 — DataFrame adapters: roadmap

[Spec](spec.md) · [Plan](plan.md) · [Tasks](tasks.md) · [Roadmap](roadmap.md) ·
[Contracts](contracts.md) · [Handoff](handoff.md) · [Agent instructions](AGENTS.md)

## Current milestone

pandas, mapping, and grouped aggregation contracts implemented; Polars proposed. See
[tasks.md](tasks.md) for known gaps.

## Next milestone

Reject unequal value/label lengths from ColumnSource before evaluating a rule; review
reproduced a weight-rule PASS for values=[1], labels=[].

## Following milestones

Follow the remaining task order in [tasks.md](tasks.md) and the approach in
[plan.md](plan.md). Cross-spec sequencing belongs to the [project
roadmap](../../docs/roadmap.md).

## Deferred scope

See [explicit deferred work](spec.md#explicit-deferred-work). A local roadmap does not
promote deferred work into an implemented capability.
