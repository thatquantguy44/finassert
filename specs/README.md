# finassert specifications

Specifications describe contracts before broad implementation. Status labels are
normative: **Implemented (initial)** means the current release supplies the small
contract described; **Proposed** means no public capability should be inferred.

## Required workspace structure

Each spec has a directory named with its permanent four-digit number. Keep the
title in the documents and catalog; do not put new specs in flat Markdown files.

```text
specs/
  0001/
    spec.md
    plan.md
    tasks.md
    roadmap.md
    AGENTS.md
    contracts.md
    handoff.md
```

| File | Responsibility |
|---|---|
| `spec.md` | Canonical requirements, scope, API, semantics, and acceptance criteria. |
| `plan.md` | Implementation approach, dependencies, affected areas, and verification. |
| `tasks.md` | Ordered actionable checklist with evidence for completed work. |
| `roadmap.md` | Current, next, later, and deferred milestones for this spec. |
| `AGENTS.md` | Instructions and constraints for agents working on this spec. |
| `contracts.md` | Contract references, review constraints, and compatibility notes. |
| `handoff.md` | Current state, blockers, next action, and append-only session entries. |

Read `AGENTS.md`, `spec.md`, `contracts.md`, `tasks.md`, and the newest handoff
before starting related implementation work. Keep requirements in `spec.md` and
link to them from companion files. Add `decisions.md`, `research.md`, or an
`artifacts/` directory when the work needs them; the seven files above are always
required. Do not imply that scaffolding means implementation is complete.

## Creating a spec

Copy [_template/](_template/spec.md) to the next unused numbered directory
(currently `0016`). Replace the template prompts, set an explicit status, and add
the spec to the catalog below. Numbers are permanent and are not reused. Keep
draft planning and unresolved questions explicit instead of inventing completion.

At session end, update the local tasks and handoff. Record project-wide decisions,
cross-spec dependencies, and overall priorities in the
[master handoff](../docs/handoff.md) and [project roadmap](../docs/roadmap.md).

## Catalog

| Specification | Status |
|---|---|
| [0001 Core validation engine](0001/spec.md) | Implemented (initial) |
| [0002 Financial invariants](0002/spec.md) | Milestones 1–2 implemented (initial) |
| [0003 Numerical tolerances](0003/spec.md) | Implemented (initial) |
| [0004 DataFrame adapters](0004/spec.md) | pandas initial; ordering decided; Polars proposed |
| [0005 Reporting and diagnostics](0005/spec.md) | Text/JSON/HTML initial |
| [0006 Rule registry and custom rules](0006/spec.md) | Implemented (initial) |
| [0007 CLI and pipeline integration](0007/spec.md) | Implemented (initial) |
| [0008 Financial units and currencies](0008/spec.md) | Money/ratio units, direct FX, and adapter integration implemented (initial) |
| [0009 Property-based testing](0009/spec.md) | Implemented (initial) |
| [0010 Performance and batch validation](0010/spec.md) | Scalar/multi-rule benchmarks, bounded diagnostics and private shared reads; batch APIs proposed |
| [0011 Non-technical interfaces](0011/spec.md) | Milestones 1–6 implemented (initial); Excel files supported |
| [0012 Treasury and capital markets](0012/spec.md) | Cash/funding pack implemented; later rules and consumer work proposed |

| [0013 Excel workbook files](0013/spec.md) | Reader, XLSX reports, and CLI extensions implemented (initial) |
| [0014 Seven-priority delivery](0014/spec.md) | Seven gates delivered; PR #17 merged |
| [0015 Verified upstream release bundles](0015/spec.md) | Implemented and locally verified; draft PR review pending |

Changes to outcomes, rule identity, tolerance mathematics, serialization, or
adapter row identity require a specification amendment and migration note.
