import hashlib
import io
import json
import tarfile
import zipfile
from pathlib import Path
from typing import Any

import pytest

from finassert._version import __version__
from finassert.release import build_release_bundle, verify_release_bundle

ROOT = Path(__file__).parents[2]
SHA = "a" * 40


@pytest.fixture
def bundle(tmp_path: Path) -> Path:
    metadata = (
        f"Metadata-Version: 2.3\nName: finassert\nVersion: {__version__}\n"
        "Requires-Python: >=3.11\nProvides-Extra: cli\n\n"
    ).encode()
    code = {
        "finassert/" + str(p.relative_to(ROOT / "src/finassert")): p.read_bytes()
        for p in (ROOT / "src/finassert").rglob("*.py")
    }
    wheel = tmp_path / f"finassert-{__version__}-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr(f"finassert-{__version__}.dist-info/METADATA", metadata)
        for name, value in code.items():
            archive.writestr(name, value)
    with tarfile.open(tmp_path / f"finassert-{__version__}.tar.gz", "w:gz") as archive:
        for name, value in {
            "PKG-INFO": metadata,
            **{"src/" + k: v for k, v in code.items()},
        }.items():
            item = tarfile.TarInfo(f"finassert-{__version__}/{name}")
            item.size = len(value)
            archive.addfile(item, io.BytesIO(value))
    return tmp_path


def build(bundle: Path, **kw: Any) -> dict[str, Any]:
    return build_release_bundle(bundle, source_revision=SHA, **kw)


def test_bundle_is_deterministic_offline_and_can_be_independently_pinned(bundle: Path) -> None:
    expected = build(bundle)
    original = (bundle / "release-manifest.json").read_bytes()
    checksum = hashlib.sha256(original).hexdigest()
    assert build(bundle) == expected
    assert (bundle / "release-manifest.json").read_bytes() == original
    assert verify_release_bundle(bundle, expected_manifest_sha256=checksum) == expected
    assert expected["package"]["requires_python"] == ">=3.11"
    assert expected["capabilities"]["rules"]
    with pytest.raises(ValueError, match="approved digest"):
        verify_release_bundle(bundle, expected_manifest_sha256="0" * 64)


@pytest.mark.parametrize("target", ["wheel", "sdist", "checksums"])
def test_byte_tampering_is_refused(bundle: Path, target: str) -> None:
    build(bundle)
    path = (
        next(bundle.glob("*.whl" if target == "wheel" else "*.tar.gz"))
        if target != "checksums"
        else bundle / "SHA256SUMS"
    )
    with path.open("ab") as handle:
        handle.write(b"tampered")
    with pytest.raises(ValueError, match="mismatch"):
        verify_release_bundle(bundle)


@pytest.mark.parametrize(
    "field,value",
    [
        ("schema_version", 2),
        ("source", {}),
        ("contracts", {}),
        ("capabilities", {}),
        ("capabilities_sha256", "0" * 64),
        ("package_source_sha256", "0" * 64),
        ("package", {}),
        ("artifacts", []),
        ("artifacts", [{"filename": "../outside"}, {"filename": "x"}]),
    ],
)
def test_manifest_contract_tampering_is_refused(bundle: Path, field: str, value: Any) -> None:
    manifest = build(bundle)
    manifest[field] = value
    (bundle / "release-manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        verify_release_bundle(bundle)


def test_dirty_development_bundles_cannot_be_promoted(bundle: Path) -> None:
    manifest = build(bundle, dirty=True)
    assert manifest["source"]["dirty"]
    with pytest.raises(ValueError, match="non-promotable"):
        verify_release_bundle(bundle)
    assert verify_release_bundle(bundle, allow_dirty=True) == manifest


@pytest.mark.parametrize("sha", ["main", "a" * 7, "G" * 40, ""])
def test_source_revision_requires_a_full_git_hash(bundle: Path, sha: str) -> None:
    with pytest.raises(ValueError, match="full Git SHA"):
        build_release_bundle(bundle, source_revision=sha)


def test_same_version_different_packaged_code_is_refused(bundle: Path) -> None:
    wheel = next(bundle.glob("*.whl"))
    with zipfile.ZipFile(wheel, "a") as archive:
        archive.writestr("finassert/untracked.py", "raise RuntimeError('never execute me')")
    with pytest.raises(ValueError, match="source differs"):
        build(bundle)


def test_unsafe_archive_paths_and_duplicate_metadata_are_refused(bundle: Path) -> None:
    with zipfile.ZipFile(next(bundle.glob("*.whl")), "a") as archive:
        archive.writestr("../escape.py", "raise RuntimeError('never execute me')")
    with pytest.raises(ValueError, match="unsafe archive path"):
        build(bundle)


def test_missing_extra_and_symlinked_distributions_are_refused(bundle: Path) -> None:
    build(bundle)
    wheel = next(bundle.glob("*.whl"))
    extra = bundle / "other.whl"
    extra.write_bytes(wheel.read_bytes())
    with pytest.raises(ValueError, match="exactly one"):
        verify_release_bundle(bundle)
    extra.unlink()
    saved = wheel.with_suffix(".saved")
    wheel.rename(saved)
    wheel.symlink_to(saved)
    with pytest.raises(ValueError, match="symlinks"):
        verify_release_bundle(bundle)


def test_duplicate_manifest_keys_are_refused(bundle: Path) -> None:
    build(bundle)
    path = bundle / "release-manifest.json"
    path.write_text('{"schema_version":1,' + path.read_text()[1:])
    with pytest.raises(ValueError, match="duplicate manifest key"):
        verify_release_bundle(bundle)
