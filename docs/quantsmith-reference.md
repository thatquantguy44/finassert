# QuantSmith reference in the Excel add-in

The optional reference panel reads allowlisted Markdown and the agent registry
from a **local checkout** of the private QuantSmith repository. It uses the exact
commit in `integrations/quantsmith-docs.lock.json`. The add-in
bundle contains no QuantSmith document content or GitHub credential.

## Set up a local reader

Clone QuantSmith with your existing GitHub access and make sure the pinned commit
is present:

```bash
git clone git@github.com:thatquantguy44/QuantSmith.git ../QuantSmith
git -C ../QuantSmith cat-file -e 86eed7f47d2735964705ecd6d43be842f594ba2f^{commit}
```

Build the Excel add-in using [the normal build instructions](excel-add-in.md).
Serve it over trusted localhost HTTPS and opt in to the reference:

```bash
python scripts/serve_excel.py --dir dist/excel --port 3000 \
  --cert localhost.pem --key localhost-key.pem \
  --quantsmith-checkout ../QuantSmith
```

The checkout's `origin` must name `thatquantguy44/QuantSmith`. The server reads
Git blobs from the pinned commit, so working-tree edits and a newer `main` do not
change what the pane shows. To update the reference, review the new QuantSmith
commit, change `integrations/quantsmith-docs.lock.json`, and restart the server.
A Git remote named `quantsmith` can help maintainers fetch updates, but the
lockfile is the version used by readers.

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
Reference mode can only bind to loopback. Without `--quantsmith-checkout`, the
routes return 404 and the add-in's validation workflow works as before.

This is a single-user local reader. A shared or remotely hosted add-in needs a
separate authenticated service before private QuantSmith content can be served
to other users. Real Excel host acceptance for this panel remains to be done.
