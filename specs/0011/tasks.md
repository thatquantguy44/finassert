# 0011 — Tasks

- [ ] Audit the current main implementation against the remaining spec milestones.
- [ ] Keep deferred live-Excel and hosted-service work outside the seven-priority delivery scope.

Initial policy, CLI, HTML, browser, assistant, and Excel add-in implementations exist on main.

- [x] Rename the expandable report to **Open Full Validation Report** and add
  **View Full Validation Report** beneath the run result banner. Actual narrow-pane
  pointer/keyboard/reduced-motion and historical-result checks pass; 39 affected
  unit/28 browser cases and shared browser/bundled Excel smoke pass. See the
  [latest handoff](handoff.md#2026-11-20-full-validation-report-navigation).

- [x] Distinguish native pane identities and display configured failure actions
  independently of outcomes; native demo, full runtime/browser, smoke, docs and
  distribution evidence are recorded in the latest local/master handoffs.
