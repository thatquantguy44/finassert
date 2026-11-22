# 0020 — Performance and backtest integrity plan

## Approach

1. P-02 reviews the current policy/catalog/artifact behavior and records a
   proposed public shape, confirmed policy-parameter export contract, and numeric
   contract in [decisions](decisions.md). The policy version-1 schema hashes
   rule parameters, but its report description currently omits them.
2. P-02 provides an out-of-order leap-year fixture, a 12-month seeded cumulative
   error, independent expected values, hand-derived short-history and percent
   cases, zero tracking error, a 13-month annualization case, and coverage/numeric
   boundary mutations in [artifacts/fixtures](artifacts/fixtures/expected.json).
3. Implement shared date coverage and reference calculation. Wire the audit
   checks and starter policy to the same logic. Record accuracy tests, failure
   evidence, and mapping round-trip before integrating Excel.
4. Build the worked Excel workbook. Include an assumptions sheet with all
   declarations and mapping instructions, a reference sheet with visible
   formulas, and a single audit table that contains the source columns and
   supplied candidate figures. Document how to correct the seeded error and
   rerun the same policy. Add a Python/CLI example that replays the calculations
   and audit using the same fixture.
5. Qualify the workbook and exports, update the catalog-derived guide as needed,
   and retain actual host and CLI parity evidence.

## Dependencies and affected areas

The date/return logic and rule registration plug into core Python and the
policy catalog. Keep the first milestone dependency-free in core. Use the
existing workbook source, add-in policy and report paths where supported. The
portable workbook is an example artifact and uses the same terms as the add-in.
See [related specifications](spec.md#dependencies-on-other-specifications)
for the cross-spec contracts.

## Verification

- For this proposal run the strict docs build, link and anchor checks, and
  `git diff --check`. Follow the [checkpoint workflow](../../CONTRIBUTING.md#master-handoff-checkpoints)
  for the spec commit.
- P-04 implements the additive 0005/0007 report contract: expose explicitly
  configured and fully resolved rule parameters, preserving exact decimals and
  mapping/window/unit/tolerance declarations when a rule skips or errors.
- During implementation run `uv run pytest`, `uv run ruff check .`,
  `uv run ruff format --check .`, and `uv run mypy src/finassert`. Execute the
  declared fixtures with Python and CLI. Compare normalized findings and
  tolerances against the independent expectations.
- Run the bundled Excel browser suite and a native workbook correction/rerun
  with the existing [acceptance runbook](../0016/acceptance.md). Record the host,
  source scope, actual report outputs, and parity comparison. Run the strict
  docs build and package checks in [CONTRIBUTING.md](../../CONTRIBUTING.md).
