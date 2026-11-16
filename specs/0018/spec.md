# 0018 — Pinned QuantSmith reference in Excel

**Status:** Implemented initial local reader; real Excel host acceptance pending.
**Owner:** finassert. QuantSmith remains a separate private repository.

## Purpose

Let a finassert Excel add-in user browse QuantSmith agent files and selected
documentation as reference text. The private source must stay outside the public
add-in bundle. The reader must identify the exact source revision.

## Requirements

- **R-01 — Pin and scope.** A versioned lockfile names the QuantSmith repository,
  a full commit SHA and permitted document patterns. A local server must verify
  its checkout origin and the commit before serving anything. Only regular UTF-8
  Git blobs matching the allowlist and size bounds may be listed or read.
- **R-02 — Local read API.** The existing Excel static server may opt in to
  `GET /api/quantsmith/v1/docs` and `GET /api/quantsmith/v1/docs/{id}`.
  An opaque catalog ID, not a caller path, selects content. Responses include
  source path, pinned commit and content digest. No write, Git fetch, model
  execution or document execution is provided.
- **R-03 — Excel reader.** The add-in displays a searchable catalog and raw
  document text on explicit user request. It sends no workbook cells or policy
  to the reference API. Missing service has a clear message and leaves
  validation usable.
- **R-04 — Private local boundary.** Reference mode binds only to loopback and
  rejects cross-origin requests. The static add-in and wheel/sdist contain no
  private QuantSmith document text or credentials. Remote multiuser hosting is
  outside this initial slice.

## Acceptance

- **AC-01:** A synthetic Git checkout with the expected origin/commit lists
  only allowed regular blobs; symlinks, wrong origin, missing commit and arbitrary
  IDs cannot disclose content. Working-tree edits do not alter pinned reads.
- **AC-02:** The local API returns a catalog and document with commit/digest,
  rejects cross-origin reads and is absent when not configured.
- **AC-03:** The built Excel pane makes no reference request until selected,
  searches and reads a document, and renders markup as inert text.
- **AC-04:** Existing Excel/browser validation and local smoke checks pass after
  the optional reader is added. Native Mac behavior is recorded separately.

## Boundaries

QuantSmith agent prompts and instructions are shown as reference data, not
adopted as finassert instructions or executed. The existing 0016 workbook
capture, financial results and E-06 acceptance contract are unchanged.
Only the localhost owner may opt in to private content. A future hosted service
requires authenticated user authorization and its own delivery review.
