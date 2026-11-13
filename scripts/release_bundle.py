"""Build or verify release integrity sidecars; never install or publish packages."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from finassert.release import build_release_bundle, verify_release_bundle

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    """Read the actual producer Git identity and build/verify a local bundle."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["build", "verify"])
    parser.add_argument("directory", type=Path)
    parser.add_argument("--allow-dirty", action="store_true")
    parser.add_argument("--manifest-sha256")
    args = parser.parse_args()
    try:
        if args.operation == "build":
            revision = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip()
            dirty = bool(
                subprocess.check_output(
                    ["git", "status", "--porcelain"], cwd=ROOT, text=True
                ).strip()
            )
            if dirty and not args.allow_dirty:
                raise ValueError(
                    "source checkout is dirty; commit first or explicitly use --allow-dirty"
                )
            manifest = build_release_bundle(args.directory, source_revision=revision, dirty=dirty)
        else:
            manifest = verify_release_bundle(
                args.directory,
                expected_manifest_sha256=args.manifest_sha256,
                allow_dirty=args.allow_dirty,
            )
        print(f"PASS: bundle {manifest['package']['version']} at {manifest['source']['commit']}")
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.exit(1, f"FAIL: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
