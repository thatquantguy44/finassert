# Grouped validation design

This design records the dataframe-contract exploration behind the public
reconciliation rules, `cash_reconciles` and `nav_reconciles`
(`finassert.rules.accounting`). The private prototype it describes has been
promoted and removed; the findings below are kept as the rationale.

## Decisions

`ColumnMapping` is the public boundary between a rule's semantic inputs and a
dataset's physical columns. It takes an immutable copy of the supplied mapping.
`GroupKey` pairs a stable diagnostic name with a physical column. Group-key order
is significant and controls deterministic grouping and serialized output.

Aggregation policy belongs in `ColumnMapping`, beside the semantic field it
describes. This keeps schema, grouping, row identity, and reduction behavior in
one immutable configuration while leaving financial equations in the rule. There
is no implicit aggregation for grouped fields.

```python
from finassert.adapters import ColumnMapping, FieldAggregation, GroupKey

mapping = ColumnMapping(
    columns={
        "opening_cash": "cash_open",
        "inflows": "subscriptions",
        "outflows": "redemptions",
        "cash_pnl": "cash_pnl",
        "closing_cash": "cash_close",
    },
    group_keys=(
        GroupKey("portfolio", "portfolio_id"),
        GroupKey("currency", "currency_code"),
        GroupKey("as_of_date", "valuation_date"),
    ),
    row_key="reconciliation_record_id",
    aggregations={
        "opening_cash": FieldAggregation.FIRST,
        "inflows": FieldAggregation.SUM,
        "outflows": FieldAggregation.SUM,
        "cash_pnl": FieldAggregation.SUM,
        "closing_cash": FieldAggregation.LAST,
    },
)
```

The optional `row_key` is a physical column used in row diagnostics. Without it,
pandas retains its index and dependency-free inputs use positional labels.
Duplicate labels are valid and are never described as unique identifiers.

Multi-column evaluation validates alignment before applying a rule. Adapters must
not coerce dtypes, fill nulls, reorder observations, reset indexes, or modify the
input object. pandas nullable values are treated as missing, and Decimal object
columns retain Decimal arithmetic.

`SUM` uses Decimal-preserving summation. `FIRST` and `LAST` use physical adapter
order and never sort data. `REQUIRE_UNIQUE` permits repeated equal values and
fails a group when distinct values occur. Its comparison is exact because it
validates data shape; financial materiality tolerance remains a rule concern.

`finassert.GroupedRule` extends the ordinary structural `Rule` contract with a
`mapping` and ordered `required_semantics`. The engine does not special-case
grouped rules: they still evaluate once and return one `ValidationResult` with
bounded group diagnostics.

## Prototype findings

The private cash rule checks each ordered group after field-specific aggregation:

```text
aggregate(opening cash) + sum(inflows) - sum(outflows) + sum(cash P&L)
    = aggregate(closing cash)
```

One result per configured rule remains workable when metadata contains the total
group count, failed-group count, bounded failed-group details, and a truncation
flag. A missing group key prevents reliable partitioning and is an evaluation
error. A missing or non-finite financial input is a validation failure with row
context. Failure of `REQUIRE_UNIQUE` is a group-level validation failure. An empty
dataset is skipped in the prototype because no reconciliation population exists.

Currency cannot be inferred safely. A production rule must require currency as a
group key when mixed currencies are possible, or require an explicit conversion
policy with provenance. It must never aggregate currencies silently.

Input grain is explicit through aggregation policy. Transaction-oriented data
normally uses `FIRST` opening balance, `SUM` flows, and `LAST` closing balance.
Snapshot-oriented data can use `REQUIRE_UNIQUE` for repeated balances. Because
adapters do not reorder data, callers using `FIRST` or `LAST` are responsible for
providing financially meaningful row order.

## Public cash and NAV rules

The promotion criteria were settled as follows.

- **Sign convention.** `outflow_sign` is required, with no default: `positive`
  checks `closing = opening + inflows - outflows (+ cash_pnl)`, `negative`
  checks `closing = opening + inflows + outflows (+ cash_pnl)`. Each result
  records the equation it checked. NAV uses signed lines,
  `sum(market_value) = nav`, so liabilities and short positions are negative
  rows rather than a separately signed column.
- **Ordering for first/last (specification 0004, milestone 5).** Public rules
  require `ColumnMapping.order_key` whenever `FIRST` or `LAST` is configured;
  physical row order is never treated as a financial ordering.
  `aggregate_ordered` takes the row with the smallest or largest key. Ordering
  values must be numbers, dates, or ISO 8601 text, because text such as
  `1/10/2026` sorts before `1/9/2026`. Rows that tie on the extreme key with
  different values, keys that mix numbers and dates, and keys that mix
  time-zone-aware and naive times fail the group. `aggregate_values` keeps its
  documented physical-order behavior for low-level callers.
- **Input grain.** The column-name factory offers `grain="summary"` (one row
  per group; every field `REQUIRE_UNIQUE`, so conflicting repeated rows fail)
  and `grain="transactions"` (running balances: `FIRST` opening, `LAST`
  closing, `SUM` flows, ordered by `order_by`). A complete `ColumnMapping` can
  be passed instead for any other configuration.
- **Currency and valuation date.** Currencies are never converted. Naming the
  `currency` column adds it as a group key; when omitted, the result records
  that every group is assumed to hold one currency. Dates are ordinary
  `group_by` columns.
- **Nulls and empty files.** `null_policy` is `fail` (unusable rows are listed
  in file order with the blank or non-numeric fields) or `skip`; `ignore` is
  rejected because leaving out rows changes the totals. A blank NAV on some
  rows is allowed, as long as each group gives at least one and they agree. A
  blank group key is an evaluation error. A file with no rows is skipped.
- **String tolerances.** The Python API takes numbers or `Decimal`; quoted text
  becomes `Decimal` in the policy layer only.
- **Parity, diagnostics, and properties.** Mapping, row-record, and pandas
  inputs give identical results. Failed groups are capped by `max_violations`
  and list the group identity, observed and expected values, the difference,
  and up to 20 row labels. Hypothesis tests cover reconciliation under row
  shuffling and the isolation of a single broken group.
