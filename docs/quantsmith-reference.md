# QuantSmith reference in the Excel add-in

The optional reference panel reads allowlisted Markdown and the agent registry
at the exact commit in `integrations/quantsmith-docs.lock.json`. It uses the
local QuantSmith checkout by default. An explicit GitHub mode is also available
when a local checkout is not suitable. The add-in bundle contains no QuantSmith
document content or GitHub credential.

## Set up a local reader

The default local checkout for this installation is:

```bash
/Users/joshualutkemuller/Documents/Quant Sandbox/agentic_workflows/qf_workflow_sdk_public
```

Build the Excel add-in using [the normal build instructions](excel-add-in.md),
then serve it over trusted localhost HTTPS. Local mode is the default and reads
the pinned Git objects from that checkout; uncommitted working-tree edits are
ignored.

```bash
python scripts/serve_excel.py --dir dist/excel --port 3000 \
  --cert localhost.pem --key localhost-key.pem
```

Set `FINASSERT_QUANTSMITH_LOCAL_PATH` or pass `--quantsmith-checkout` to use a
different local checkout. Its `origin` must name `thatquantguy44/QuantSmith` and
it must contain the locked commit. To update the reference, review the new
QuantSmith commit, change `integrations/quantsmith-docs.lock.json`, and restart
the server.

## Choose GitHub instead

GitHub mode is explicit; it never becomes the default because it makes outbound
requests from the local server. It reads only the same locked commit and
allowlisted blobs. For a private repository, put a fine-grained token with
**Contents: read** permission in a local environment variable; it is not written
to the workbook, add-in bundle, or report.

```bash
export FINASSERT_QUANTSMITH_GITHUB_TOKEN=your-local-token
python scripts/serve_excel.py --dir dist/excel --port 3000 \
  --cert localhost.pem --key localhost-key.pem \
  --quantsmith-source github
```

Use `--quantsmith-source disabled` to turn the optional reader off. In every
mode, the API binds only to loopback and never receives workbook cells or policy
data.

In the pane, expand **QuantSmith reference**, select **Load reference**, search
by path or name, and open a document. The panel displays raw text with source
path, commit and SHA-256. Document text cannot run as code or modify workbook
cells. No reference request is made until the user selects **Load reference**.

## Read-only HTTP API

The same local origin exposes:

| Route | Response |
| --- | --- |
| `GET /api/quantsmith/v1/docs` | Repository, pinned commit and document catalog. |
| `GET /api/quantsmith/v1/docs/{id}` | One allowlisted UTF-8 document, source path, commit and content SHA-256. |

The API uses opaque catalog IDs, never caller-supplied filesystem paths. It
limits document and catalog size, excludes symlinks, rejects a checkout with the
wrong Git origin or missing commit, and sends no cross-origin access header.
Reference mode can only bind to loopback. Disabled mode returns 404; a selected
but unavailable local or GitHub source returns 503, while the add-in's validation
workflow continues to work.

This is a single-user local reader. A shared or remotely hosted add-in needs a
separate authenticated service before private QuantSmith content can be served
to other users. Real Excel host acceptance for this panel remains to be done.
