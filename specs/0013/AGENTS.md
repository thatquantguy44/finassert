# Spec 0013 agent instructions

Follow [the shared spec instructions](../AGENTS.md). Read this folder's [spec](spec.md),
[contracts](contracts.md), [tasks](tasks.md), and newest [handoff](handoff.md) before
related implementation work.

Scope: Excel workbook integration. Relevant implementation areas:
[src/finassert/excel.py](../../src/finassert/excel.py),
[tests/integration/test_excel_reader.py](../../tests/integration/test_excel_reader.py),
[pyproject.toml](../../pyproject.toml).

Preserve these review constraints:

- Worksheet row numbers remain default labels, and reading never modifies the source
  workbook.
- Cached values are not recalculated; an unreadable or uncached formula region cannot
  pass silently.
- Error markers are distinct from nulls; Decimal report values and formula-like strings
  are written as text.

Use [plan.md](plan.md) for the approach and its verification command. Update task
evidence and the local handoff when work finishes; reflect cross-spec effects in the
master handoff.
