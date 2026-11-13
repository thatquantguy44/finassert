# 0014 — Seven-priority delivery: contracts

This workspace coordinates delivery and defines no independent runtime contract.
The [owning specs](spec.md#dependencies-on-other-specifications) define APIs,
numeric semantics, failure outcomes, row identity, and artifact compatibility.

Contract amendments require explicit migration notes in the owning workspace.
Passing, failing, errored, and skipped results stay distinct; missing or
unreadable input must never silently pass. Preserve Decimal arithmetic and
explicit currency/sign/ordering conventions through all integrations.
