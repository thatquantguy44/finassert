# 0013 — Excel workbook integration: plan

[Spec](spec.md) · [Plan](plan.md) · [Tasks](tasks.md) · [Roadmap](roadmap.md) ·
[Contracts](contracts.md) · [Handoff](handoff.md) · [Agent instructions](AGENTS.md)

1. Close formula/error-cell correctness gaps before extending workbook capabilities.
2. Verify shared adapter contracts and workbook edge cases without modifying input
   workbooks.
3. Implement the basic report writer, then coordinate CLI flags with 0007 and structured
   diagnostics with 0005.

Implementation areas: [src/finassert/excel.py](../../src/finassert/excel.py),
[tests/integration/test_excel_reader.py](../../tests/integration/test_excel_reader.py),
[pyproject.toml](../../pyproject.toml).

Dependencies and acceptance requirements remain in
[spec.md](spec.md#dependencies-on-other-specifications).

Verification from the repository root:

```bash
PYTHONPATH=src .venv/bin/python -m pytest -q tests/integration/test_excel_reader.py tests/unit/test_adapter_contracts.py
```

This command covers the existing baseline. Add focused coverage for new behavior as
tasks are implemented.
