# finassert User Guide

<!-- finassert-guide-revision: 2026-11-21 -->

Financial data validation in Excel, in a browser, and in reproducible pipelines.

**Product version:** 0.1.0. **Guide revision:** 2026-11-21.

[Download this guide as a PDF](assets/finassert-user-guide.pdf).
The local add-in API also provides the PDF at
`GET /api/finassert/v1/user-guide.pdf` and its identity metadata at
`GET /api/finassert/v1/user-guide`.

## 1. Start here

finassert checks whether financial data satisfies explicit rules. You choose the
data, state its assumptions, configure the checks, and retain the results. The
same Python engine powers policies, the command line, the browser application,
the Excel add-in, and the assistant tool server.

Use this guide as a working manual. Chapters 2 and 5-7 cover the Excel workflow;
chapter 8 covers the browser; chapters 9-11 cover policies, Python and the CLI.
Chapters 12-14 explain financial applicability and units. Chapters 15-19 cover
evidence, assistant access, the download API, recovery and daily operation.
The appendices list every current built-in rule, its settings, and all templates.

### Choose an interface

| Interface | Use it for | What you need |
| --- | --- | --- |
| Excel task pane | Read a live table/range, inspect findings, correct cells and rerun | A compatible Excel host, a trusted HTTPS add-in origin and a loaded manifest |
| Browser app | Check a saved workbook, CSV or JSON without installing Python | The built HTML application and its pinned checking engine |
| Python | Compose checks, reuse policies and integrate with application code | Python 3.11+ and the appropriate optional extras |
| Command line | Reproducible file checks, scheduled jobs and pipeline gates | The installed `finassert` command, input and policy |
| Assistant server | Let a connected assistant inspect and check approved local files | The `assistant` extra and explicitly allowed workspace roots |

### Understand the current support boundary

The product is an initial implementation. Focused native Mac Excel checks have
verified source/date binding, navigation, freshness, exports, both date epochs,
the Home-ribbon entry points, and a synthetic 50,000-row workflow. Full Mac
acceptance still has table/hidden/filtered and remaining failure/race/keyboard
cases open. Windows/web add-in acceptance, the optional reference panel's native
acceptance, and external review are separate unfinished work.

A feature described as implemented has an actual code path. It is not a promise
that every Excel host, data convention or operating environment has been accepted.
See [the live Excel acceptance record](https://github.com/thatquantguy44/finassert/blob/main/specs/0016/acceptance.md)
for the tested scope and retained evidence.

### Four concepts you will use throughout

- **Source:** the particular file, worksheet region or live table being checked.
- **Policy:** an ordered set of rules, parameters and stated assumptions.
- **Result:** the outcome of one rule; a report contains all rule results.
- **Freshness:** whether a live Excel result still matches its source at its last
  successful verification. Freshness and the financial outcome are separate.

A passing report says the configured rules did not block. It does not establish
that all necessary checks were present, the data was complete, a valuation was
economically sound, or an investment or liquidity decision was appropriate.

## 2. Your first Excel check and demo

Use a disposable workbook. This example is one long-only portfolio in one
currency; both positions, including any cash position, are part of its weights.
The negative market value is an intentional input error for this example.

### Prepare the sample

Enter the following at `Sheet1!C7:H9`. The header is row 7. Enter weights as
numeric fractions; a percentage format may display them as 40.0% and 60.0%.

| portfolio | ticker | weight | market_value | nav | date |
| --- | --- | --- | --- | --- | --- |
| Alpha | AAA | 0.4 | -400 | 1000 | 2026-01-01 |
| Alpha | BBB | 0.6 | 600 | 1000 | 2026-01-01 |

If the date cells are real Excel dates, format them as dates and choose the
workbook's actual 1900 or 1904 system in the pane. Do not switch the workbook's
date system just to make the pane match. ISO date text may remain text when that
is the intended schema.

### Run, find, correct and rerun

1. Open **Home > Open validation** in Excel's finassert ribbon group.
2. Wait for the checking engine to say **Ready**.
3. Choose the actual **Workbook date system**: 1900 or 1904.
4. Select the complete `C7:H9` rectangle and choose **Use selected range**.
5. Confirm the summary: Sheet1, header row 7, two physical and parsed rows,
   six columns, the exact range, and the chosen date interpretation.
6. Start from **Long-only holdings file** and confirm the `weight` and
   `market_value` column choices and the template's assumptions.
7. Choose **Run checks**. Expect a **Current** result with two passes and one
   failure. The market-value check identifies row 8 and the negative value.
8. Choose **Select cell in row 8**. The selected cell should be F8 with -400.
9. Replace F8 with the numeric value 400. Expect **Stale** and disabled current
   report exports/navigation.
10. Choose **Run checks** again. The pane rereads the bound source. Expect
    **Current**, three passed checks, and the preview showing 400.
11. Write results to a sheet, download JSON/HTML, and save/download the policy.

The long-only template checks weights sum to one and nonnegative weights and
market values. It does not include NAV reconciliation. Add an appropriate NAV
rule or use the multi-portfolio template when that relationship is required.

### Reopening the prepared demo

The prepared demonstration workbook uses the **1904** date system and
`Sheet1!C7:H9`. It includes saved policy and results sheets. On a new pane session,
choose 1904 again, bind the range, refresh saved policies, load the saved policy,
and run. A reopened saved results sheet is evidence of its old snapshot, not a
live Current result. For a repeat demo, change F8 to -400 and follow the sequence
above, finishing with 400 and a fresh run.

## 3. Installation and local setup

### Python and optional features

Install a reviewed source checkout or verified wheel approved for your environment;
no published PyPI release is claimed. The package requires Python 3.11 or later
and has no core runtime dependencies. The pip commands below assume you are in
the checkout root; uv can install the same extras.

```bash
python -m pip install -e .
python -m pip install -e ".[cli,excel]"
finassert --version
finassert rules
```

| Extra | Adds |
| --- | --- |
| `cli` or `yaml` | PyYAML for YAML policies; JSON policies do not need it |
| `excel` | openpyxl for the explicit workbook-reader API and XLSX report writing |
| `pandas` | DataFrame support with preserved index labels |
| `parquet` | pyarrow for Parquet files |
| `assistant` | MCP SDK for the stdio assistant tool server |

There are two workbook-reading paths: the CLI/file/browser loader reads supported
XLSX content without openpyxl; `finassert.excel.read_workbook` is the optional
openpyxl-backed API. Creating a separate XLSX report requires the `excel` extra.
Neither path calculates formulas or refreshes external links.

From a source checkout, follow [Contributing](https://github.com/thatquantguy44/finassert/blob/main/CONTRIBUTING.md):

```bash
uv sync --all-extras --dev
```

### Build and serve the Excel add-in

Office loads the pane over HTTPS. Use an existing trusted development certificate
or your organization's approved deployment certificate. The repository's local
server binds to your computer by default; it is not a hosted validation service.

```bash
python scripts/build_excel.py \
  --base-url https://localhost:3002/ --output-dir dist/excel
python scripts/serve_excel.py --dir dist/excel --port 3002 \
  --cert /path/to/localhost.crt --key /path/to/localhost.key
```

The Excel build includes this guide's prebuilt PDF and identity sidecar. If the
builder reports stale guide assets, rebuild them using the documented guide
builder before repeating the Excel build; chapter 17 gives that command.

For a development installation, Microsoft's add-in debugging tool can load the
generated manifest. Run it from a disposable directory with a minimal
`package.json`; when this HTTPS server is already running, use:

```bash
npx office-addin-debugging start /path/to/manifest.xml desktop \
  --app excel --no-debug --no-live-reload --dev-server-port 3002
```

The Mac CLI sideload route has focused native evidence. Organizational
central deployment, AppSource distribution and Windows/web routes have their
own deployment and acceptance requirements. Do not infer that a checked manifest
schema proves a successful native installation.

### Keep the checking engine local

The default build loads a hash-pinned Pyodide engine from its pinned CDN release.
To bundle the engine next to the pane, build with:

```bash
python scripts/build_excel.py \
  --base-url https://localhost:3002/ --output-dir dist/excel \
  --bundle-pyodide download
```

You may provide an already verified local Pyodide directory instead of
`download`. The builder checks the loader and runtime/package hashes. The
bundled pane still loads Microsoft's required Office library. No workbook cells
are sent to the engine's download server.

## 4. Prepare data that means what the policy assumes

### Declare the grain before choosing checks

Write down what one row represents: a position, a portfolio/date balance, a
transaction, or a forecast series/week. Then identify the group keys, row keys,
currency, units, as-of dates and sign conventions. One row per security lot is
not the same grain as one aggregated position per security.

For each amount, decide whether it is a balance, a flow, a rate or a price.
Balances are not automatically summed just because they are numeric. Grouped
rules use their documented aggregation contract. Where a rule offers explicit
mapping and aggregation settings, choose them deliberately.

### Headers, regions and totals

Use one nonblank, unique header per populated column. Remove merged headers and
multirow decorative header blocks from the selected source. Select only one
rectangle in live range mode. A single selected cell never expands silently to
the used worksheet.

Excel table mode uses the actual table header and data body and excludes the
table's totals row. Fixed-range mode uses precisely the chosen bounds; exclude
totals yourself. File-based workbook workflows can use `header_row` and
`max_row` to exclude surrounding notes and totals.

Hidden and filtered rows are included in live validation. Hiding a bad row does
not remove it from a live check. The CLI/file-reader `hidden="reject"` option
is a different, explicitly selected contract; there is no live visible-only mode.

### Types and missing values

| Input | Interpretation |
| --- | --- |
| Numeric Excel percentage displaying 40% | Stored 0.4; no rescaling |
| CSV text `40%`, `$5` or a thousands-formatted token | Not a plain numeric value; no guessing of units/locale |
| Numeric text such as `0.4` | Parsed as a number by the file/live parsing path |
| Blank or spaces-only cell | Missing, not zero |
| Excel error such as `#N/A` | Invalid cell value, not a numeric observation |
| Date-formatted Excel numeric cell | Interpreted as a date using the chosen/live or stored/file date system |
| Formula in a saved workbook | Its cached result; missing cached results are input errors |

For CSV, use UTF-8 and put the headers in the first row. Quote CSV fields that
contain separators; a quoted `1,000` still is not a plain numeric token.
JSON input can be an object of columns or a list of row objects. The JSON file
loader reads JSON numbers as exact decimals; Python objects you construct retain
their Python numeric types. Parquet preserves stored types and uses row labels
starting at 0; pandas diagnostics preserve the DataFrame index.

### Identity and dates

Ordinary live Excel labels are physical worksheet row numbers, including gaps.
A configured business row key is a label, never an instruction to navigate to
that numbered Excel row. Duplicate, blank or ambiguous keys can block navigation
or the rule that requires unique keys. Missing groups have no physical row.

Choose 1900/1904 to match the workbook. A date-system selection changes only
interpretation in the pane; it does not edit Excel's workbook setting. After any
date choice change, rebind/review the source and run again. Treasury weekly rules
require their documented ISO `YYYY-MM-DD` text dates; do not assume arbitrary
locale date strings or other date object types satisfy that contract.

## 5. Excel: source binding and validation

### Ribbon entry points

The Home ribbon has **Open validation** and **Settings**. Validation opens the
ordinary source/policy/run workflow. Settings opens a focused pane view with
capture/freshness/request controls. **Back to validation** returns from that
view without discarding its in-memory session settings. These commands do not
run financial checks or edit workbook cells.

### Bind a table

1. Refresh **Available table** if the workbook's tables have changed.
2. Choose the intended structured table and select **Use this table**.
3. Check its worksheet, address, header row, width and physical/parsed row counts.
4. Confirm the workbook date system and the actual preview.

The binding tracks host identity, not just the displayed name. Deleting a table
and recreating another with the same name does not authorize silently reusing
old results. Resize/sort changes invalidate the old snapshot and targets.

### Bind a fixed range

1. Select a rectangle with one header row and the intended data rows.
2. Choose **Use selected range**.
3. Verify the exact address and counts before running.

Moving the selection later does not change the bound source. Structural changes
that make the fixed range uncertain require explicit reselection. Missing sheets
or changed headers require a new source and mapping review. Range mode requires
ExcelApi 1.13 for merged-header detection; on older hosts, use a supported table
workflow or update Excel. Sheet writing declares a 1.7 floor, and live capture
requires the additional 1.9 capabilities.

### Choose and review checks

Start from a template, open a YAML/JSON policy, load a saved workbook policy, or
add individual checks. Match each semantic setting to the exact header. Proposed
column matches explain whether they are exact, known-name, contains or similar
matches. Resolve ambiguous columns explicitly; base versus local currency
columns must not be guessed.

Review assumptions as well as the visible settings. A long-only negative-value
check is inappropriate for an instrument whose value can legitimately be
negative. A NAV check needs every included liability/cash/accrual in the same
currency and perimeter as its NAV.

### Run and read the result

Each **Run checks** reads the bound source again. The normal verified workflow
compares stable captures around evaluation. A mismatch, failed read, calculation
problem or superseded operation does not publish a new Current result.

The report shows one result per configured rule in policy order. Expand the
retained findings for counts and examples. A **Current** failed report is a
freshly verified failure; a **Stale** passed report is historical. Neither word
changes the rule's underlying outcome.

## 6. Excel: freshness, settings and calculation

### Lifecycle states

| State | Meaning and next action |
| --- | --- |
| Unbound | Choose a table/range and the date interpretation |
| Ready | Source preview is available; run the checks to verify a result |
| Reading | An operation is capturing the source; allow it to finish or cancel |
| Checking | The engine is evaluating the captured input |
| Current | Result matched the source at the displayed last verification time |
| Stale | Result is historical; correct the cause and rerun |
| Blocked | The pane explains a capability, input, setting or verification problem |

Current is not a lock, a live transaction or a guarantee against an edit made
after the timestamp. Before current-result exports or navigation, the pane
rereads and compares the source and policy. Missing/delayed events cannot by
themselves authorize an old result.

### Session settings

| Setting | Default | Allowed values |
| --- | --- | --- |
| Change monitoring | Live workbook events | Live events or on demand |
| Capture verification | Verify stable captures | Verified or snapshot only |
| Matching captures per run | 2 | 2-4 |
| Maximum rows per request | 5,000 | 1-5,000 |
| Maximum cells per request | 50,000 | 1,000-50,000 |
| Operation timeout | 120 seconds | 1-300 seconds |

Changing these settings requires a new run. Invalid settings block validation;
**Restore default settings** provides a recovery path. Settings and source
bindings last only for this pane session. They do not change workbook settings,
policy YAML or the financial meaning of a rule.

On-demand mode disables immediate cell/format/calculation alerts. Run,
navigation and export still verify the source. Snapshot-only mode evaluates one
capture for inspection and stays unverified/Stale; current-result export and
navigation are unavailable. It does not bypass date, calculation or size guards.

### Calculation, request limits and cancellation

finassert never changes Excel's calculation mode or silently recalculates it.
Wait until calculation is Done. In manual mode, calculate in Excel and use
**I calculated this workbook in Excel** before the next protected action. A
successful operation consumes this acknowledgement; subsequent operations may
need another confirmation.

The source ceiling is 5,000,000 cells. Captures are chunked by both row and cell
limits. Reduce the request size for host payload errors; one source row must fit
the selected cell limit. A wide row that exceeds it is rejected before capture.

Cancel/timeout takes effect between host requests and at guarded completion
points. An outstanding Office request or synchronous Python evaluation cannot
be interrupted. An interrupted or partial read never becomes a successful run.

## 7. Excel: findings, correction and safe outputs

### Follow a finding

The diagnostic panel shows the complete count, retained-example cap, number of
examples shown and truncation state. A count of 1,000 with 20 examples means
1,000 violations were counted; it does not mean only 20 rows were evaluated.
Use **Select cell** for an unambiguous diagnostic column or **Select source row**
for a row-level finding. These actions change selection, not source values.

The pane reverifies the result before navigating. Stale, blocked and unverified
results cannot navigate. A duplicate business key requires a unique mapping and
new run. **No source row** for a missing forecast series is correct: a row that
does not exist cannot be selected. Sorting/resizing/deletion can invalidate old
targets and requires a fresh run or rebind.

### Correct the source

Read the rule's observed/expected values and equation, not just the banner.
Correct the underlying workbook or upstream input. Do not weaken tolerances or
remove a required rule to make a demonstration pass. Recheck the source preview,
run again, and retain the new outcome together with any prior failed evidence.
The add-in does not perform automatic fixes or annotate/highlight source cells.

### Export results

- **Download report (JSON):** machine-readable canonical artifact and provenance.
- **Download report (HTML):** readable standalone report with the artifact embedded.
- **Write results to a sheet:** a stamped snapshot and canonical findings.
- **Download policy (YAML):** reusable policy independently of result freshness.

Current-result export performs another source/policy comparison. The worksheet
stamp includes outcome, checked address, source identity/bounds, row counts,
date interpretation, policy fingerprint, snapshot digest, UTC capture and
verification times, and tool version. Different export actions can have
different verification times for the same evaluated snapshot.

### Ownership and collisions

The default write creates `finassert results` or a unique numbered name if it
already exists. To replace a completed output, refresh the output picker, choose
an owned results sheet and use **Replace selected results sheet** explicitly.
The workbook saves ownership by worksheet ID. A matching sheet name alone does
not authorize replacement, and a bound source sheet cannot be cleared.

Older outputs without ownership records can still be retained as historical
evidence but are not automatically adopted as writable destinations. A later
source edit never rewrites earlier exported snapshots.

### Save and reload the policy

**Save these checks in the workbook** creates a uniquely named `finassert policy`
sheet. The policy is literal text in column A starting at row 3. Keep its
indentation and review edits. To reload after reopening, refresh saved policies,
choose the correct sheet, then **Load the checks saved in the workbook**.
Saving/loading a valid policy does not require a Current financial result.

### Failed writes

The add-in checks worksheet bounds, a 5,000,000-cell output ceiling and Excel's
32,767-character cell limit. Protected/read-only destinations, host errors or
cancellation can leave a clearly incomplete output. Completion is recorded only
after body and styling writes succeed. Do not use an incomplete sheet as finished
evidence. Correct the cause, get a Current result and create a new output; use
JSON/HTML for evidence too large for one Excel cell.

## 8. Use the browser app with saved files

The browser application is a built HTML file, not the Excel task pane. Open it
in a supported browser, wait for the checking engine to become Ready, then choose
an Excel workbook, CSV or JSON input. For a multisheet workbook, choose the
specific worksheet and confirm its preview before choosing checks.

The browser offers matching templates and lets you build individual checks or
open a policy. Review assumptions, matched columns, numeric settings, severity
and null handling. Run, inspect the report and download HTML, JSON and YAML.
Opening a different input or editing the policy invalidates an old file result.

There is no live connection back to the saved workbook. Correct the source file,
save/recalculate it if needed, reopen it in the browser and rerun. Live Excel
Current/Stale binding/navigation controls are not a promise about browser files.

The engine and YAML reader load at startup from the pinned Pyodide release,
unless the build bundles them. Input data is processed in the tab; the offline
file application makes no network requests after startup. Reports display in a
sandboxed frame with scripts disabled. Excel-only guide/reference requests are
separate explicit local document requests, not workbook-data uploads.

To build the standalone page from the repository:

```bash
python scripts/build_web.py --output dist/web/finassert.html
```

## 9. Write, review and reuse policies

A policy is a versioned description of checks, not executable Python. YAML and
JSON use the same structure. Start with a template, adapt its exact column names
and assumptions, and keep the reviewed file with the data/report evidence.

```yaml
version: 1
name: Daily long-only holdings
description: One portfolio in one base currency
assumptions:
  - Weights are fractions of 1 and include the cash position.
  - Market values cannot legitimately be negative in this book.
rules:
  - rule: weights_sum_to_one
    column: weight
    tolerance: "0.0001"
  - rule: non_negative
    column: weight
  - rule: non_negative
    column: market_value
    null_policy: fail
    severity: error
    max_violations: 20
```

`version` must be 1. `rules` is ordered. Use a factory name such as
`non_negative` or its stable rule identifier `arithmetic.non_negative`.
Headers are exact data-schema names, including spaces/punctuation. Optional
name, description and assumptions appear in reports.

Unknown settings, misspelled rules, wrong types and duplicate policy keys are
errors. Policy issues include location, line where available, message and
suggested spelling. Suggestions are not automatic corrections. An empty rules
list passes vacuously; it is not evidence that expected controls were evaluated.

### Exact numbers and inclusive tolerances

Quote decimal parameters in policies and use `Decimal("...")` for exact Python
inputs. Unquoted Python/YAML floats retain binary floating-point behavior.
CSV/JSON file loaders parse their plain decimal tokens as exact decimals.

For a tolerance with absolute A and relative R, closeness uses:

```text
abs(actual - expected) <= A + R * max(abs(actual), abs(expected))
```

Equality at the configured bound passes. Values/tolerances must be finite and
tolerances nonnegative. Decimal operands stay in Decimal arithmetic; a tolerance
is not a request to round away source precision. Choose the absolute allowance
in the rule's units: currency units, shares or fractional weights.

```yaml
    tolerance:
      absolute: "0.01"
      relative: "0.000001"
```

Not every rule accepts both parts. `non_negative` uses an absolute tolerance;
relative tolerance against zero has no useful meaning. Limit rules apply their
own documented bounds. A weight allowance of 0.0001 is one basis point, not
0.0001 percent and not one cent.

### Null policies and severity

Most numeric rules default to `null_policy: fail`. `ignore` removes permitted
missing observations from that rule's calculation; `skip` records the entire
rule as not evaluated. Some reconciliations reject ignore because omitting a
flow changes the identity. The appendix lists each rule's accepted choices.
Missing columns are evaluation errors; a null policy cannot invent a column.

Severity controls whether a failed assertion blocks, not whether it failed:

The add-in results sheet labels this **If check fails**, with **Block validation**,
**Show warning** and **Show information**. The report cards and policy editor use
the same action wording. **Result** shows what actually happened; a passed check
can still be configured to block if it fails. JSON/policy severity values remain
`error`, `warning` and `info`.

| Setting/outcome | Default report effect |
| --- | --- |
| Failed at `error` severity | Blocks the report |
| Failed at `warning` or `info` severity | Reported as a warning; does not block |
| Evaluation `error` outcome | Always blocks, even when configured severity is lower |
| `skipped` outcome | Does not block by default; required-control coverage must be enforced separately |

The CLI `--fail-on warning` or `--fail-on info` can use a stricter exit-code
threshold without changing report contents or the configured rule severity.

## 10. Python API and data adapters

### Run ordinary checks

```python
from decimal import Decimal
import finassert as fa

data = {
    "weight": [Decimal("0.4"), Decimal("0.6")],
    "market_value": [Decimal("400"), Decimal("600")],
}
report = fa.check(
    data,
    [
        fa.weights_sum_to_one(column="weight", tolerance=Decimal("0.0001")),
        fa.non_negative(column="market_value"),
    ],
)
assert report.passed, report.summary()
print(report.summary())
```

Core inputs can be column mappings, sequences of row mappings, compatible pandas
DataFrames, or `ColumnSource` implementations. Column values and labels must
have consistent lengths. Rules must not mutate caller data. Ordinary checks
collect evaluation errors in results; use `raise_on_error=True` when the first
evaluation error should interrupt control flow.

### Load the same policy and file

```python
from finassert.loaders import load_input
from finassert.policy import load_policy
from finassert.reporting import build_artifact, artifact_to_json, to_html

policy = load_policy("policy.yml")
source = load_input("positions.csv")
report = policy.check(source)
artifact = build_artifact(
    report,
    policy=policy,
    input_locator="positions.csv",
    input_format="csv",
)
json_text = artifact_to_json(artifact)
html_text = to_html(report, policy=policy, input_locator="positions.csv")
```

Use `parse_policy(document)` or `parse_policy_text(text, format="yaml")` for
in-memory configuration. `dump_policy(policy)` emits reloadable YAML. The
policy digest fingerprints the parsed configuration, rather than whitespace.

### Read a precise workbook region and write a separate report

```python
from finassert.excel import read_workbook, write_report_xlsx
from finassert.policy import load_policy

source = read_workbook(
    "positions.xlsx",
    sheet="Positions",
    header_row=7,
    max_row=9,
    hidden="include",
)
report = load_policy("policy.yml").check(source)
write_report_xlsx(report, "review.xlsx")
```

This optional reader requires `finassert[excel]`, requires the sheet argument,
and uses 1-based worksheet row bounds. `hidden="reject"` refuses hidden
selected sheets/rows/named columns; include is the default. The report is a
separate workbook with Summary, Results and Diagnostics sheets. No input
workbook is edited. JSON/HTML preserve exact Decimal values as text where needed.

### Grouping, ordering and custom checks

Use `group_by` for the dimensions that define independent checks, and specify
`currency` where offered rather than offsetting currencies. `row_key` preserves
portable business identity where supported. pandas adapters preserve index labels.
For multicolumn mapping, `ColumnMapping`, `GroupKey` and `FieldAggregation` make
semantic fields and SUM/FIRST/LAST/REQUIRE_UNIQUE reductions explicit. FIRST/LAST
rules require explicit ordering; never infer chronology from physical row order.

```python
import finassert as fa

present = fa.custom_rule(
    "acme.positions.present",
    "Positions are present",
    lambda data: len(data["position_id"]) > 0,
)
assert fa.check({"position_id": ["P-1"]}, [present]).passed
```

A custom evaluator may return a complete `ValidationResult` for observed,
expected, tolerance and bounded diagnostic evidence. Exceptions are evaluation
errors. A custom policy factory must be explicitly registered in a caller-owned
`RuleCatalog`; a policy cannot import arbitrary code by naming an unregistered
factory. See [rule development](rule-development.md) for the extension contract.

## 11. Command line and pipeline use

### Discover and adapt

```bash
finassert rules
finassert rules --json
finassert templates
finassert templates --json
finassert init --template long-only-holdings --output policy.yml
finassert suggest --input holdings.csv
finassert suggest --input holdings.csv --output suggested-policy.yml
```

`init` and suggestion outputs do not replace existing files without `--force`.
`suggest` ranks header fits and records proposed matches for confirmation.
Unmatched/ambiguous columns remain unresolved so later checking can report the
problem. It does not infer currencies, units, dates or sign conventions.

### Run and retain evidence

```bash
finassert check --config policy.yml --input positions.csv \
  --output report.json --html report.html

finassert check --config policy.yml --input positions.xlsx \
  --sheet Positions --header-row 7 --max-row 9 --hidden include \
  --output report.json --html report.html --xlsx review.xlsx
```

| Option | Purpose |
| --- | --- |
| `--config`, `--input` | Required policy and data paths |
| `--format` | Override inferred input format: csv, json, xlsx or parquet |
| `--policy-format` | Override inferred YAML/JSON policy format |
| `--sheet` | Workbook worksheet; required when the file has multiple sheets |
| `--header-row`, `--max-row` | Explicit 1-based workbook region bounds |
| `--hidden` | Include hidden regions or reject them |
| `--output` | Canonical JSON artifact destination |
| `--html` | Standalone HTML report destination |
| `--xlsx` | Separate Excel report; requires the excel extra |
| `--fail-on` | Lowest failure severity that blocks the exit code |
| `--quiet` | Suppress the printed summary |

The CLI does not prompt. It protects input/policy paths and writes reports
atomically rather than leaving a partly written replacement. Old `.xls` files
must be converted to supported `.xlsx`; macros in `.xlsm` inputs are not executed.

### Handle every exit code

| Code | Meaning | Operational response |
| --- | --- | --- |
| 0 | No result blocks at the selected threshold | Also review warnings, skips and required-control coverage |
| 1 | At least one assertion failed at/above the threshold | Review the financial/data break |
| 2 | At least one check could not run | Resolve missing columns, bad values or evaluation problems |
| 3 | Invalid command/policy or unreadable policy | Correct configuration and retry |
| 4 | Input read/parse or report write failure | Fix file, format, path or output access |

Code 2 takes precedence over code 1. A report write failure is not a successful
validation, even when rule evaluation completed. Capture the exact return code,
keep logs/report paths, and do not implement a pipeline that treats every
nonzero result as the same condition. A scheduler/orchestrator can invoke the
CLI directly; a hosted scheduler is not included in finassert.

Set `SOURCE_DATE_EPOCH` for a controlled reproducible artifact timestamp when
needed. Otherwise retain the actual UTC generation and verification timestamps.
Compare canonical results/policy and normalized source identities when matching
interfaces; do not mistake expected input-locator or timestamp differences for
different financial findings.

## 12. Select financial rules by their assumptions

The appendix provides the complete factory/settings reference. This chapter
explains which relationships each family is intended to check. Compose
complementary checks rather than relying on one green banner.

### Data quality and arithmetic

`required_fields` detects blanks in declared columns; `no_duplicates` checks
declared keys. `non_negative` and `in_range` check numeric observations against
configured bounds. Decide whether negative values are economically legitimate
before applying a long-only constraint. Booleans, nonfinite numbers and unusable
amounts do not become zero merely because they occur in a numeric column.

### Holdings, allocation and limits

`weights_sum_to_one` checks total fractional weight, optionally per portfolio.
Use group keys when one dataset contains multiple portfolios. A whole-file sum
is not a substitute for per-portfolio completeness. `weights_match_market_values`
checks each weight against market value/NAV, or the sum of market values when no
NAV column is configured; a zero denominator needs explicit review.

`drift_within_band` compares actual and target weights using position bands and,
when configured, a total drift limit. `turnover_within_limit` sums absolute
changes from previous weights; explicitly choose one-way (half the absolute
sum) or two-way. Tolerances/bands use fractional-weight units.

`gross_within_limit` limits sum of absolute values; `net_within_limit` limits the
signed sum. An optional base converts configured amounts to relative exposure
under the rule's base contract. `position_within_limit` limits each position's
absolute value. Configure both currency/group scope and caller-approved limits.
Net bounds can be negative. No regulatory, mandate or investment limit is
silently provided by a template.

### Accounting and valuation identities

```text
Cash, positive outflows:
  closing = opening + inflows - outflows + cash_pnl

NAV:
  sum(signed market_value) = reported NAV

Position valuation:
  market_value = quantity * price * multiplier

Position quantity, positive sells:
  closing = opening + buys - sells + adjustments

Simple return:
  return = (ending - beginning - net_flows) / beginning
```

Cash requires an explicit positive/negative outflow sign. Transaction-grain cash
requires an ordering key and does not choose FIRST/LAST by physical row order.
Summary-grain cash assumes the total balances/flows cover one declared group.
Currencies never offset or convert implicitly.

NAV needs all relevant assets, liabilities, cash and accruals in a consistent
base currency/perimeter. Position valuation needs compatible quantity, price
and multiplier units. Position roll-forward requires the sell sign and the
position-identifying group keys; repeated summary rows must agree rather than
being interpreted as additional independent trades.

Simple return requires `return_unit="fraction"` or `"percent"`. It is a
simple period identity, not a time-weighted return, IRR or general performance
attribution model. A zero beginning value and flow-timing assumptions matter.

### Monthly strategy and benchmark audit

`monthly_performance_audit` checks one declared strategy/benchmark comparison
in a single composite rule. It verifies every month in the inclusive window,
normalizes periodic and reported return units independently, links the periodic
returns, and compares each reported cumulative value with its reference value.
The policy must name the strategy, benchmark, base currency, month-end valuation
convention, fee treatment for both series, absolute return tolerance, and source
columns. Use it only when both series describe the same stable comparison and
do not require cash-flow reconstruction.

Create its documented starter policy with:

```bash
finassert init --template monthly-performance-audit --output performance.yml
```

Review and update every column mapping, date, unit, identifier and methodology
declaration before using it for another file. The starter settings match the
synthetic, out-of-order 2024 fixture and intentionally find its seeded June
strategy cumulative discrepancy. Run the fixture with:

```bash
finassert check --config performance.yml \
  --input specs/0020/artifacts/fixtures/monthly_returns_2024_seeded.csv \
  --format csv --output performance-report.json --html performance-report.html \
  --xlsx performance-report.xlsx
```

The expected June strategy cumulative return is `0.061520150601`; the supplied
value is `0.071520150601`. Correct the reported candidate value, rerun the same
policy, and retain both the original and corrected reports. JSON, HTML and XLSX
show configured parameters separately from effective parameters, including
defaults and normalized dates, units, currency and exact decimal tolerance.
The report preserves the configured policy digest and bounded source-row
diagnostics. It never uses a reported cumulative value to seed a later reference.

### Common mistakes to prevent

- Treating a 40% display as numeric 40 instead of stored 0.4.
- Summing repeated NAV balances over holdings rows.
- Reconciling local-currency market values to base-currency NAV.
- Choosing a tolerance in currency units for a fractional-weight comparison.
- Omitting cash, fees, accruals, liabilities or corporate actions from an identity.
- Increasing an example cap and assuming it changes evaluation scope.
- Treating an ignored blank or skipped rule as a verified required observation.

## 13. Weekly treasury and cash/funding pack

The treasury pack contains separate cash-forecast and facility-schedule
workflows. It validates declared coverage, identities and configured thresholds;
it does not generate a forecast or establish forecast accuracy or funding adequacy.

### Define the schedule and expected universe

Supply ISO text `period_start`/`period_end`, explicit grouping dimensions, a
currency column, `expected_scope`, `first_period` and the number of weeks.
Each bucket is a seven-calendar-day interval `[start, end)`. Expected schedules
are capped at 100,000 rows. Input order does not define the schedule.

Expected scope must include entirely absent entity/currency/scenario/vintage
series. Inferring it from observed rows would miss a whole missing series.
When `row_key` is configured for these rules it must provide unique, nonempty
text labels. Keep forecast vintages and scenarios as independent group keys.

### What the four treasury rules cover

| Rule | Checks and limits |
| --- | --- |
| `forecast_coverage` | Expected weekly buckets; missing, duplicate, extra or invalid weeks fail |
| `cash_continuity` | Current opening equals prior closing only on a complete unique schedule; invalid coverage is an evaluation error |
| `minimum_cash_buffer` | Closing less restricted cash meets the caller-supplied nonnegative minimum; configured tolerance can permit a visible shortfall |
| `facility_capacity` | Principal identity, effective commitment/headroom, continuity and maturity boundaries on each explicit facility/currency |

Coverage/continuity alone do not check within-week `opening + flows = closing`.
Compose cash reconciliation for that identity. The first opening is not
automatically tied to actuals. Currencies/scenarios are not offset and undrawn
facilities are not automatically added to available cash.

For facility controls, draws/repayments and other monetary components use
nonnegative magnitudes in currency major units. Facility identity is explicit in
expected scope. Maturity at/before a period start restricts draws/closing drawn;
maturity strictly within a week errors. Maturity at the period end is assessed
at the next period start if that period is supplied. These are period-end
controls, not intraperiod peak or legal-eligibility tests.

### Start with the current templates

```bash
finassert init --template treasury-cash-forecast --output cash-policy.yml
finassert init --template treasury-facility-schedule --output facility-policy.yml
finassert check --config examples/treasury/cash-pack.yml \
  --input examples/treasury/cash-forecast.csv --html cash.html
finassert check --config examples/treasury/facility-pack.yml \
  --input examples/treasury/facilities.csv --html facilities.html
```

The repository examples use synthetic data. Replace template scope/date
placeholders and provide approved minimum/commitment columns. The preparation
example explicitly constructs total inflows and total outflows using Decimal;
absent values are not converted to zero. Consumer mapping owns cross-file
facility-flow links and initial-opening actual tie-outs.

`treasury_pack_manifest()` identifies `treasury.cash-funding` version 1 and its
required inventory/assumptions. An absent, skipped or errored required check
means incomplete pack coverage even if the core report's default boolean is
true for skips. Paired forecast accuracy and debt principal/issuance expansion
remain proposed work, not supplied checks.

## 14. Financial units and explicit foreign exchange

Use typed quantities when dimensional and currency checks are needed before
numeric validation. `Money`, `Price` and `Notional` are distinct immutable
dimensions. `BasisPoints(50)` means 0.5%; `Percentage(50)` means 50%;
`Return("0.05")` is a 5% fractional return.

```python
from datetime import UTC, datetime, timedelta
from finassert.units import BasisPoints, FxRate, Money, MoneySource
import finassert as fa

stamp = datetime(2026, 11, 20, 12, tzinfo=UTC)
rate = FxRate("EUR", "USD", "1.08", stamp, source="approved-close")
usd = rate.convert(Money("50.00", "EUR"), at=stamp, max_age=timedelta(hours=24))
assert usd == Money("54.0000", "USD")
assert Money("100", "USD").scale(BasisPoints(50)) == Money("0.5", "USD")
source = MoneySource({"amount": [usd]}, columns=["amount"], currency="USD")
assert fa.check(source, [fa.non_negative(column="amount")]).passed
```

The caller supplies the rate, direction, valuation timestamp and maximum age.
Future, stale, nonpositive and incompatible rates are rejected. Inversion is
explicit. No provider, triangulation or automatic conversion path is selected.
Same-currency rates must equal one. Currency strings check three-letter syntax;
they are not an automatically maintained currency assignment registry.

MoneySource exposes declared Money columns as Decimal after checking the
currency. Convert mixed currencies explicitly before adaptation. It preserves
other columns/native labels and retains the used currency/FX provenance in
results and JSON/Excel evidence. More than 100 distinct used rates errors rather
than silently truncating provenance. Its initial adapter accepts Money columns,
not automatic Price/Notional coercion. Currency rounding and tolerance
materiality are distinct decisions.

## 15. Read and retain trustworthy evidence

### Read the result, not just the color

| Outcome | Interpretation |
| --- | --- |
| passed | This rule was evaluated and satisfied its configured condition |
| failed | It was evaluated and found a break; severity determines blocking |
| error | It could not evaluate reliably; always blocks |
| skipped | It was not evaluated under the selected policy; not a positive check |

An error severity and an error outcome are different concepts. An error-severity
rule can pass; a warning-severity rule can encounter an evaluation error and
block. Inspect counts, messages, observed/expected values, allowed difference,
assumptions and required-control coverage together.

### Canonical artifact and report views

The version-1 artifact wraps `report` with `tool`, `generated_at`, `policy` and
`input`. The policy includes its resolved digest. Decimal values serialize as
strings to preserve precision. Bounded diagnostic collections retain kind,
complete count, limit, observations and truncation.

HTML embeds that canonical artifact in `script#finassert-report` and needs no
external resources to read. The CLI XLSX report has Summary/Results/Diagnostics
tabs. A live add-in results sheet has its snapshot stamp and live provenance;
its layout is different from the separate CLI review workbook.

Live `input.excel` records source geometry/IDs, physical and parsed counts,
date-system choice, snapshot digest, and capture/verification times. File-based
workbook context records selected bounds and visibility details. A policy digest
identifies configuration, not the entire workbook; preserve both the source
snapshot and report rather than treating a fingerprint alone as an audit trail.

### Suggested evidence bundle

Keep the exact source file/saved snapshot, reviewed policy, JSON artifact,
readable HTML or results sheet, tool/build version, execution time and required
coverage decision. Preserve failed evidence when a correction is made. Record
who reviewed the exceptions through your organization's own workflow; finassert
does not supply a sign-off or policy-approval service.

Reports can contain financial values, row labels, identifiers and grouping keys.
Review them before sharing. Running locally does not make an exported report
safe to publish, and a diagnostic example cap is not an anonymization feature.

## 16. Assistant and MCP integration

The optional assistant server speaks MCP over stdio. It checks files inside
approved local roots using the same policy/loader/engine path as the CLI.

```bash
python -m pip install -e ".[assistant]"
finassert-assistant --root /path/to/approved-data
```

Register that command and its root arguments in the connected assistant's MCP
configuration. The allowed roots are the file-access boundary; the default is
the startup folder. Resolved paths and symbolic links cannot escape them.

| Tool | Use |
| --- | --- |
| `rules` | Discover allowed checks, settings and inappropriate uses |
| `templates` | Discover starter policies and pack metadata |
| `suggest` | Propose a template/column mapping for review |
| `check_policy` | Validate configuration text and explain issues |
| `inspect` | Inspect columns, row counts, previews and workbook sheets |
| `run_checks` | Execute policy text, file or template and return results |

Only `run_checks` can write an HTML report when a permitted `.html` destination
is supplied. Existing files require explicit overwrite. The assistant must not
describe an evaluation error as a pass or silently loosen tolerances/drop rules.

Results return to the assistant you connected. That assistant's own handling of
provided data is separate from the local engine's operation. The MCP stdio tools
are not HTTP workbook-upload endpoints. The guide's HTTP download API is also a
separate read-only documentation feature.

## 17. Retrieve this guide through the API

### Metadata and PDF routes

The existing Excel add-in server exposes the following read-only routes. Replace
the example origin with the actual local host/port where your build is served.

| Request | Response |
| --- | --- |
| `GET /api/finassert/v1/user-guide` | JSON identity metadata and download URL |
| `GET /api/finassert/v1/user-guide.pdf` | The validated PDF as a downloadable attachment |
| `HEAD` on either route | Same status/headers with no response body |

PDF responses use `Content-Type: application/pdf`, a fixed attachment filename,
`Content-Length`, `X-Content-Type-Options: nosniff` and `Cache-Control: no-store`.
The metadata includes schema version, title, product version, guide revision,
byte count and SHA-256. Read the revision and hash before caching or distributing
a copy. No workbook data, path parameter or private-checkout access is needed.

```bash
curl --fail --show-error \
  https://localhost:3002/api/finassert/v1/user-guide

curl --fail --show-error --output finassert-user-guide.pdf \
  https://localhost:3002/api/finassert/v1/user-guide.pdf
```

Use your trusted local CA configuration if curl does not use the same trust
store as Office. Do not disable certificate validation to paper over a trust or
hostname problem. This server's loopback address is reachable on the serving
computer; a colleague needs a downloaded copy or a separately approved deployment.
An installed Python wheel alone does not start this HTTP server.

For a Python download from a running server with trusted TLS:

```python
import json
from hashlib import sha256
from pathlib import Path
from urllib.request import urlopen

origin = "https://localhost:3002"
with urlopen(origin + "/api/finassert/v1/user-guide", timeout=30) as response:
    metadata = json.load(response)
with urlopen(origin + metadata["download_url"], timeout=30) as response:
    pdf = response.read()
assert len(pdf) == metadata["bytes"]
assert sha256(pdf).hexdigest() == metadata["sha256"]
Path("finassert-user-guide.pdf").write_bytes(pdf)
```

### Build, revision and failure behavior

The PDF is built ahead of time from this guide and the registered catalog; it is
not generated during a request. A verified identity sidecar travels with it.
The Excel builder checks that assets match their current source/catalog before
copying them. A maintainer can update the appendix and PDF with the build-only
tools; they are not required to import or use core finassert:

```bash
uv run --with reportlab==4.4.9 --with Markdown==3.11 \
  python scripts/build_user_guide.py --update-reference
```

A missing asset returns 404. A malformed/mismatched asset returns 503. Unknown
guide routes return 404. An error response is not a PDF; API clients should check
the status, MIME and hash rather than saving any HTTP body under a `.pdf` name.
The Excel pane offers **Download user guide (PDF)** as an explicit action.

## 18. Troubleshooting and known limits

| Symptom | Check and recovery |
| --- | --- |
| Add-in cannot load / Retry shown | Confirm the HTTPS server is running, manifest origin/port matches, and Excel trusts the certificate; retry after correcting setup |
| Engine never Ready | Inspect startup connectivity/CSP; use a verified bundled runtime if appropriate; do not treat startup failure as a pass |
| No table listed | Refresh the table picker and confirm the data is an actual structured table |
| Single-cell selection rejected | Select the exact header/data rectangle or explicitly choose a table |
| Range capability unavailable | Range binding needs ExcelApi 1.13; use an appropriate supported table path or update the host |
| Wrong dates / serial numbers | Confirm the workbook epoch, cell format and intended data schema; rebind/rerun after changes |
| Missing/duplicate headers | Give each populated source column one explicit, unique, nonblank header |
| Wrong matched column | Review the mapping; choose exact local/base-currency and semantic fields explicitly |
| Missing column / could not run | Fix the input/policy schema; null handling does not synthesize absent columns |
| Saved workbook formula lacks a result | Calculate and save in Excel, then reload; finassert does not calculate formulas |
| Manual/pending calculation blocks | Calculate in Excel, wait for Done, acknowledge manual calculation and retry |
| Result stays Stale | Read the reason; review source/policy/settings, use verified mode, and rerun |
| Snapshot-only cannot export | Restore verified captures and run again to obtain Current evidence |
| Cannot select a reported group | Missing groups have no row; ambiguous business keys need a unique mapping and rerun |
| Too many examples omitted | Read the complete count/truncation; increase max_violations only when useful for retained evidence |
| Read exceeds payload/time limits | Reduce per-request rows/cells; one row must fit; the total source ceiling remains fixed |
| Protected/colliding results destination | Use a new unique sheet; replace only an explicitly selected completed owned output |
| Incomplete results sheet | Correct the host/write problem and create fresh evidence; never infer completion |
| Guide download 404 / 503 | Rebuild missing/stale guide assets, rebuild the add-in and restart its server; inspect status/MIME/hash |
| CLI cannot write XLSX | Install the excel extra; check output path and cell-text limits |
| YAML cannot load | Install cli/yaml extra, inspect line issues and duplicate keys, or use a valid JSON policy |
| Assistant cannot access a file | Confirm the resolved file/report path is inside an approved root |

### Privacy and unsupported capabilities

The live engine executes in the Excel pane; the browser engine executes in its
tab. Startup loads the documented runtime/Office resources. The guide and the
optional reference panel make explicit local documentation requests without
reading/sending cells. The optional QuantSmith reader uses a pinned allowlisted
local checkout by default; its local owner may explicitly choose the matching
GitHub source. It stays separate from public guide downloads.

There is no automatic correction, source-cell highlighting, custom worksheet
function such as `FINASSERT.CHECK`, cross-workbook/multitable execution, saved
live-source configuration across pane sessions, remote validation upload API,
hosted scheduler, live FX provider or AppSource publication in this guide's
implemented scope. Polars/distributed integration and further financial packs
remain proposed unless separately delivered and documented.

## 19. Daily operating and demonstration playbook

### Before a control run

Confirm the source perimeter/date/currency/grain, the approved policy revision,
mandatory check inventory and permitted tolerance/sign settings. Preserve a
snapshot that another person can reproduce. In Excel, confirm binding bounds,
hidden/filtered inclusion and calculation state. A default template is a starting
point that still needs review.

### During exception review

Distinguish a true assertion failure from inability to evaluate. Inspect complete
counts as well as retained examples. Locate the source using its actual identity,
correct approved input errors, and keep the old failed evidence. Rebinding,
policy changes or material settings changes require another reviewed run.

### Before sharing

Require the expected checks to be present and evaluated; treat unexplained skips
and errors as incomplete control coverage. Export only a newly verified Current
live result. Confirm report identity/source bounds and that the output write
completed. Review confidentiality of included identifiers/values. Record human
review through your existing process.

### A five-minute product demonstration

1. Show the exact two-row source, 1904 date interpretation, and reviewed long-only
   policy in the prepared demo workbook.
2. Set F8 to -400 and run; explain one failed assertion versus two passes.
3. Follow the row-8 finding to F8.
4. Correct it to 400; point out Stale and disabled current exports.
5. Run again, show three passes/Current, and write a new results sheet.
6. Open the standalone HTML and its policy/source provenance.
7. Download this guide from the pane/API for the person reviewing the demo.

Keep broader host acceptance and external review separate from the demonstrated
workflow. Diagnostics create/replace a test data sheet and additional outputs;
run them only in a new disposable workbook, not a production working book.

## 20. Glossary and further reference

| Term | Meaning |
| --- | --- |
| Assertion | A configured condition that can pass or fail |
| Evaluation error | A check could not run reliably; never a pass |
| Severity | Business blocking level for an assertion failure |
| Null policy | Per-rule handling of permitted missing observations |
| Tolerance | Explicit inclusive allowance in a comparison's units |
| Grain | What one input row represents |
| Group key | Dimensions defining independent rule evaluations |
| Row key | Business label used where a rule supports portable identity |
| Physical row | The actual worksheet row number |
| Capture | One bounded read of the live source values/types/formats |
| Current | Matched source/policy at the last successful verification time |
| Stale | Historical live result needing a fresh run |
| Snapshot digest | Identity of a captured/evaluated source representation |
| Policy digest | Identity of the resolved policy configuration |
| Diagnostic cap | Maximum retained examples, not maximum evaluated rows |
| Owned output | A destination recorded by saved worksheet identity |
| Cached formula result | The value previously calculated and stored by Excel |
| Expected scope | Explicit universe including series that may be entirely absent |
| Pack coverage | Required checks present and evaluated, independent of default skip semantics |

Detailed repository references: [getting started](getting-started.md),
[policies and CLI](command-line.md), [Excel add-in](excel-add-in.md),
[browser application](browser-app.md), [Python API](reference/index.md),
[financial units](financial-units.md), [treasury example](examples/treasury-forecast.md),
[assistant server](assistant.md), [grouped validation](design/grouped-validation.md),
and [current project status](handoff.md).

The following appendices are generated from the current registered catalog and
templates. They include every exposed policy setting, defaults and applicability;
they do not expose private evaluators as additional public rules.

<!-- finassert-generated-reference:start -->

## Appendix A. Complete built-in rule reference

This reference covers all 21 registered built-in policy factories.
Required means the policy must supply the parameter. None means an optional
setting is unused by default. Defaults below are the catalog's declared values;
review the applicability and each field's units before changing them.

### A1. cash_continuity

**Cash connects between weeks**. Stable rule ID: `treasury.cash_continuity`.

Compares opening to prior closing cash on complete unique weekly series.

**Why use it:** Missing periods and disconnected balances can conceal treasury shortfalls.

**Do not use when:** The schedule is not weekly, scope is inferred from observed rows, balances change perimeter, or currencies require conversion.

| Parameter | Required / default | Meaning and allowed values |
| --- | --- | --- |
| `period_start` | Required | Inclusive ISO YYYY-MM-DD week start. Type: column. |
| `period_end` | Required | Exclusive ISO week end, seven days later. Type: column. |
| `group_by` | Required | Series columns including vintage/entity/scenario; currency is separate. Type: columns. |
| `currency` | Required | Mandatory explicit currency column; never inferred or converted. Type: column. |
| `expected_scope` | Required | Text mappings naming exactly the group and currency columns, including absent series. Type: records. |
| `first_period` | Required | Explicit ISO YYYY-MM-DD first week start; no weekday inference. Type: text. |
| `periods` | 13 | Consecutive calendar weeks; expected schedule capped at 100,000 rows. Type: integer. Minimum: 1. |
| `row_key` | None | Unique nonempty text labels; leave unused for native labels. Type: column. |
| `opening_cash` | Required | Opening balance in currency major units. Type: column. |
| `closing_cash` | Required | Closing balance in the same units. Type: column. |
| `tolerance` | 0 | Inclusive allowance between opening and prior closing cash. Type: tolerance. |
| `null_policy` | fail | What to do with blank amounts: 'fail' lists the rows as a failure, and 'skip' records the whole check as not run. Blanks are never treated as zero. Type: choice. Choices: fail, skip. |
| `severity` | error | 'error' (the default) fails the run. 'warning' and 'info' are listed in the report but do not fail the run. A check that could not run always fails it. Type: choice. Choices: error, warning, info. |
| `max_violations` | 20 | Maximum number of failing groups or rows listed in the report. Type: integer. Minimum: 0. |

### A2. cash_reconciles

**Cash balances roll forward**. Stable rule ID: `accounting.cash_reconciles`.

Checks that opening cash plus inflows, less outflows, plus any cash P&L, equals closing cash for each account.

**Why use it:** A cash balance that does not roll forward means a movement is missing, duplicated, or booked with the wrong sign, or a balance is stale.

**Do not use when:** Movements are recorded in a different currency from the balances, the file omits some movement types (such as fees or FX), or balances are as of different dates than the movements.

| Parameter | Required / default | Meaning and allowed values |
| --- | --- | --- |
| `outflow_sign` | Required | 'positive' if money paid out appears as positive amounts (they are subtracted), 'negative' if it appears as negative amounts (they are added). There is no default: a wrong guess would hide real breaks. Type: choice. Choices: positive, negative. |
| `opening_cash` | Required | Column with the balance at the start. Type: column. |
| `inflows` | Required | Column with cash received. Type: column. |
| `outflows` | Required | Column with cash paid out. Type: column. |
| `closing_cash` | Required | Column with the balance at the end. Type: column. |
| `cash_pnl` | None | Optional column with interest, fees, or other cash P&L. Leave empty if none. Type: column. |
| `group_by` | None | Columns that identify each account or portfolio, such as a portfolio code and a date. Leave empty to reconcile the whole file as one. Type: columns. |
| `currency` | None | Column holding each row's currency, so each currency reconciles separately. Leave empty only if every group is in one currency; amounts are never converted. Type: column. |
| `grain` | summary | 'summary': one row per account holds both balances and the total flows. 'transactions': each row is a movement carrying the balance before and after it, ordered by 'order_by'. Type: choice. Choices: summary, transactions. |
| `order_by` | None | Needed for 'transactions': a sequence number or timestamp that is unique within each account. A plain date works only if no two movements share the first or last date. Dates must be ISO (2026-01-31) or real date cells. Type: column. |
| `tolerance` | 0 | How far closing cash may be from the expected balance, in the currency's units, for example 0.01. Type: tolerance. |
| `null_policy` | fail | What to do with blank amounts: 'fail' lists the rows as a failure, and 'skip' records the whole check as not run. Blanks are never treated as zero. Type: choice. Choices: fail, skip. |
| `row_key` | None | Optional column, such as a ticker, used to name rows in the report. Without it rows are named by their position in the file. Type: column. |
| `severity` | error | 'error' (the default) fails the run. 'warning' and 'info' are listed in the report but do not fail the run. A check that could not run always fails it. Type: choice. Choices: error, warning, info. |
| `max_violations` | 20 | Maximum number of failing groups or rows listed in the report. Type: integer. Minimum: 0. |

### A3. drift_within_band

**Weights stay near their targets**. Stable rule ID: `portfolio.drift_within_band`.

Checks that no weight has drifted from its target by more than a band you set, and optionally that total drift stays within a limit.

**Why use it:** Drift beyond a tolerance is the usual trigger for rebalancing, and a portfolio far from its targets is no longer the portfolio that was approved.

**Do not use when:** Targets are not set for every position, drift is measured in market value or risk rather than weight, or small positions need a relative band (this check uses one absolute band for all positions).

| Parameter | Required / default | Meaning and allowed values |
| --- | --- | --- |
| `weight` | Required | Column with each current weight. Type: column. |
| `target_weight` | Required | Column with each position's target weight. Type: column. |
| `band` | None | Largest allowed difference between a weight and its target, as a fraction (0.02 is two percentage points). Inclusive. Type: number. Nonnegative values. |
| `total_limit` | None | Optional limit on the sum of all absolute drifts in a portfolio. Set a band, a total limit, or both. Type: number. Nonnegative values. |
| `group_by` | None | Columns that identify each portfolio, such as a portfolio code, so every portfolio is checked on its own. Leave empty if the file holds a single portfolio. Type: columns. |
| `row_key` | None | Optional column, such as a ticker, used to name rows in the report. Without it rows are named by their position in the file. Type: column. |
| `null_policy` | fail | What to do with blank amounts: 'fail' lists the rows as a failure, and 'skip' records the whole check as not run. Blanks are never treated as zero. Type: choice. Choices: fail, skip. |
| `severity` | warning | 'warning' (the default for drift) lists the drift but does not fail the run; 'error' fails the run. A check that could not run always fails it. Type: choice. Choices: error, warning, info. |
| `max_violations` | 20 | Maximum number of failing groups or rows listed in the report. Type: integer. Minimum: 0. |

### A4. facility_capacity

**Facility principal and capacity reconcile**. Stable rule ID: `treasury.facility_capacity`.

Check principal, capacity, continuity and maturity per facility.

**Why use it:** A balanced cash forecast may exceed usable funding or retain matured debt.

**Do not use when:** Intraperiod usage or maturity, conditional eligibility, legal availability or a borrowing base must be established.

| Parameter | Required / default | Meaning and allowed values |
| --- | --- | --- |
| `period_start` | Required | Inclusive ISO YYYY-MM-DD week start. Type: column. |
| `period_end` | Required | Exclusive ISO week end, seven days later. Type: column. |
| `group_by` | Required | Series columns including vintage/entity/scenario; currency is separate. Type: columns. |
| `currency` | Required | Mandatory explicit currency column; never inferred or converted. Type: column. |
| `expected_scope` | Required | Text mappings naming exactly the group and currency columns, including absent series. Type: records. |
| `first_period` | Required | Explicit ISO YYYY-MM-DD first week start; no weekday inference. Type: text. |
| `periods` | 13 | Consecutive calendar weeks; expected schedule capped at 100,000 rows. Type: integer. Minimum: 1. |
| `row_key` | None | Unique nonempty text labels; leave unused for native labels. Type: column. |
| `facility_id` | Required | Facility key added to group_by; include it in expected_scope. Type: column. |
| `opening_drawn` | Required | Nonnegative opening principal, major units. Type: column. |
| `draws` | Required | Nonnegative new principal draws. Type: column. |
| `repayments` | Required | Nonnegative repayment magnitudes. Type: column. |
| `closing_drawn` | Required | Nonnegative closing principal. Type: column. |
| `commitment` | Required | Nonnegative effective contractual commitment. Type: column. |
| `unavailable_amount` | Required | Nonnegative disjoint reduction excluding drawn amounts. Type: column. |
| `maturity_date` | Required | ISO YYYY-MM-DD maturity; intraperiod maturity errors. Type: column. |
| `tolerance` | 0 | Inclusive amount allowance; zero by default, signs remain strict. Type: tolerance. |
| `null_policy` | fail | What to do with blank amounts: 'fail' lists the rows as a failure, and 'skip' records the whole check as not run. Blanks are never treated as zero. Type: choice. Choices: fail, skip. |
| `severity` | error | 'error' (the default) fails the run. 'warning' and 'info' are listed in the report but do not fail the run. A check that could not run always fails it. Type: choice. Choices: error, warning, info. |
| `max_violations` | 20 | Maximum number of failing groups or rows listed in the report. Type: integer. Minimum: 0. |

### A5. forecast_coverage

**Forecast covers every expected week**. Stable rule ID: `treasury.forecast_coverage`.

Requires one row per expected group, currency and calendar week.

**Why use it:** Missing periods and disconnected balances can conceal treasury shortfalls.

**Do not use when:** The schedule is not weekly, scope is inferred from observed rows, balances change perimeter, or currencies require conversion.

| Parameter | Required / default | Meaning and allowed values |
| --- | --- | --- |
| `period_start` | Required | Inclusive ISO YYYY-MM-DD week start. Type: column. |
| `period_end` | Required | Exclusive ISO week end, seven days later. Type: column. |
| `group_by` | Required | Series columns including vintage/entity/scenario; currency is separate. Type: columns. |
| `currency` | Required | Mandatory explicit currency column; never inferred or converted. Type: column. |
| `expected_scope` | Required | Text mappings naming exactly the group and currency columns, including absent series. Type: records. |
| `first_period` | Required | Explicit ISO YYYY-MM-DD first week start; no weekday inference. Type: text. |
| `periods` | 13 | Consecutive calendar weeks; expected schedule capped at 100,000 rows. Type: integer. Minimum: 1. |
| `row_key` | None | Unique nonempty text labels; leave unused for native labels. Type: column. |
| `severity` | error | 'error' (the default) fails the run. 'warning' and 'info' are listed in the report but do not fail the run. A check that could not run always fails it. Type: choice. Choices: error, warning, info. |
| `max_violations` | 20 | Maximum number of failing groups or rows listed in the report. Type: integer. Minimum: 0. |

### A6. gross_within_limit

**Gross exposure is within its limit**. Stable rule ID: `exposure.gross_within_limit`.

Checks that the total of the absolute values (longs plus shorts) of each portfolio, as a fraction of its base, is within the limits you set.

**Why use it:** Gross exposure measures leverage; a breach means the book is bigger than its mandate allows, or a position was entered at the wrong size.

**Do not use when:** The file holds several portfolios and you have not chosen a column to check each one by, values are in several currencies without a currency column, derivatives are listed at market value rather than notional while the limit is on notional, or the base is not in the same currency as the values.

| Parameter | Required / default | Meaning and allowed values |
| --- | --- | --- |
| `value` | Required | Column with each position's signed weight or market value; shorts are negative. Type: column. |
| `base` | None | Optional column with the amount exposure is measured against, such as the portfolio's NAV, on every row or some rows of each portfolio. Leave empty if the value column already holds weights. Type: column. |
| `maximum` | None | Largest allowed exposure as a fraction (1.3 means 130%). Inclusive. Type: number. Nonnegative values. |
| `minimum` | None | Smallest allowed exposure as a fraction. Inclusive. Set a highest, a lowest, or both. Type: number. Nonnegative values. |
| `group_by` | None | Columns that identify each account or portfolio, such as a portfolio code and a date. Leave empty to reconcile the whole file as one. Type: columns. |
| `currency` | None | Column holding each row's currency, so each currency reconciles separately. Leave empty only if every group is in one currency; amounts are never converted. Type: column. |
| `null_policy` | fail | What to do with blank amounts: 'fail' lists the rows as a failure, and 'skip' records the whole check as not run. Blanks are never treated as zero. Type: choice. Choices: fail, skip. |
| `severity` | error | 'error' (the default) fails the run. 'warning' and 'info' are listed in the report but do not fail the run. A check that could not run always fails it. Type: choice. Choices: error, warning, info. |
| `max_violations` | 20 | Maximum number of failing groups or rows listed in the report. Type: integer. Minimum: 0. |

### A7. in_range

**Values stay within a range**. Stable rule ID: `arithmetic.in_range`.

Checks that every value in a column is between a lowest and a highest value.

**Why use it:** A cash weight of 140%, a leverage of -3x, or a rate of 4000% is usually a unit or sign error, and downstream calculations will quietly use it.

**Do not use when:** The range is not a fact about the data but a choice you have not made yet, the column mixes units (percent and fractions), or the legitimate range differs by row, such as by asset class.

| Parameter | Required / default | Meaning and allowed values |
| --- | --- | --- |
| `column` | Required | Column whose values must stay within the range. Type: column. |
| `minimum` | None | Smallest allowed value, inclusive. Set a lowest, a highest, or both. Type: number. Negative values allowed. |
| `maximum` | None | Largest allowed value, inclusive. Set a highest, a lowest, or both. Type: number. Negative values allowed. |
| `tolerance` | 0 | How far beyond either limit a value may be and still pass, for example 0.01 to tolerate rounding. Type: tolerance. Absolute allowance only; relative must be zero. |
| `null_policy` | fail | What to do with blank cells: 'fail' treats them as a failure, 'ignore' leaves them out, and 'skip' records the whole check as not run. Type: choice. Choices: fail, ignore, skip. |
| `severity` | error | 'error' (the default) fails the run. 'warning' and 'info' are listed in the report but do not fail the run. A check that could not run always fails it. Type: choice. Choices: error, warning, info. |
| `max_violations` | 20 | Maximum number of offending rows listed in the report. Type: integer. Minimum: 0. |
| `row_key` | None | Optional column, such as a ticker, used to name rows in the report. Without it rows are named by their position in the file. Type: column. |

### A8. market_value_reconciles

**Market value equals quantity times price**. Stable rule ID: `accounting.market_value_reconciles`.

Checks, on every row, that the reported market value equals quantity times price (times a contract multiplier, if there is one).

**Why use it:** A market value that disagrees with its own quantity and price means a stale price, a wrong multiplier, a sign error, or a hand-edited cell.

**Do not use when:** Prices are quoted per 100 of par (bonds) or as a percentage, the price and the market value are in different currencies, or the market value includes accrued interest that the price does not.

| Parameter | Required / default | Meaning and allowed values |
| --- | --- | --- |
| `quantity` | Required | Column with units held; shorts are negative. Type: column. |
| `price` | Required | Column with the price of one unit. Type: column. |
| `market_value` | Required | Column with the market value. Type: column. |
| `multiplier` | None | Optional column with a contract multiplier. Leave empty if there is none. Type: column. |
| `row_key` | None | Optional column, such as a ticker, used to name rows in the report. Without it rows are named by their position in the file. Type: column. |
| `tolerance` | 0 | How far the market value may be from quantity times price, in its own units, for example 0.01. A relative allowance also covers prices rounded before multiplying. Type: tolerance. |
| `null_policy` | fail | What to do with blank amounts: 'fail' lists the rows as a failure, and 'skip' records the whole check as not run. Blanks are never treated as zero. Type: choice. Choices: fail, skip. |
| `severity` | error | 'error' (the default) fails the run. 'warning' and 'info' are listed in the report but do not fail the run. A check that could not run always fails it. Type: choice. Choices: error, warning, info. |
| `max_violations` | 20 | Maximum number of failing groups or rows listed in the report. Type: integer. Minimum: 0. |

### A9. minimum_cash_buffer

**Available cash meets its minimum**. Stable rule ID: `treasury.minimum_cash_buffer`.

Closing cash less restricted cash must meet each row's explicit minimum.

**Why use it:** Restricted funds cannot meet an unrestricted liquidity requirement.

**Do not use when:** Facilities are treated as cash, currencies need conversion, or limits are unspecified.

| Parameter | Required / default | Meaning and allowed values |
| --- | --- | --- |
| `period_start` | Required | Inclusive ISO YYYY-MM-DD week start. Type: column. |
| `period_end` | Required | Exclusive ISO week end, seven days later. Type: column. |
| `group_by` | Required | Series columns including vintage/entity/scenario; currency is separate. Type: columns. |
| `currency` | Required | Mandatory explicit currency column; never inferred or converted. Type: column. |
| `expected_scope` | Required | Text mappings naming exactly the group and currency columns, including absent series. Type: records. |
| `first_period` | Required | Explicit ISO YYYY-MM-DD first week start; no weekday inference. Type: text. |
| `periods` | 13 | Consecutive calendar weeks; expected schedule capped at 100,000 rows. Type: integer. Minimum: 1. |
| `row_key` | None | Unique nonempty text labels; leave unused for native labels. Type: column. |
| `closing_cash` | Required | Cash including restricted balances, major units. Type: column. |
| `restricted_cash` | Required | Nonnegative restricted cash in the same units. Type: column. |
| `minimum_buffer` | Required | Nonnegative caller-owned minimum column. Type: column. |
| `tolerance` | 0 | Inclusive shortfall allowance; zero by default. Type: tolerance. |
| `null_policy` | fail | What to do with blank amounts: 'fail' lists the rows as a failure, and 'skip' records the whole check as not run. Blanks are never treated as zero. Type: choice. Choices: fail, skip. |
| `severity` | error | 'error' (the default) fails the run. 'warning' and 'info' are listed in the report but do not fail the run. A check that could not run always fails it. Type: choice. Choices: error, warning, info. |
| `max_violations` | 20 | Maximum number of failing groups or rows listed in the report. Type: integer. Minimum: 0. |

### A10. monthly_performance_audit

**Monthly performance matches periodic returns**. Stable rule ID: `performance.monthly_performance_audit`.

Checks monthly coverage and inputs, then ties reported strategy and benchmark cumulative returns to the periodic returns.

**Why use it:** Missing months, mis-scaled inputs, or a cumulative figure that does not follow from the underlying returns can make a performance report misleading.

**Do not use when:** Returns are cash-flow reconstructed, the strategy or benchmark changes during the window, or the supplied series do not represent one declared comparison.

| Parameter | Required / default | Meaning and allowed values |
| --- | --- | --- |
| `period_end` | Required | Column with each source row's ISO calendar month-end date. Type: column. |
| `strategy_return` | Required | Column with the supplied simple monthly strategy total return. Type: column. |
| `benchmark_return` | Required | Column with the paired simple monthly benchmark total return. Type: column. |
| `reported_strategy_cumulative` | Required | Column with the strategy return linked from the first month through each row. Type: column. |
| `reported_benchmark_cumulative` | Required | Column with the benchmark return linked from the first month through each row. Type: column. |
| `window_start` | Required | Required inclusive ISO YYYY-MM-DD calendar month-end. Type: text. |
| `window_end` | Required | Required inclusive ISO YYYY-MM-DD calendar month-end. Type: text. |
| `periodic_return_unit` | Required | Declare fraction when 0.05 means 5%; percent when 5 means 5%. Type: choice. Choices: fraction, percent. |
| `reported_return_unit` | Required | Declare the reported cumulative columns' unit independently. Type: choice. Choices: fraction, percent. |
| `strategy_id` | Required | Declared identifier for the strategy series. Type: text. |
| `benchmark_id` | Required | Declared identifier for the benchmark series. Type: text. |
| `base_currency` | Required | Three-letter ISO 4217 code or explicit UNIT:identifier, normalized to uppercase. Type: text. |
| `valuation_convention` | Required | Required analyst declaration; retained in the policy report. Type: text. |
| `strategy_fee_treatment` | Required | Required analyst declaration of fees included in the strategy returns. Type: text. |
| `benchmark_fee_treatment` | Required | Required analyst declaration of fees included in the benchmark returns. Type: text. |
| `tolerance` | Required | Absolute allowance in decimal-return fractions; relative tolerance is zero. Type: tolerance. Absolute allowance only; relative must be zero. |
| `row_key` | None | Optional column, such as a ticker, used to name rows in the report. Without it rows are named by their position in the file. Type: column. |
| `severity` | error | 'error' (the default) fails the run. 'warning' and 'info' are listed in the report but do not fail the run. A check that could not run always fails it. Type: choice. Choices: error, warning, info. |
| `max_violations` | 20 | Maximum number of failing groups or rows listed in the report. Type: integer. Minimum: 0. |

### A11. nav_reconciles

**Market values add up to the NAV**. Stable rule ID: `accounting.nav_reconciles`.

Checks that the market values of every line in a portfolio add up to its reported net asset value (NAV).

**Why use it:** If holdings do not add up to the NAV, a position is missing or duplicated, a price is stale, or the NAV was struck on different data.

**Do not use when:** Liabilities, accruals, or cash are not rows in the file, liabilities are stored as positive numbers, or market values are in local currencies while the NAV is in the base currency.

| Parameter | Required / default | Meaning and allowed values |
| --- | --- | --- |
| `market_value` | Required | Column with each line's signed market value; liabilities and short positions are negative. Type: column. |
| `nav` | Required | Column with the reported NAV, on every row or on some rows of each portfolio. Type: column. |
| `group_by` | None | Columns that identify each account or portfolio, such as a portfolio code and a date. Leave empty to reconcile the whole file as one. Type: columns. |
| `currency` | None | Column holding each row's currency, so each currency reconciles separately. Leave empty only if every group is in one currency; amounts are never converted. Type: column. |
| `tolerance` | 0 | How far the total may be from the NAV, in the currency's units, for example 0.01. Type: tolerance. |
| `null_policy` | fail | What to do with blank amounts: 'fail' lists the rows as a failure, and 'skip' records the whole check as not run. Blanks are never treated as zero. Type: choice. Choices: fail, skip. |
| `severity` | error | 'error' (the default) fails the run. 'warning' and 'info' are listed in the report but do not fail the run. A check that could not run always fails it. Type: choice. Choices: error, warning, info. |
| `max_violations` | 20 | Maximum number of failing groups or rows listed in the report. Type: integer. Minimum: 0. |

### A12. net_within_limit

**Net exposure is within its limit**. Stable rule ID: `exposure.net_within_limit`.

Checks that the total of the signed values (shorts offset longs) of each portfolio, as a fraction of its base, is within the limits you set.

**Why use it:** Net exposure measures directional market risk; a breach means the book is more long or short than its mandate allows.

**Do not use when:** The file holds several portfolios and you have not chosen a column to check each one by, values are in several currencies without a currency column, derivatives are listed at market value rather than notional while the limit is on notional, or the base is not in the same currency as the values.

| Parameter | Required / default | Meaning and allowed values |
| --- | --- | --- |
| `value` | Required | Column with each position's signed weight or market value; shorts are negative. Type: column. |
| `base` | None | Optional column with the amount exposure is measured against, such as the portfolio's NAV, on every row or some rows of each portfolio. Leave empty if the value column already holds weights. Type: column. |
| `maximum` | None | Largest allowed exposure as a fraction (1.3 means 130%). Inclusive. Type: number. Negative values allowed. |
| `minimum` | None | Smallest allowed exposure as a fraction. Inclusive. Set a highest, a lowest, or both. Type: number. Negative values allowed. |
| `group_by` | None | Columns that identify each account or portfolio, such as a portfolio code and a date. Leave empty to reconcile the whole file as one. Type: columns. |
| `currency` | None | Column holding each row's currency, so each currency reconciles separately. Leave empty only if every group is in one currency; amounts are never converted. Type: column. |
| `null_policy` | fail | What to do with blank amounts: 'fail' lists the rows as a failure, and 'skip' records the whole check as not run. Blanks are never treated as zero. Type: choice. Choices: fail, skip. |
| `severity` | error | 'error' (the default) fails the run. 'warning' and 'info' are listed in the report but do not fail the run. A check that could not run always fails it. Type: choice. Choices: error, warning, info. |
| `max_violations` | 20 | Maximum number of failing groups or rows listed in the report. Type: integer. Minimum: 0. |

### A13. no_duplicates

**Each item appears only once**. Stable rule ID: `data.no_duplicates`.

Checks that no value, or combination of values, appears on more than one row.

**Why use it:** A position or transaction listed twice double-counts value and exposure, and usually means two extracts were combined or a row was pasted twice.

**Do not use when:** A repeated identifier is legitimate: several tax lots of one security, one row per trade or per date, or the columns chosen do not identify a row. Text is compared exactly, so 'AAPL' and 'aapl ' count as different; numbers compare by value, so 1 and 1.0 count as the same.

| Parameter | Required / default | Meaning and allowed values |
| --- | --- | --- |
| `columns` | Required | Column, or columns taken together, that must be unique, for example portfolio and ticker. Type: columns. |
| `null_policy` | fail | What to do with blank cells: 'fail' treats them as a failure, 'ignore' leaves them out, and 'skip' records the whole check as not run. Type: choice. Choices: fail, ignore, skip. |
| `severity` | error | 'error' (the default) fails the run. 'warning' and 'info' are listed in the report but do not fail the run. A check that could not run always fails it. Type: choice. Choices: error, warning, info. |
| `max_violations` | 20 | Maximum number of repeated values listed in the report. Type: integer. Minimum: 0. |

### A14. non_negative

**No negative values**. Stable rule ID: `arithmetic.non_negative`.

Checks that no value in a column is below zero.

**Why use it:** Quantities such as market value, notional, prices, or fees cannot be negative by definition; a negative value usually signals a sign or booking error.

**Do not use when:** The column can legitimately be negative, such as weights or quantities of a portfolio with short positions, P&L, or cash balances.

| Parameter | Required / default | Meaning and allowed values |
| --- | --- | --- |
| `column` | Required | Column whose values must not be negative. Type: column. |
| `tolerance` | 0 | How far below zero a value may be and still pass, for example 0.01 to tolerate rounding. Type: tolerance. Absolute allowance only; relative must be zero. |
| `null_policy` | fail | What to do with blank cells: 'fail' treats them as a failure, 'ignore' leaves them out, and 'skip' records the whole check as not run. Type: choice. Choices: fail, ignore, skip. |
| `severity` | error | 'error' (the default) fails the run. 'warning' and 'info' are listed in the report but do not fail the run. A check that could not run always fails it. Type: choice. Choices: error, warning, info. |
| `max_violations` | 20 | Maximum number of offending rows listed in the report. Type: integer. Minimum: 0. |

### A15. position_rolls_forward

**Position quantities roll forward**. Stable rule ID: `accounting.position_rolls_forward`.

Checks that each position's opening quantity plus buys, less sells, plus any other movements, equals its closing quantity.

**Why use it:** A closing quantity that does not follow from the opening quantity and the trades means a trade is missing or booked twice, a sell has the wrong sign, or a corporate action was not applied.

**Do not use when:** Trades are listed on several rows with a running quantity (combine them first), the quantities are in different units on different rows, or movements such as splits and transfers are not in the file and not in the adjustments column.

| Parameter | Required / default | Meaning and allowed values |
| --- | --- | --- |
| `sell_sign` | Required | 'positive' if quantities sold appear as positive numbers (they are subtracted), 'negative' if they appear as negative numbers (they are added). There is no default: a wrong guess would hide real breaks. Type: choice. Choices: positive, negative. |
| `opening_quantity` | Required | Column with the quantity at the start. Type: column. |
| `buys` | Required | Column with the quantity bought. Type: column. |
| `sells` | Required | Column with the quantity sold. Type: column. |
| `closing_quantity` | Required | Column with the quantity at the end. Type: column. |
| `adjustments` | None | Optional column with splits, transfers, or corporate actions, added to the opening quantity. Leave empty if none. Type: column. |
| `group_by` | Required | Columns that identify one position, such as portfolio and ticker. Each position is one row, or several rows that agree. Type: columns. |
| `row_key` | None | Optional column, such as a ticker, used to name rows in the report. Without it rows are named by their position in the file. Type: column. |
| `tolerance` | 0 | How far the closing quantity may be from the expected one, in units of the security, for example 0.0001 for fractional shares. Type: tolerance. |
| `null_policy` | fail | What to do with blank amounts: 'fail' lists the rows as a failure, and 'skip' records the whole check as not run. Blanks are never treated as zero. Type: choice. Choices: fail, skip. |
| `severity` | error | 'error' (the default) fails the run. 'warning' and 'info' are listed in the report but do not fail the run. A check that could not run always fails it. Type: choice. Choices: error, warning, info. |
| `max_violations` | 20 | Maximum number of failing groups or rows listed in the report. Type: integer. Minimum: 0. |

### A16. position_within_limit

**No single position is too large**. Stable rule ID: `exposure.position_within_limit`.

Checks that no position, long or short, is larger than the limit you set, as a fraction of its portfolio's base.

**Why use it:** Concentration in one name is a classic mandate breach, and often the symptom of a mis-sized order or a duplicated line.

**Do not use when:** The limit applies to a whole issuer or sector rather than to single lines (use a gross exposure check grouped by that column instead), or the same security appears on several rows.

| Parameter | Required / default | Meaning and allowed values |
| --- | --- | --- |
| `value` | Required | Column with each position's signed weight or market value. Type: column. |
| `base` | None | Optional column with the amount exposure is measured against, such as the portfolio's NAV, on every row or some rows of each portfolio. Leave empty if the value column already holds weights. Type: column. |
| `maximum` | Required | Largest allowed position as a fraction (0.1 means 10%). Inclusive. Type: number. Nonnegative values. |
| `group_by` | None | Columns that identify each account or portfolio, such as a portfolio code and a date. Leave empty to reconcile the whole file as one. Type: columns. |
| `currency` | None | Column holding each row's currency, so each currency reconciles separately. Leave empty only if every group is in one currency; amounts are never converted. Type: column. |
| `row_key` | None | Optional column, such as a ticker, used to name rows in the report. Without it rows are named by their position in the file. Type: column. |
| `null_policy` | fail | What to do with blank amounts: 'fail' lists the rows as a failure, and 'skip' records the whole check as not run. Blanks are never treated as zero. Type: choice. Choices: fail, skip. |
| `severity` | error | 'error' (the default) fails the run. 'warning' and 'info' are listed in the report but do not fail the run. A check that could not run always fails it. Type: choice. Choices: error, warning, info. |
| `max_violations` | 20 | Maximum number of failing groups or rows listed in the report. Type: integer. Minimum: 0. |

### A17. required_fields

**Required fields are filled in**. Stable rule ID: `data.required_fields`.

Checks that none of the chosen columns has a blank cell.

**Why use it:** A missing identifier, price, or quantity usually means an incomplete export, and downstream totals may silently skip the row or treat it as zero.

**Do not use when:** A column is legitimately empty on some rows, such as an optional comment, or a price on cash lines. A cell of only spaces counts as blank; zero does not.

| Parameter | Required / default | Meaning and allowed values |
| --- | --- | --- |
| `columns` | Required | Columns that must have a value on every row. Type: columns. |
| `severity` | error | 'error' (the default) fails the run. 'warning' and 'info' are listed in the report but do not fail the run. A check that could not run always fails it. Type: choice. Choices: error, warning, info. |
| `max_violations` | 20 | Maximum number of blank rows listed for each column. Type: integer. Minimum: 0. |

### A18. simple_return_reconciles

**Reported returns follow from the values**. Stable rule ID: `returns.simple_return_reconciles`.

Checks, on every row, that the reported return equals (ending value - beginning value - net flows) divided by the beginning value.

**Why use it:** A return that does not follow from its own start and end values usually means a different denominator, stale values, or flows that were handled twice.

**Do not use when:** Money moves in or out during the period and the file reports a time-weighted or Modified Dietz return, returns are compounded over several periods, or returns are reported net of fees that the values do not reflect.

| Parameter | Required / default | Meaning and allowed values |
| --- | --- | --- |
| `beginning_value` | Required | Value at the start of the period. Type: column. |
| `ending_value` | Required | Value at the end of the period. Type: column. |
| `reported_return` | Required | The return the file reports. Type: column. |
| `return_unit` | Required | 'fraction' if 0.05 means 5%, 'percent' if 5 means 5%. There is no default: a wrong guess is off by a factor of 100. Type: choice. Choices: fraction, percent. |
| `net_flows` | None | Optional column with money added (positive) or withdrawn (negative) during the period. Leave empty if none. Type: column. |
| `row_key` | None | Optional column, such as a ticker, used to name rows in the report. Without it rows are named by their position in the file. Type: column. |
| `tolerance` | 0 | How far the reported return may be from the computed one, in the return's own unit, for example 0.0001 for a fraction. Type: tolerance. |
| `null_policy` | fail | What to do with blank amounts: 'fail' lists the rows as a failure, and 'skip' records the whole check as not run. Blanks are never treated as zero. Type: choice. Choices: fail, skip. |
| `severity` | error | 'error' (the default) fails the run. 'warning' and 'info' are listed in the report but do not fail the run. A check that could not run always fails it. Type: choice. Choices: error, warning, info. |
| `max_violations` | 20 | Maximum number of failing groups or rows listed in the report. Type: integer. Minimum: 0. |

### A19. turnover_within_limit

**Turnover stays within a limit**. Stable rule ID: `portfolio.turnover_within_limit`.

Checks that the change from the previous weights, summed over every position, stays within a limit you set.

**Why use it:** Turnover drives trading costs and often has a mandate or budget limit; an unexpectedly high figure usually means stale previous weights or a mapping error.

**Do not use when:** The previous weights are not on the same basis (different NAV or date), positions that were not held before have a blank instead of 0, or turnover should be measured in market value or after cash flows.

| Parameter | Required / default | Meaning and allowed values |
| --- | --- | --- |
| `weight` | Required | Column with each current weight. Type: column. |
| `previous_weight` | Required | Column with the previous weight. Use 0, not blank, for a position not held before. Type: column. |
| `sides` | Required | 'one_way' is half the sum of absolute changes (each unit sold funds a unit bought); 'two_way' is the full sum. There is no default: the two differ by a factor of 2. Type: choice. Choices: one_way, two_way. |
| `maximum` | Required | Largest allowed turnover as a fraction (0.2 is 20%). Inclusive. Type: number. Nonnegative values. |
| `group_by` | None | Columns that identify each portfolio, such as a portfolio code, so every portfolio is checked on its own. Leave empty if the file holds a single portfolio. Type: columns. |
| `row_key` | None | Optional column, such as a ticker, used to name rows in the report. Without it rows are named by their position in the file. Type: column. |
| `null_policy` | fail | What to do with blank amounts: 'fail' lists the rows as a failure, and 'skip' records the whole check as not run. Blanks are never treated as zero. Type: choice. Choices: fail, skip. |
| `severity` | error | 'error' (the default) fails the run. 'warning' and 'info' are listed in the report but do not fail the run. A check that could not run always fails it. Type: choice. Choices: error, warning, info. |
| `max_violations` | 20 | Maximum number of failing groups or rows listed in the report. Type: integer. Minimum: 0. |

### A20. weights_match_market_values

**Weights match market values**. Stable rule ID: `portfolio.weights_match_market_values`.

Checks that each weight equals its market value divided by the portfolio's NAV (or by its total market value if there is no NAV column).

**Why use it:** Weights that were not refreshed after prices moved no longer describe the portfolio, so exposures, attribution, and rebalancing trades built on them will be wrong even though they still add up to 1.

**Do not use when:** Weights are measured against something other than NAV or total market value (for example gross exposure), market values and NAV are in different currencies, or the weights are deliberately target weights, not current ones.

| Parameter | Required / default | Meaning and allowed values |
| --- | --- | --- |
| `weight` | Required | Column with each weight as a fraction of 1. Type: column. |
| `market_value` | Required | Column with each signed market value. Type: column. |
| `nav` | None | Optional column with the portfolio's NAV, on every row or some rows of each portfolio. Leave empty to measure against the total market value. Type: column. |
| `group_by` | None | Columns that identify each portfolio, such as a portfolio code, so every portfolio is checked on its own. Leave empty if the file holds a single portfolio. Type: columns. |
| `row_key` | None | Optional column, such as a ticker, used to name rows in the report. Without it rows are named by their position in the file. Type: column. |
| `tolerance` | 1e-8 | How far a weight may be from its expected value and still pass, as a fraction: 0.0001 is one basis point. Type: tolerance. |
| `null_policy` | fail | What to do with blank amounts: 'fail' lists the rows as a failure, and 'skip' records the whole check as not run. Blanks are never treated as zero. Type: choice. Choices: fail, skip. |
| `severity` | error | 'error' (the default) fails the run. 'warning' and 'info' are listed in the report but do not fail the run. A check that could not run always fails it. Type: choice. Choices: error, warning, info. |
| `max_violations` | 20 | Maximum number of failing groups or rows listed in the report. Type: integer. Minimum: 0. |

### A21. weights_sum_to_one

**Portfolio weights add up to 100%**. Stable rule ID: `portfolio.weights_sum_to_one`.

Checks that the values in a weight column add up to exactly 1, for the whole file or for each portfolio.

**Why use it:** Weights that do not add to 1 mean some holdings are missing, duplicated, or mis-scaled, so exposures and performance attribution will be wrong.

**Do not use when:** Weights are written as percentages (40 rather than 0.4), the file holds several portfolios and you have not chosen a column to check each one by, or the portfolio is deliberately levered or holds cash outside the weight column.

| Parameter | Required / default | Meaning and allowed values |
| --- | --- | --- |
| `column` | weight | Column holding each position's weight as a fraction of 1. Type: column. |
| `tolerance` | 1e-8 | How far the total may be from 1 and still pass, for example 0.0001. Type: tolerance. |
| `null_policy` | fail | What to do with blank cells: 'fail' treats them as a failure, 'ignore' leaves them out, and 'skip' records the whole check as not run. Type: choice. Choices: fail, ignore, skip. |
| `severity` | error | 'error' (the default) fails the run. 'warning' and 'info' are listed in the report but do not fail the run. A check that could not run always fails it. Type: choice. Choices: error, warning, info. |
| `group_by` | None | Columns that identify each portfolio, such as a portfolio code, so every portfolio must add up to 1. Leave empty if the file holds a single portfolio. Type: columns. |
| `max_violations` | 20 | Maximum number of failing groups or rows listed in the report. Type: integer. Minimum: 0. |

## Appendix B. Complete starter-template reference

All 11 current templates are ordinary policies.
Use finassert init to emit the full YAML. Replace sample schema/scope/date
settings, confirm proposed matches, and review every assumption. Templates
do not supply a mandate limit or establish required-control completeness.

### B1. cash-reconciliation

**Daily cash reconciliation**. One row per portfolio, currency, and day with balances and total flows.

Create with `finassert init --template cash-reconciliation --output policy.yml`.

Included checks: `cash_reconciles`.

**Adapt before use:**

- Set each column to the header your file uses.
- Set 'outflow_sign' to how your file records money paid out.
- Set the 'tolerance' in currency units; "0.01" allows one cent.

**Assumptions:**

- Each row covers one portfolio, currency, and day.
- Inflows, outflows, and cash income or expense include every movement between the two balances, fees and FX included.
- Opening and closing balances are as of the start and end of the same day as the movements.

### B2. long-only-holdings

**Long-only holdings file**. Daily holdings of one long-only portfolio, with cash held as a position.

Create with `finassert init --template long-only-holdings --output policy.yml`.

Included checks: `weights_sum_to_one`, `non_negative`, `non_negative`.

**Adapt before use:**

- Set each 'column' to the header your file uses.
- Set the weight 'tolerance' to how your weights are rounded; "0.0001" allows one basis point.

**Assumptions:**

- The file holds exactly one portfolio.
- Weights are fractions of total portfolio value (0.25, not 25).
- Cash is a position in the file, so weights include it.
- The portfolio holds no short positions and no instruments that can have a negative market value, such as swaps or futures.

### B3. monthly-performance-audit

**Monthly strategy and benchmark audit**. Monthly periodic and reported cumulative total returns for one declared strategy and benchmark.

Create with `finassert init --template monthly-performance-audit --output policy.yml`.

Included checks: `monthly_performance_audit`.

**Adapt before use:**

- Map each column name and set the inclusive first and last month ends to match your file.
- Replace the strategy, benchmark, currency, valuation, and fee declarations with the policy that produced your returns.
- Confirm periodic and reported return units separately; both default to fractions.
- Set the absolute tolerance in decimal-return fractions to match your reporting precision.
- The companion synthetic 2024 fixture intentionally fails on the June strategy cumulative value until that source figure is corrected.

**Assumptions:**

- Each row is one calendar month in one stable strategy and benchmark comparison.
- Periodic values are simple total returns with no intraperiod cash-flow reconstruction.
- The synthetic example reports strategy returns net of management and transaction costs and benchmark returns gross of fees.
- Both source series are denominated in USD and use calendar month-end valuation.
- The synthetic 2024 example contains a deliberate June strategy cumulative discrepancy for the correction walkthrough.

### B4. multi-portfolio-holdings

**Holdings of several portfolios**. One file of positions for many portfolios, with weights, market values, and NAV.

Create with `finassert init --template multi-portfolio-holdings --output policy.yml`.

Included checks: `required_fields`, `no_duplicates`, `weights_sum_to_one`, `nav_reconciles`.

**Adapt before use:**

- Set each column to the header your file uses.
- Remove the NAV check if your file has no NAV column, and add a 'non_negative' check on the weight column if your portfolios are long-only.
- Set the weight 'tolerance' to how your weights are rounded; "0.0001" allows one basis point.

**Assumptions:**

- Each row is one position of one portfolio, and every position, including cash and liabilities, is a row.
- A security appears once per portfolio; several lots of one security are combined before this check.
- Weights are fractions of the portfolio's NAV (0.25, not 25).
- Market values and NAV are in each portfolio's base currency, and liabilities and short positions have negative market values.
- The NAV is given on every row, or on at least one row, of each portfolio.

### B5. nav-reconciliation

**Holdings add up to the NAV**. Holdings of several funds, each line with a market value and the fund's NAV.

Create with `finassert init --template nav-reconciliation --output policy.yml`.

Included checks: `nav_reconciles`.

**Adapt before use:**

- Set each column to the header your file uses.
- Set the 'tolerance' in currency units; "0.01" allows one cent.

**Assumptions:**

- Every asset, liability, accrual, and cash balance is a line in the file.
- Liabilities and short positions have negative market values.
- Market values and the NAV are in each fund's base currency.
- The NAV is given on every line, or on at least one line, of each fund.

### B6. position-rollforward

**Position quantity roll-forward**. One row per portfolio and security: opening and closing quantities and trades.

Create with `finassert init --template position-rollforward --output policy.yml`.

Included checks: `required_fields`, `no_duplicates`, `position_rolls_forward`.

**Adapt before use:**

- Set each column to the header your file uses.
- Set 'sell_sign' to how your file records quantities sold: 'positive' if sells are positive numbers, 'negative' if they are negative.
- Add an 'adjustments' column for splits, transfers, or corporate actions if your file has them; without it they show up as breaks.
- Set the 'tolerance' in units of the security if quantities are fractional.

**Assumptions:**

- Each row is one position of one portfolio over one period, and the buys and sells are the totals for that period.
- Opening and closing quantities are as of the start and end of the same period as the trades.
- Splits, transfers, and corporate actions are in the adjustments column, or the file has none.
- Quantities are in units of the security, not market value.

### B7. position-valuation

**Position market values**. One row per position with quantity, price, and market value.

Create with `finassert init --template position-valuation --output policy.yml`.

Included checks: `required_fields`, `market_value_reconciles`.

**Adapt before use:**

- Set each column to the header your file uses.
- Add the 'multiplier' column if your file holds futures or options, and set 'row_key' to a column such as the ticker so the report names each position.
- Set the 'tolerance' in the market value's units; "0.01" allows one cent.

**Assumptions:**

- Each row is one position, with shorts as negative quantities.
- Prices are quoted per unit, not per 100 of par or as a percentage.
- Price and market value are in the same currency.
- The market value excludes accrued interest, or the price includes it.

### B8. return-reconciliation

**Reported returns**. One row per portfolio and period with beginning and ending values and a return.

Create with `finassert init --template return-reconciliation --output policy.yml`.

Included checks: `simple_return_reconciles`.

**Adapt before use:**

- Set each column to the header your file uses.
- Set 'return_unit' to 'percent' if a 5% return is written as 5 rather than 0.05.
- Add a 'net_flows' column if money moved in or out during the period, and read the assumptions: flows are treated as happening at the end of the period.
- Set the 'tolerance' in the return's unit; "0.0001" allows one basis point when returns are fractions.

**Assumptions:**

- Each row is one portfolio and one period.
- The return is simple (not time-weighted or Modified Dietz), so flows are assumed to happen at the end of the period.
- The return is gross of any fees the values do not already reflect.
- Values are in one currency per row.

### B9. target-allocation

**Target (model) allocation**. A model portfolio or strategic asset allocation, before it is traded.

Create with `finassert init --template target-allocation --output policy.yml`.

Included checks: `weights_sum_to_one`, `non_negative`.

**Adapt before use:**

- Set 'column' to the header holding the target weights.
- Set the 'tolerance' to how the targets are rounded; "0.0001" allows one basis point.

**Assumptions:**

- The file holds the targets of exactly one model or mandate.
- Targets are fractions of the whole (0.25, not 25).
- The model is long-only: no target is negative.

### B10. treasury-cash-forecast

**Weekly cash forecast**. Treasury cash/funding pack v1: coverage, identity, continuity and available cash.

Create with `finassert init --template treasury-cash-forecast --output policy.yml`.

Included checks: `required_fields`, `no_duplicates`, `no_duplicates`, `forecast_coverage`, `non_negative`, `non_negative`, `non_negative`, `non_negative`, `non_negative`, `non_negative`, `cash_reconciles`, `cash_continuity`, `minimum_cash_buffer`.

**Adapt before use:**

- Replace synthetic expected_scope and first_period using independent approved scope.
- Map physical column names, row identity and explicit currency; review the weekly horizon.
- Supply approved minimum/commitment columns and review zero amount tolerance.
- Prepare total flows explicitly; do not double-count financing or restricted cash.
- Check every required rule ran; skipped/error/absent checks mean incomplete coverage.

**Assumptions:**

- Synthetic scope and dates are placeholders requiring review.
- One complete unique row per weekly series/currency, with exclusive week end.
- Amounts in currency major units; no conversion or intercompany netting.
- Payments/repayments are positive magnitudes; financing is separate from operations.
- total_inflows = receipts + financing_inflows; total_outflows = payments + financing_outflows.
- Minimum buffers and effective commitment/reductions are caller supplied, not recommendations.
- Facility checks cover period ends; legal eligibility and intraperiod peaks are outside scope.

### B11. treasury-facility-schedule

**Weekly facility schedule**. Treasury cash/funding pack v1: principal, capacity and maturity.

Create with `finassert init --template treasury-facility-schedule --output policy.yml`.

Included checks: `required_fields`, `no_duplicates`, `no_duplicates`, `forecast_coverage`, `facility_capacity`.

**Adapt before use:**

- Replace synthetic expected_scope and first_period using independent approved scope.
- Map physical column names, row identity and explicit currency; review the weekly horizon.
- Supply approved minimum/commitment columns and review zero amount tolerance.
- Prepare total flows explicitly; do not double-count financing or restricted cash.
- Check every required rule ran; skipped/error/absent checks mean incomplete coverage.

**Assumptions:**

- Synthetic scope and dates are placeholders requiring review.
- One complete unique row per weekly series/currency, with exclusive week end.
- Amounts in currency major units; no conversion or intercompany netting.
- Payments/repayments are positive magnitudes; financing is separate from operations.
- total_inflows = receipts + financing_inflows; total_outflows = payments + financing_outflows.
- Minimum buffers and effective commitment/reductions are caller supplied, not recommendations.
- Facility checks cover period ends; legal eligibility and intraperiod peaks are outside scope.

<!-- finassert-generated-reference:end -->
