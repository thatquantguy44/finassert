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
