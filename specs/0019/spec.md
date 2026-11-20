# 0019 - Comprehensive user guide and PDF download API

**Status:** Implemented (initial); verified local PDF/API delivery.
**Updated:** 2026-11-20

## Problem statement

Operators and developers need one complete guide they can read offline, share,
and retrieve through the existing local API without assembling scattered pages.

## Goals

Deliver a searchable, navigable PDF with installation, Excel/browser/Python/CLI
workflows, policy authoring, numeric/input contracts, all built-in rules and
starter templates, units/FX, treasury, reports, MCP, troubleshooting, a demo and
operating guidance. Keep the source in docs/user-guide.md and register it in MkDocs.
Generate the catalog appendix from the current allowlist. Preserve explicit
initial support and deferred boundaries.

## Non-goals

A hosted validation service, workbook uploads, authentication rollout, remote
publication, new financial rules, changed pass/fail semantics and completion of
0016 host acceptance are outside this work.

## Architecture

A build-only ReportLab renderer creates a prebuilt PDF and identity sidecar.
The Excel builder validates/copies them into its static directory. The existing
local HTTPS server serves fixed read-only guide routes. The Excel pane offers
an explicit download link, without reading cells or changing the browser app's
offline behavior. No PDF-generation dependency enters the core import path.

## Public API design

- GET /api/finassert/v1/user-guide: JSON metadata with schema_version, title,
  tool name/version, guide revision, filename, byte count, SHA-256 and download URL.
- GET /api/finassert/v1/user-guide.pdf: the matching PDF, application/pdf,
  Content-Disposition attachment with a fixed filename, Content-Length,
  X-Content-Type-Options nosniff and Cache-Control no-store.
- HEAD supports both routes with identical status/headers and no body.
- Routes use the server's current origin and port; this does not establish a
  hosted or public internet API. No path, Git ref or workbook content is accepted.

## Data contracts

One reviewed Markdown source and generated catalog appendix own the prose.
The sidecar records its content hash, catalog hash, renderer source hash, tool
version and PDF identity.
The build must reject missing or stale guide assets with an actionable rebuild
message. Downloads are the exact validated asset bytes, not regenerated per request.
The checked PDF includes a cover, clickable contents/bookmarks, page numbers,
readable code/tables and source/reference links. Package source distributions
carry the source, builder and prebuilt assets; core wheel dependency isolation stays intact.

## Financial and numerical edge cases

Explain outcome versus freshness, severity versus evaluation errors, skips and
empty-rule caveats, Decimal/float behavior, tolerance units, null policies, grouping,
row identity, dates, percentages, currency/sign contracts and incomplete evidence.
Examples use synthetic data and explicit assumptions; no regulatory thresholds
or unsupported capabilities are presented as supplied controls.

## Failure semantics

Missing assets return 404. Invalid or mismatched PDF/metadata return 503, never a
successful HTML error masquerading as a PDF. Unknown guide routes return 404.
These errors cannot modify workbook data, policy, financial results or private
QuantSmith reader configuration. The PDF remains usable offline after download.

## Implementation milestones

See [plan.md](plan.md), [tasks.md](tasks.md) and [roadmap.md](roadmap.md).

## Acceptance criteria

1. All documented current interfaces and every built-in catalog rule/template
   appear with assumptions, settings and boundaries; documented examples execute.
2. PDF text is searchable, contents links/bookmarks work, and rendered pages show
   no clipped/overlapping text or unreadable tables/code.
3. The built add-in contains matching PDF/metadata; GET/HEAD, MIME, filename,
   byte identity, missing/stale assets and invalid routes have automated coverage.
4. The running local HTTPS API downloads the verified PDF and the pane exposes
   its explicit link. Neither action reads cells or requires the private reader.
5. Relevant runtime/browser checks, strict docs/links and package verification pass;
   local/master handoffs record actual evidence and remaining host acceptance.

## Dependencies on other specifications

[0011](../0011/spec.md) owns user interfaces; [0016](../0016/spec.md) owns live
Excel behavior/support; [0018](../0018/spec.md) owns the separate private reader.
Existing rule, artifact, loader, policy and unit specifications remain normative.

## Explicit deferred work

Remote hosting, translations, tagged-PDF accessibility certification, videos,
new runtime financial APIs and additional real-host platform acceptance.
