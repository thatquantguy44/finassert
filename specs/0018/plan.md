# 0018 — Plan

Use the current `serve_excel.py` origin for an opt-in reference API. Index
regular Git blobs from the locked commit with `git ls-tree`; read by blob SHA,
with bounded content and opaque IDs. Do not place private content in
`build_web.py` output. Add a simple Excel-pane reader that fetches on click
and writes raw text through `textContent`.

Verification: synthetic checkout/API tests, a bundled-pane browser test,
the existing server/build tests, full runtime and browser regressions, lint,
format, type checking, strict docs and the existing Excel smoke flows. The
native 0016 E-06 gate and this panel's Mac check remain separate.
