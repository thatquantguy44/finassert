# Grouped validation design

This design records the dataframe-contract exploration completed before a public
cash-reconciliation rule. The prototype lives in the private
`finassert.rules._cash_reconciliation` module and is not supported API.

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

## Proposed cash-rule API

The rule factory remains proposed, while its grouped mapping contract is settled:

```python
rule = fa.cash_reconciles(
    mapping=mapping,
    tolerance=fa.Tolerance(absolute="0.01"),
    null_policy="fail",
    empty_policy="skip",
    max_violations=20,
)
```

Before export, `absolute` string coercion, a currency grouping precondition, and
whether production rules require an explicit ordering column must be specified.
The private prototype must not be imported by applications.

## Promotion criteria

A public cash rule requires:

- an explicit sign convention;
- a decision on requiring an ordering column for first/last aggregation;
- currency and valuation-date preconditions;
- stable null and empty-population policies;
- contract parity across mapping, row-record, and pandas inputs;
- bounded, JSON-compatible group diagnostics; and
- property tests for partitioning and reconciliation identities.
