"""Validate and copy prebuilt public guide assets without PDF runtime dependencies."""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
PDF_NAME = "finassert-user-guide.pdf"
METADATA_NAME = "finassert-user-guide.json"
API_PATH = "/api/finassert/v1/user-guide"
PDF_PATH = API_PATH + ".pdf"
SOURCE = ROOT / "docs" / "user-guide.md"
ASSETS = ROOT / "docs" / "assets"
REBUILD = (
    "uv run --with reportlab==4.4.9 --with Markdown==3.11 "
    "python scripts/build_user_guide.py --update-reference"
)


class GuideAssetError(ValueError):
    """Guide bytes or identity metadata are invalid or out of date."""


@dataclass(frozen=True)
class GuideAsset:
    """Verified prebuilt PDF bytes and their public identity metadata."""

    pdf: bytes
    metadata: dict[str, Any]


def catalog_document() -> dict[str, Any]:
    """Return the source catalog/templates represented in the guide appendix."""
    from finassert.policy import default_catalog, policy_templates

    return {
        "rules": default_catalog().to_dict()["rules"],
        "templates": [template.to_dict() for template in policy_templates()],
    }


def catalog_sha256() -> str:
    """Return a stable identity for every documented catalog/template setting."""
    body = json.dumps(catalog_document(), sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(body).hexdigest()


def read_asset(directory: Path) -> GuideAsset:
    """Read fixed guide assets, rejecting invalid identities and PDF signatures.

    Missing files raise FileNotFoundError so HTTP callers can distinguish 404
    from a present but invalid asset's 503 response.
    """
    pdf = (directory / PDF_NAME).read_bytes()
    try:
        metadata = json.loads((directory / METADATA_NAME).read_text(encoding="utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise GuideAssetError("Invalid guide metadata") from exc
    if (
        not isinstance(metadata, dict)
        or metadata.get("schema_version") != 1
        or metadata.get("filename") != PDF_NAME
        or metadata.get("download_url") != PDF_PATH
        or metadata.get("content_type") != "application/pdf"
        or not isinstance(metadata.get("tool"), dict)
        or metadata["tool"].get("name") != "finassert"
        or not isinstance(metadata.get("revision"), str)
        or not pdf.startswith(b"%PDF-")
        or type(metadata.get("bytes")) is not int
        or metadata["bytes"] != len(pdf)
        or metadata.get("sha256") != hashlib.sha256(pdf).hexdigest()
    ):
        raise GuideAssetError("Guide PDF and metadata do not match")
    return GuideAsset(pdf=pdf, metadata=metadata)


def copy_assets(destination: Path) -> None:
    """Copy source-current assets into an add-in build, or explain how to rebuild."""
    from finassert import __version__

    try:
        asset = read_asset(ASSETS)
        if (
            asset.metadata.get("source_sha256") != hashlib.sha256(SOURCE.read_bytes()).hexdigest()
            or asset.metadata.get("catalog_sha256") != catalog_sha256()
            or asset.metadata.get("builder_sha256")
            != hashlib.sha256((ROOT / "scripts" / "build_user_guide.py").read_bytes()).hexdigest()
            or asset.metadata["tool"].get("version") != __version__
        ):
            raise GuideAssetError("Guide source, catalog or product version changed")
    except (OSError, GuideAssetError) as exc:
        raise GuideAssetError(
            f"User guide assets are missing or stale. Rebuild with: {REBUILD}"
        ) from exc
    destination.mkdir(parents=True, exist_ok=True)
    for name in (PDF_NAME, METADATA_NAME):
        if (ASSETS / name).resolve() != (destination / name).resolve():
            shutil.copyfile(ASSETS / name, destination / name)
