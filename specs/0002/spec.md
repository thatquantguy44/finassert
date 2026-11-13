# 0002 — Financial invariants

**Status:** Milestones 1–2 implemented (initial): weight-sum and nonnegative
rules, and grouped cash (`accounting.cash_reconciles`) and NAV
(`accounting.nav_reconciles`) reconciliation. Cash requires an explicit
`outflow_sign`; NAV sums signed lines, so assets minus liabilities is
`sum(market_value)` with liabilities negative. Currencies are never converted;
a currency column becomes a group key. `weights_sum_to_one` can check each
portfolio with `group_by`. Milestone 3 is implemented (initial):
`accounting.market_value_reconciles` (quantity × price × optional multiplier),
`returns.simple_return_reconciles` (explicit `fraction` or `percent`; flows at
the end of the period), and `exposure.gross_within_limit`,
`exposure.net_within_limit`, and `exposure.position_within_limit`, which
measure per group against an optional base column such as the NAV. Limits are
inclusive and supplied by the user: no template encodes one. Portfolio-management rules follow:
`arithmetic.in_range`, `portfolio.weights_match_market_values`,
`portfolio.drift_within_band` (default severity `warning`),
`portfolio.turnover_within_limit` (explicit `one_way` or `two_way`), and
`accounting.position_rolls_forward` (explicit sell sign). Collateral and
financing rules remain proposed.

## Problem statement

A catalog must encode equations plus domain assumptions without presenting
institution-specific conventions as universal financial truth.

## Motivation and use cases

Portfolio construction, accounting, performance, collateral, risk, and securities
financing all produce plausible data that may violate economic identities.

## Goals

Define names, inputs, equations, units, null behavior, tolerances, diagnostics, and
applicability statements for every built-in rule.

## Non-goals

The catalog does not prescribe investment policy, prohibit short positions, infer
currencies, fetch market data, or replace accounting control ownership.

## Proposed architecture

Rule families are `portfolio`, `accounting`, `returns`, `collateral`, `exposure`,
and `securities_financing`, plus `arithmetic` for single-column value checks and
`data` for file-shape checks (`data.no_duplicates`, `data.required_fields`) that
hold for any file. Each rule is immutable configuration plus pure
evaluation. Stable IDs use `family.rule_name`.

Catalog candidates include weight totals; cash opening + flows + P&L = closing;
assets - liabilities = NAV; price × quantity × multiplier = market value; return
denominator consistency; haircut-adjusted collateral; eligibility predicates;
gross/net exposure limits; and loan + collateral + fee balance reconciliation.

## Public API design

Factories use finance-language parameters, for example
`weights_sum_to_one(column, tolerance, null_policy)`. Future reconciliation rules
must require explicit left/right component mappings, signs, and grouping keys.

## Data contracts

Inputs name columns rather than assume schemas. Results include aggregate observed
and expected values plus bounded row/group violations. Metadata records grouping,
units, sign convention, and truncation.

## Financial and numerical edge cases

Short weights are valid; liabilities may be stored positive or negative; prices
and quantities may reflect multipliers; zero denominators need policy; stale FX
must not be inferred; corporate actions can break naïve position continuity.

## Failure semantics

Policy violations fail. Missing required columns or incompatible units error.
Optional checks may skip only for a documented precondition. Missing observations
follow an explicit rule configuration.

## Implementation milestones

1. Weight sum and explicit nonnegative rule. 2. Cash and NAV reconciliation with
sign contracts. 3. Returns and exposure rules. 4. Collateral and financing rules.

## Acceptance criteria

Every rule states equation, applicability, counterexamples, required units,
tolerance basis, empty/null behavior, and diagnostic cap before export.

## Testing requirements

Use synthetic passing/failing examples, exact boundaries, Decimal inputs, nulls,
empty groups, non-finite values, sign variants, and property identities.

## Dependencies on other specifications

Requires 0001, 0003, and 0004; currency-aware rules require 0008; diagnostics use
0005 and property suites use 0009.

## Explicit deferred work

VaR model validation, regulatory interpretation, solver feasibility, live prices,
FX acquisition, and institution-specific eligibility policy are deferred.
