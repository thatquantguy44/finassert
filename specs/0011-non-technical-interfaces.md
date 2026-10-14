# 0011 — Non-technical interfaces

**Status:** Milestones 1–6 implemented (initial): catalog metadata, policy
diagnostics, the HTML renderer and `--html` flag, the Pyodide browser
application, starter policy templates, and the assistant tool server
(`finassert-assistant`, shipped as the `assistant` extra rather than a separate
distribution). Spreadsheet *files* are also supported: Excel `.xlsx` is read
without a dependency in both the CLI and the browser. Integration inside Excel
itself (milestone 7) remains proposed; the market survey, options, and a
recommended Office-add-in design with a spike plan are in
`docs/design/excel-integration.md`. Column matching (`finassert suggest`, the
browser app, and the assistant) proposes which header plays which template
column; it explains each match and never applies one silently.

## Problem statement

Validation is reachable only through Python. Fund accountants, operations
analysts, compliance reviewers, and portfolio managers who own the data, and who
work mainly in spreadsheets and file exports, cannot author, run, or read checks
without an engineer.

## Motivation and use cases

An operations analyst validates a daily position export before sign-off; a
compliance reviewer attaches a readable report to a control record; a portfolio
manager confirms a model allocation before submission; an analyst drafts a check
interactively and hands the identical policy to engineering for pipeline gating.

## Goals

Specify a plain-language rule catalog, human-oriented policy diagnostics, a
self-contained HTML report, a local-only browser application, a spreadsheet
integration path, and an assistant tool interface. Every surface executes the
0007 policy format through the ordinary engine and produces 0005 results.

## Non-goals

Hosted services, data upload to any server, user accounts, scheduling, alert
delivery, rule authoring in arbitrary code from a UI, natural-language rule
generation without a reviewable policy, and institution-specific compliance
regimes are excluded.

## Proposed architecture

Three layers. The core engine stays dependency-free and unchanged. A shared
`policy` layer (0007) parses, validates, and resolves policies through a
caller-selected registry and exposes catalog metadata. Interfaces are separate
distributions or optional extras that consume only the policy layer and 0005
results: `finassert[cli]` with an HTML renderer, `finassert-web` (static page
running the engine under Pyodide), a spreadsheet integration, and
`finassert-mcp` (assistant tool server). No interface may evaluate rules
through a path other than `check`.

## Public API design

```python
from finassert.policy import default_catalog, load_policy, PolicyError
from finassert.reporting import to_html

catalog = default_catalog()  # caller-owned allowlist
entry = catalog.resolve("portfolio.weights_sum_to_one")  # name or rule ID
entry.summary, entry.rationale, entry.inappropriate_when, entry.parameters

policy = load_policy("policy.yml")  # 0007
# PolicyError.issues -> PolicyIssue(location, line, message, suggestion)
to_html(report, policy=policy)  # pure view over the 0005 artifact
```

```text
finassert check --config policy.yml --input positions.xlsx --html report.html
```

Column mapping by header text (`column: "Mkt Val (USD)"`) is part of the policy
schema, never inferred.

## Data contracts

Catalog entries carry rule ID, version, one-sentence summary, financial
rationale, inappropriate uses, and typed parameter descriptions with defaults and
units; built-in rules must supply all fields to ship. Policy templates are
ordinary versioned policies with a mandatory `assumptions` list. The HTML report
is one file with no network requests, embeds the 0005 payload, policy digest,
tool version, and UTC timestamp, and caps displayed rows per 0005 limits.
Interfaces that edit policies must round-trip them: export, reload, and identical
results.

## Financial and numerical edge cases

UI numeric inputs are captured as strings and parsed as Decimal to preserve
tolerance intent; spreadsheet cells may hold display-rounded values, formulas,
dates as serial numbers, or percentages stored as 0.4 or 40, so loaders report
the cell type read and never rescale. Thousands separators and locale decimal
commas are rejected unless the policy declares a locale. Templates must not
encode a regulatory limit as a default.

## Failure semantics

Plain-language messages never replace outcomes: failures, errors, and skips keep
distinct visual treatment, and an error is never shown as a pass. Policy problems
name the line and key and suggest the nearest valid identifier, but are never
auto-corrected. The browser application makes zero network requests after load;
a failed load or Pyodide error is shown as an evaluation error, not an empty
report. Reports omit full records beyond capped diagnostics.

## Implementation milestones

1. Catalog metadata for existing rules and `default_catalog()`. 2. Human policy
diagnostics in the 0007 loader. 3. Self-contained HTML renderer and CLI flag.
4. Pyodide browser application with policy export. 5. Starter policy templates.
6. Assistant tool server. 7. Spreadsheet integration. The recommended design bundles the engine inside the
add-in, so it does not depend on PyPI publication.

## Acceptance criteria

A reviewer without Python can, using only documentation, validate a CSV in the
browser, export the policy, and obtain identical results from the CLI; the HTML
report opens offline and passes automated accessibility checks; no interface
adds a dependency to the core import path.

## Testing requirements

Catalog completeness for every registered built-in; misspelled rules, keys, and
columns; UI-to-CLI policy round-trip equality; HTML snapshot, escaping of
untrusted cell text, and no external references; browser network-request audit;
spreadsheet type and percentage edge cases; mixed outcomes and empty rule sets.

## Dependencies on other specifications

Requires 0005 and 0007; uses 0006 for catalog resolution, 0004 for spreadsheet
and dataframe input, and 0008 for unit labels in parameter descriptions.

## Explicit deferred work

Hosted or multi-user deployment, an Office add-in beyond the first spreadsheet
path, policy collaboration and approval workflows, localization of messages,
visual rule builders for grouped rules, and LLM-generated policies are deferred.
