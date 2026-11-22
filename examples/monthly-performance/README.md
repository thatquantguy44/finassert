# Monthly performance audit workbook

`monthly-performance-audit.xlsx` is a synthetic 2024 monthly strategy and
benchmark return example. It starts with a deliberately incorrect June reported
strategy cumulative return. The data rows are intentionally out of chronological
order. The `Reference` worksheet calculates the expected returns from monthly
periodic returns and never uses reported cumulative values.

The `Assumptions` worksheet holds the complete policy declarations. The
`Audit input` worksheet is the source range for both the Python API and CLI.
It has one formula check for each source row. The formulas show the expected
cumulative values, differences, and the configured tolerance. The formulas are
workbook evidence. `finassert` independently checks the values saved in the
source columns.

Run the Python API example from the checkout root:

```bash
python examples/monthly-performance/run_audit.py --expect failed
```

Run the equivalent CLI check and write a structured report:

```bash
finassert check \
  --config examples/monthly-performance/policy.yml \
  --input examples/monthly-performance/monthly-performance-audit.xlsx \
  --format xlsx --sheet "Audit input" --header-row 5 --max-row 17 \
  --output monthly-performance-report.json --html monthly-performance-report.html
```

The initial run fails at `src-2024-06`. Change `Audit input!E15` from
`0.071520150601` to `0.061520150601`, save the workbook, then rerun either
command with `--expect passed` for the Python example. The correction changes
only the reported June strategy cumulative value. Reference values for later
months continue to come from their periodic returns.

All data is synthetic. Replace the comparison declarations, mappings, window,
units, fee treatment, tolerance, and source rows before using this workflow for
a production performance report.
