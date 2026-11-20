# 0019 - User guide: handoff

## Current state

- **Status:** Implemented (initial); local guide delivery verified.
- **Branch:** feature/excel-e06-mac-acceptance; existing changes are uncommitted.
- **Scope:** Comprehensive offline PDF, local metadata/download API and pane link.
- **Next step:** Return to E-06 under the master ordering; rebuild/review this
  guide whenever its source, catalog, version or renderer changes.

## Entries

### 2026-11-20 — Track PDF assets as binary

Added the repository PDF binary attribute after Git guessed the generated asset
was text during staged whitespace checking. The reviewed PDF bytes, API hashes,
source/catalog identities and runtime behavior are unchanged. Staged whitespace,
checkpoint and strict docs checks pass. The feature commit is ad2a173; this
follow-up is part of the user-authorized push. Master priorities remain unchanged.

### 2026-11-20 — Refresh the guide for clear failure-action wording

Added the human-facing failure-action terminology without changing canonical
severity or outcomes. Rebuilt the 47-page PDF/sidecar, reviewed every rendered
page, verified all 105 outline destinations and exact trusted HTTPS downloads.
Full 3,743 runtime/111 browser tests include the actual guide examples and pane
PDF download. The current [verification record](artifacts/verification.json)
identifies the refreshed source/PDF. The earlier 60-page draft is preserved locally
in ignored output/pdf/; docs/assets contains one canonical guide and its sidecar.
The user authorized committing/pushing all current-branch changes; E-06 remains next.

### 2026-11-20 - Deliver and verify the comprehensive PDF/API guide

- **Done:** Authored the comprehensive guide and complete generated catalog;
  built/reviewed the deterministic 47-page PDF; added validated build copies,
  GET/HEAD metadata/download routes and an explicit Excel pane link.
- **Evidence:** [Verification record](artifacts/verification.json) identifies the
  exact PDF/source and records all 47 rendered pages, 105 outline destinations,
  zero clipped/replacement glyphs and byte-identical rebuild/live downloads.
  The six Python examples and CLI workflow execute. Full 3,742 runtime and 111
  browser cases pass, alongside 31 focused unit/API cases and the final actual
  download rerun, smoke/scale, lint/format/mypy, strict docs/links and distributions.
- **Running state:** Existing trusted HTTPS localhost:3002 serves the current
  bundled build. GET /api/finassert/v1/user-guide.pdf downloads the attachment;
  GET /api/finassert/v1/user-guide returns its identity metadata. Both HEAD routes
  work. The final downloaded copy is also in ignored output/pdf/ for delivery.
- **Limits:** Native pane-link clicking was not separately observed. Full E-06,
  other hosts, remote hosting and tagged-PDF certification remain open/deferred.
  No workbook content, financial semantics or private-reader boundary changed.
  Existing changes remain uncommitted; no staging, commit, push or CI performed.
- **Pickup:** Keep source/catalog/PDF identities aligned and retain rendered QA
  for updates. Resume E-06, then 0012 U-08 and U-09 under the master ordering.

### 2026-11-20 - Scope the comprehensive guide and local download API

- **Done:** Audited current master/catalog, interface specs, docs, catalog and
  native acceptance. Chose the existing local HTTPS origin and a build-time PDF.
- **Limits:** Implementation/verification remain open. No remote deployment,
  changed financial contract, full Mac acceptance, commit or push is claimed.
- **Pickup:** Complete this user-requested guide, then return to E-06 under
  the master priority ordering.
