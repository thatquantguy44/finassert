# 0004 — DataFrame adapters: tasks

[Spec](spec.md) · [Plan](plan.md) · [Tasks](tasks.md) · [Roadmap](roadmap.md) ·
[Contracts](contracts.md) · [Handoff](handoff.md) · [Agent instructions](AGENTS.md)

Baseline recorded 2026-11-13. Checked items identify existing implementation, not full
acceptance certification.

## Existing baseline

- [x] Mapping/record extraction, pandas identity preservation, and immutable column
  mappings exist.
- [x] Group keys, explicit field aggregations, and grouped-rule contracts exist.

## Remaining work, in order

- [ ] Reject unequal value/label lengths from ColumnSource before evaluating a rule;
  review reproduced a weight-rule PASS for values=[1], labels=[].
- [ ] Build one shared adapter suite covering mappings, row records, pandas, and Excel,
  including alignment and non-mutation.
- [ ] Retain source row identity when invalid weight values are reported after null
  filtering; coordinate with 0005.
- [ ] Resolve whether production FIRST/LAST aggregation requires an explicit ordering
  column with 0002.

Record evidence in [handoff.md](handoff.md) before checking off work.
