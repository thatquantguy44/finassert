# 0018 — Contracts

[spec.md](spec.md) owns the requirements. The lockfile is
`integrations/quantsmith-docs.lock.json` (schema version 1): repository,
full commit SHA and document include patterns. The local server verifies its
checkout's origin and that commit. Catalog IDs are SHA-256 of source paths;
document reads use the blob SHA recorded at the pinned commit.

The optional API is same-origin and local only. Local is the default source and
reads the configured checkout; GitHub is an explicit local-server source that
uses the lock's exact commit and allowlisted Git objects. The catalog route
returns `repository`, `commit`, `source` and `documents`; the document route
adds `content` and its SHA-256. No filesystem path, Git ref or clearance is
accepted from an HTTP request. GitHub credentials are accepted only from the
local process environment. No QuantSmith content enters the finassert wheel or
built pane.

Parent [0011](../0011/spec.md) still owns the interface and [0016](../0016/spec.md)
still owns live workbook validation and Mac acceptance.
