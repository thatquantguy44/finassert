# Releasing

This page is for maintainers. Nothing here publishes anything by itself: the
release workflow builds and verifies the files, and publishing to PyPI stays a
separate step that maintainers enable deliberately.

## What is checked before a release

Every pull request and the release workflow run `scripts/verify_dist.py` on the
built files. It checks that:

- `pyproject.toml` and `src/finassert/_version.py` carry the same version, and
  the wheel and source distribution are named for it;
- the source distribution has the licence, changelog, examples, browser app
  sources, and `py.typed` marker;
- the wheel installs into a fresh virtual environment, outside the source tree,
  and the installed `finassert` command runs the sample policy and fails the one
  check the documentation says it fails;
- the installed units/FX, homogeneous MoneySource, workbook reader, and XLSX
  report writer work together, while importing their APIs does not import openpyxl;
- on a tag build, the tag is exactly `v` plus the version.

The release workflow also runs `twine check --strict`, so the README renders on
PyPI, builds the browser app, and keeps all of it as a workflow artifact.

## Making a release

1. Choose the version. While the package is below 1.0, any change to rule
   behavior, report schema, or policy format is a minor version.
2. Change the version in both `pyproject.toml` and `src/finassert/_version.py`.
   A unit test fails if they disagree.
3. In `CHANGELOG.md`, rename `Unreleased` to the version and date, and add a new
   empty `Unreleased` section above it.
4. Merge to `main`, then tag the merge commit and push the tag:

   ```bash
   git tag -s v0.2.0 -m "finassert 0.2.0"
   git push origin v0.2.0
   ```

5. Download the `distributions` artifact from the workflow run. The wheel and
   source distribution are what would be published; the browser app
   (`finassert-web.html`) can be attached to a GitHub release.

## Enabling publication to PyPI

Use trusted publishing, so no API token is stored anywhere:

1. On PyPI, add a trusted publisher for the project: repository
   `thatquantguy44/finassert`, workflow `release.yml`, environment `pypi`.
2. In the repository settings, create an environment named `pypi` and require
   a maintainer's approval for deployments.
3. Add this job to `.github/workflows/release.yml`:

   ```yaml
   publish:
     needs: build-and-verify
     if: github.ref_type == 'tag'
     runs-on: ubuntu-latest
     environment: pypi
     permissions:
       id-token: write
     steps:
       - uses: actions/download-artifact@v4
         with:
           name: distributions
           path: dist
       - run: rm -f dist/finassert-web.html
       - uses: pypa/gh-action-pypi-publish@release/v1
   ```

4. Only then update the README, which today says no PyPI release is claimed, and
   the install instructions, which today use the repository.

A published version cannot be replaced, only yanked, so publish a release
candidate (`0.2.0rc1`) to TestPyPI first if the process is new to you.

## Verified producer bundle

From a clean committed checkout, build and run the installed-distribution checks,
then generate and verify the identity sidecars:

```bash
uv build
uv run python scripts/verify_dist.py dist
uv run python scripts/release_bundle.py build dist
uv run python scripts/release_bundle.py verify dist
```

The release workflow retains `release-manifest.json` and `SHA256SUMS` alongside
the wheel/sdist. The manifest records exact Git identity, actual artifact byte
hashes, matching packaged Python source, Requires-Python/extras, policy/artifact
contract versions and a versioned canonical capability catalog. No wheel hashes
itself; sidecars stay outside the packages. Verification executes no candidate
code and accesses no network. The installed smoke test remains a separate step.

A consumer can verify against an independently approved manifest digest:

```bash
uv run python scripts/release_bundle.py verify dist --manifest-sha256 APPROVED_SHA256
```

Checksums alone do not authenticate their producer. Approve/pin the manifest or
artifact digest separately. `--allow-dirty` creates/inspects a development-only
bundle with `source.dirty=true`; ordinary verification refuses promotion of it.
Hashes identify exact artifacts; equivalent builds on different machines are not
assumed to be byte-identical. This adds no release publication or downstream
installer. QuantSmith owns its local environment/readiness controls.

Capability schema 1 also embeds the versioned treasury pack manifest. Pack required
rule references are checked against the bundled rule catalog. The digest covers
both rules and pack assumptions, so consumers can retain the approved inventory.
