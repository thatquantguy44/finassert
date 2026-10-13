# Policies and the command line

A **policy** is a small file that names the checks a dataset must pass. Policies
let people who do not write Python define, review, and run checks, and let
pipelines run exactly the same checks without bespoke code.

## Writing a policy

```yaml
version: 1
name: Daily positions
description: Long-only equity book, one portfolio per file
assumptions:
  - Weights are fractions of 1, not percentages
rules:
  - rule: weights_sum_to_one
    column: weight
    tolerance: "0.0001"
  - rule: non_negative
    column: Mkt Val (USD)
    null_policy: ignore
```

- `version` is required and must be `1`.
- `rules` is an ordered list; results appear in the same order. An empty list
  is allowed and passes vacuously.
- Each entry starts with `rule:`, naming a check by factory name
  (`non_negative`) or rule identifier (`arithmetic.non_negative`). The other
  keys are that check's settings. Run `finassert rules` to see every check, its
  settings, and when **not** to use it.
- `column` is the header text exactly as it appears in the data file, spaces
  and punctuation included.
- `name`, `description`, and `assumptions` are optional and are printed in the
  HTML report.

Unknown settings, misspelled rule names, wrong types, and duplicated keys are
errors, never ignored. Every problem is reported at once with its line number
and the nearest valid spelling; nothing is corrected automatically:

```text
finassert: the policy 'policy.yml' is not valid:
  - line 7, rules[2].rule: Unknown rule 'non_negativ'. Available rules: non_negative, weights_sum_to_one. Did you mean 'non_negative'?
  - line 11, rules[3].tolerance: '1,000' is not a plain number. Write digits only, such as "0.0001"; commas, percent signs, and currency symbols are not accepted.
```

### Numbers and tolerances

Quote tolerances (`"0.0001"`) to keep them as exact decimals. Unquoted values
with a decimal point are binary floats, as in Python. A tolerance may also be a
mapping with `absolute` and `relative` parts:

```yaml
    tolerance:
      absolute: "0.0001"
      relative: "0.000001"
```

`non_negative` accepts only an absolute tolerance, because a relative bound has
no meaning against zero.

Policies may also be written as JSON with the same structure. JSON strings in
tolerances are exact decimals, and JSON numbers are floats.

## Running checks

Install the command line with `finassert[cli]`, which adds the YAML reader.
To try it, run the sample policy against the sample data in `examples/`; one
check passes and one fails on a negative market value:

```bash
finassert check --config examples/policy.yml --input examples/positions.csv --html report.html
```

For your own files:

```bash
finassert check --config policy.yml --input positions.csv \
  --output report.json --html report.html
```

| Option | Meaning |
|---|---|
| `--config` | Policy file (`.yml`, `.yaml`, or `.json`). |
| `--input` | Data file: `.csv`, `.json`, `.xlsx`/`.xlsm`, or `.parquet`/`.pq`. |
| `--sheet` | Worksheet to check in an Excel workbook; required if it has several. |
| `--format`, `--policy-format` | Override the format inferred from the extension. |
| `--output` | Write the JSON report artifact. |
| `--html` | Write a self-contained HTML report for people. |
| `--quiet` | Print nothing on success except errors. |

The command never prompts. Reports are written atomically: a failed write
leaves any previous file untouched, and an interrupted run writes nothing.

### Exit codes

| Code | Meaning |
|---|---|
| `0` | Every check passed or was skipped. |
| `1` | At least one check failed. |
| `2` | At least one check could not run, for example a missing column. Wins over `1`. |
| `3` | The command line or policy is invalid, or the policy cannot be read. |
| `4` | The input cannot be read or parsed, or a report cannot be written. |

### Reading data files

CSV files must be UTF-8 (Excel: *Save As › CSV UTF-8*) with unique column
headers in the first row. Cells are read without guessing:

- blank cells are missing values, handled by each check's `null_policy`;
- whole numbers become integers, and numbers with a decimal point or exponent
  become exact decimals, so `0.1 + 0.2 + 0.7` sums to exactly `1.0`;
- everything else stays text. `1,000`, `40%`, and `$5` are reported as
  non-numeric, never rescaled.

Rows are labelled as a spreadsheet would show them, with the header on row 1,
so a failing "row 3" is row 3 in Excel.

JSON input may be an object of columns (`{"weight": [0.4, 0.6]}`) or a list of
row objects. JSON numbers are read as exact decimals.

Excel workbooks (`.xlsx`, `.xlsm`) are read directly, with no extra
dependency. The first non-empty row holds the headers, and rows are labelled
with the sheet's own row numbers. Cells are read as Excel stored them, not as
they are displayed:

- numbers keep their exact stored value, so a cell showing `0.3` because of its
  format is still checked at full precision, and an Excel table checks the same
  way as the CSV export of it;
- percentage cells keep their stored fraction: a cell showing `40%` is `0.4`;
- date cells become dates and are reported as non-numeric, never read as the
  day counts Excel stores them as;
- formulas are checked by their saved result. A formula with no saved result,
  as some export tools write, is an error: open the file in Excel and save it;
- rows with no values are skipped; a value in a column with no header is an
  error.

A workbook with several sheets needs `--sheet`, so the wrong tab is never
checked by accident. Old `.xls` files must be re-saved as `.xlsx`.

Parquet files need `finassert[parquet]` (pyarrow). Values keep their stored
types: decimal columns become exact decimals, floating-point columns stay
binary floats, and nulls and NaN are missing values. Rows are labelled from 0,
as in a default pandas index.

## Report artifacts

`--output` writes the 0005 report wrapped with the context needed to audit it:

```json
{
  "schema_version": 1,
  "tool": {"name": "finassert", "version": "0.1.0"},
  "generated_at": "2026-01-01T00:00:00Z",
  "policy": {"name": "Daily positions", "digest": "sha256:…", "rules": ["…"]},
  "input": {"locator": "positions.csv", "format": "csv"},
  "report": {"passed": true, "results": ["…"]}
}
```

The policy digest fingerprints the parsed policy, so reformatting a file does
not change it but changing any setting does. Set `SOURCE_DATE_EPOCH` to fix
`generated_at` for reproducible artifacts.

The HTML report embeds the same artifact in `script#finassert-report`, uses no
external resources, adapts to dark mode, and prints cleanly.

## From Python

```python
from finassert.loaders import load_input
from finassert.policy import load_policy
from finassert.reporting import to_html

policy = load_policy("policy.yml")
report = policy.check(load_input("positions.csv"))
html = to_html(report, policy=policy, input_locator="positions.csv")
```

Organizations can expose their own rules to policies by registering a
`RuleFactorySpec` in a `RuleCatalog` and passing `catalog=` to
`load_policy`. Policies can never name a factory the caller did not register.
