# 0019 - User guide: plan

## Approach

1. Audit implemented docs, catalog, templates, APIs and acceptance limits.
2. Write the task-based guide and generate the complete catalog appendix.
3. Build a deterministic PDF and identity sidecar; render and inspect all pages.
4. Copy verified assets into Excel builds; add GET/HEAD metadata/download routes
   and a discoverable pane link. Preserve the private reader and core isolation.
5. Verify examples, PDF structure/layout, endpoint failure/identity contracts,
   browser link behavior, strict docs and packages; restart the authorized local
   server and verify its actual HTTPS response.

## Affected areas

New docs/user-guide.md, docs/assets/finassert-user-guide.pdf plus JSON sidecar,
scripts/build_user_guide.py and a small standard-library asset helper. Existing
scripts/build_excel.py, scripts/serve_excel.py, web/excel-panel.html, MkDocs and
focused build/server/browser tests. No financial engine changes.

## Verification

Use the PDF skill's marker, ReportLab, Poppler PNG rendering and pypdf/pdfplumber
checks. Run focused tests and the full runtime suite with absolute PYTHONPATH and
socket access; the existing pinned Playwright browser suite and Excel smoke cover
the changed pane/build. Run lint/format, mypy, strict MkDocs, links/anchors, fresh
wheel/sdist and scripts/verify_dist.py. Exercise the live HTTPS GET/HEAD with the
existing trusted certificate; preserve all unrelated workbook and Git state.
