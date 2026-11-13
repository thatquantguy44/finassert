# 0015 — Verified upstream release bundles

**Status:** Implemented; full branch verification in progress

## Problem statement

Local consumers need exact source and artifact identity, beyond package version.
Existing release builds verify installation but do not produce a machine-readable
integrity/capability manifest. QuantSmith owns its local installer under its spec
0137; finassert supplies the independently inspectable producer bundle.

## Motivation and use cases

A consuming application pins an approved manifest/artifact digest, verifies local
bytes and records the chosen engine/contract identity with each run.

## Goals

Produce wheel/sdist hashes, source commit/dirty state, Python requirements, extras,
contract versions and a versioned capability catalog. Verify tampering, metadata
and packaged-code consistency without installing code or accessing the network.

## Non-goals

Package publication, release tagging, downstream installers, hosted services,
remote execution, automatic updates and changes to financial result semantics.

## Proposed architecture

A producer helper creates release-manifest.json and SHA256SUMS alongside an
already verified wheel/sdist. The manifest never hashes itself; SHA256SUMS hashes
artifacts and manifest but not itself. Both distributions must contain identical
Python source matching the producer source. The release workflow builds these
sidecars after existing installed-distribution smoke checks.

## Public API design

`finassert.release` helpers build/verify a version-1 manifest. A script
supports build and verify operations; build reads the actual Git revision and
rejects dirty source unless explicitly marked non-promotable. No runtime API
fetches or installs packages. Existing catalog and policy/report contracts are
reused, not duplicated as financial equations.

## Data contracts

Manifest version 1 includes source repository/full commit/dirty flag, distribution
name/version/Requires-Python/extras, package Python-source SHA-256, contract
versions, the canonical rule catalog and versioned pack snapshot/digest and exact wheel/sdist filenames,
byte sizes and SHA-256. Filenames are plain basenames; duplicate/path-traversing
entries, symlinks, missing/extra distributions and unsupported versions are errors.
A caller may supply an independently approved manifest SHA-256. Checksums prove
integrity relative to that trusted record, not authenticity on their own.

## Financial and numerical edge cases

Catalog parameters retain their existing Decimal/text encoding. Bundle metadata
must not mutate outcomes, tolerances, row identity, units or financial artifacts.

## Failure semantics

Invalid metadata, hashes, source contents, catalogs or dirty promotion fail closed.
Verification executes no wheel or sdist code. A dirty development bundle is marked
non-promotable and is refused by ordinary promotion verification.

## Implementation milestones

See [plan.md](plan.md), [tasks.md](tasks.md), and [roadmap.md](roadmap.md).

## Acceptance criteria

Deterministic manifests and checksums identify both distributions and exact source;
real installed-wheel checks still pass; byte/metadata/source/catalog tampering and
unsafe filenames are refused. Verify works offline and rejects unknown schemas.

## Testing requirements

Use authored wheel/sdist fixtures, mutate independent integrity fields and confirm
errors. Build a real bundle from a clean committed revision and verify its source,
capabilities and existing installed workflows. Never claim a release was published.

## Dependencies on other specifications

Uses 0005 artifacts, 0006 catalog, 0007 policies/distribution and 0008 unit metadata.
The six-slice delivery order is indexed in tasks.md; each later owning spec remains
canonical for its financial, property or workbook requirements.

## Explicit deferred work

Signing/attestation providers, publication, source-update automation, downstream
installation and additional release contract versions remain deferred.
