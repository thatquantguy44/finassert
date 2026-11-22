# 0020 — Performance and backtest integrity tasks

| ID | Work | Acceptance | Status |
|---|---|---|---|
| P-01 | Scope the performance workbook, proposed interfaces, and later milestones, and add the numbered workspace to the catalog and roadmap | Proposal review | Done, [handoff](handoff.md) |
| P-02 | Review policy metadata, public rule shape, and numeric precision. Prepare independent synthetic fixtures and expected values | AC-01, AC-02, AC-03 | Done; see [decisions](decisions.md) and [fixtures](artifacts/fixtures/expected.json) |
| P-03 | Implement monthly coverage preflight and shared reference calculations | AC-01, AC-02 | Done; AC-01/AC-02 fixtures pass in [acceptance tests](../../tests/unit/test_performance.py) |
| P-04 | Register one composite monthly audit rule and starter policy with bounded diagnostics; export explicit and effective parameters for full policy traceability | AC-03, AC-05 | Implemented; AC-03 and CLI/report parameter traceability verified. Full AC-05 Excel parity remains for P-05/P-06. Tracking: [issue #31](https://github.com/thatquantguy44/finassert/issues/31) |
| P-05 | Author the Excel workbook and Python/CLI example, including a seeded correction case | AC-04, AC-05 | Proposed; next spec task |
| P-06 | Verify native Excel, exports, and CLI parity and update the guide and package evidence | AC-01–AC-05 | Proposed |
| P-07 | Specify point-in-time inputs and the walkthrough acceptance before implementation | Milestone 2 review | Proposed |
| P-08 | Specify minimum-variance inputs, independent checks, and the reference solver example before implementation | Milestone 3 review | Proposed |

The [spec](spec.md#acceptance-criteria) owns the acceptance criteria. Add actual
verification to the task record and [handoff](handoff.md) as work lands.
