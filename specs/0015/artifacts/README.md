# Verified six-slice bundle evidence

Built from clean source commit `f0b96672c878f565f3657db84631126254a39c44`.
The [receipt](verified-bundle.json) records source, wheel/sdist, manifest, code
and capability hashes, Python requirement and treasury pack version.

The actual bundle is retained locally at `/tmp/finassert-six-slices-final-dist`:
wheel, sdist, release-manifest.json and SHA256SUMS. The receipt identifies these
specific bytes; it does not replace the full manifest or publish a release.
A rebuild creates a new candidate whose artifact hashes must be verified again.

Verification completed:

- Clean offline wheel/sdist build and producer sidecar generation.
- Offline bundle verification, including independently supplied manifest SHA256.
- Isolated installed-wheel checks: CLI pass/fail, units/FX provenance, workbook
  reading/reporting, both treasury factories and both cash/facility templates.
- Full repository suite: 3,624 passed, including real MCP stdio and report parity.
- Ruff, formatting (281 files), mypy (62 modules), strict MkDocs, browser and
  Excel add-in builds passed. External PR review remains pending.

Verify the retained bytes from this checkout:

```bash
PYTHONPATH=src .venv/bin/python scripts/release_bundle.py verify \
  /tmp/finassert-six-slices-final-dist \
  --manifest-sha256 3960c205bfc35327ebf896be79b708bafcea33574773d511aa1e111812d94ade
```

No release tag, package publication or downstream application change was made.
