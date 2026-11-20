# finassert

**Financial invariants, tested like code.**

`finassert` evaluates financial assumptions as deterministic, composable Python
rules. It distinguishes business failures from evaluation errors, preserves
Decimal arithmetic where practical, and never silently changes input data.

Start with [Getting started](getting-started.md), then read
[Architecture](architecture.md) before adding a rule.

The [comprehensive user guide](user-guide.md) covers all current interfaces,
rules and templates. [Download the PDF](assets/finassert-user-guide.pdf) for
offline use or retrieve it from the local add-in server through
`GET /api/finassert/v1/user-guide.pdf`.
