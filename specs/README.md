# finassert specifications

Specifications describe contracts before broad implementation. Status labels are
normative: **Implemented (initial)** means the current release supplies the small
contract described; **Proposed** means no public capability should be inferred.

| Specification | Status |
|---|---|
| [0001 Core validation engine](0001-core-validation-engine.md) | Implemented (initial) |
| [0002 Financial invariants](0002-financial-invariants.md) | Milestones 1–2 implemented (initial) |
| [0003 Numerical tolerances](0003-numerical-tolerances.md) | Implemented (initial) |
| [0004 DataFrame adapters](0004-dataframe-adapters.md) | pandas initial; ordering decided; Polars proposed |
| [0005 Reporting and diagnostics](0005-reporting-and-diagnostics.md) | Text/JSON/HTML initial |
| [0006 Rule registry and custom rules](0006-rule-registry-and-custom-rules.md) | Implemented (initial) |
| [0007 CLI and pipeline integration](0007-cli-and-pipeline-integration.md) | Implemented (initial) |
| [0008 Financial units and currencies](0008-financial-units-and-currencies.md) | Proposed |
| [0009 Property-based testing](0009-property-based-testing.md) | Implemented (initial) |
| [0010 Performance and batch validation](0010-performance-and-batch-validation.md) | Proposed |
| [0011 Non-technical interfaces](0011-non-technical-interfaces.md) | Milestones 1–6 implemented (initial); Excel files supported |
| [0012 Treasury and capital markets](0012-treasury-capital-markets/SPEC.md) | Proposed; upstream rules and deferred QuantMeridian handoff |

Changes to outcomes, rule identity, tolerance mathematics, serialization, or
adapter row identity require a specification amendment and migration note.
