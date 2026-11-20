# 0018 — Plan

Use the current `serve_excel.py` origin for a local-default reference API.
Index regular Git blobs from the locked local commit with `git ls-tree`; support
an explicit GitHub Git-object source at the same pinned commit, with bounded
responses and opaque IDs. Do not place private content in `build_web.py` output.
Add a simple Excel-pane reader that fetches on click and writes raw text through
`textContent`.

Verification: synthetic local and GitHub source/API tests, a bundled-pane browser test,
the existing server/build tests, full runtime and browser regressions, lint,
format, type checking, strict docs and the existing Excel smoke flows. The
native 0016 E-06 gate and this panel's Mac check remain separate.
