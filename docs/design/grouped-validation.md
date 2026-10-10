# Grouped validation design

This design records the dataframe-contract exploration completed before a public
cash-reconciliation rule. The prototype lives in the private
`finassert.rules._cash_reconciliation` module and is not supported API.

## Decisions

`ColumnMapping` is the public boundary between a rule's semantic inputs and a
dataset's physical columns. It takes an immutable copy of the supplied mapping.
`GroupKey` pairs a stable diagnostic name with a physical column. Group-key order
is significant and controls deterministic grouping and serialized output.

```python
from finassert.adapters import ColumnMapping, GroupKey

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
)
```

The optional `row_key` is a physical column used in row diagnostics. Without it,
pandas retains its index and dependency-free inputs use positional labels.
Duplicate labels are valid and are never described as unique identifiers.

Multi-column evaluation validates alignment before applying a rule. Adapters must
not coerce dtypes, fill nulls, reorder observations, reset indexes, or modify the
input object. pandas nullable values are treated as missing, and Decimal object
columns retain Decimal arithmetic.

## Prototype findings

The private cash rule uses additive slices and checks each ordered group:

```text
sum(opening cash) + sum(inflows) - sum(outflows) + sum(cash P&L)
    = sum(closing cash)
```

One result per configured rule remains workable when metadata contains the total
group count, failed-group count, bounded failed-group details, and a truncation
flag. A missing group key prevents reliable partitioning and is an evaluation
error. A missing or non-finite financial input is a validation failure with row
context. An empty dataset is skipped in the prototype because no reconciliation
population exists.

Currency cannot be inferred safely. A production rule must require currency as a
group key when mixed currencies are possible, or require an explicit conversion
policy with provenance. It must never aggregate currencies silently.

The largest unresolved financial question is grain. Additive slices are simple
and composable, but many operational datasets repeat opening and closing balances
across transaction rows. A public rule must either require one balance row per
group or distinguish additive flow columns from non-additive balance columns.

## Proposed cash-rule API

The following remains proposed until the grain decision is resolved:

```python
rule = fa.cash_reconciles(
    mapping=mapping,
    tolerance=fa.Tolerance(absolute="0.01"),
    null_policy="fail",
    empty_policy="skip",
    max_violations=20,
)
```

Before export, `absolute` string coercion, balance-versus-flow aggregation, and a
currency grouping precondition must be specified. The private prototype must not
be imported by applications.

## Promotion criteria

A public cash rule requires:

- an explicit input-grain and sign convention;
- a decision on additive versus first/last balance aggregation;
- currency and valuation-date preconditions;
- stable null and empty-population policies;
- contract parity across mapping, row-record, and pandas inputs;
- bounded, JSON-compatible group diagnostics; and
- property tests for partitioning and reconciliation identities.
