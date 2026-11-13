"""Offline producer manifests for verified finassert wheel/source bundles."""

from __future__ import annotations

import hashlib
import json
import re
import tarfile
import zipfile
from email import message_from_bytes
from pathlib import Path, PurePosixPath
from typing import Any

from finassert._files import write_atomic
from finassert._version import __version__
from finassert.policy.catalog import default_catalog
from finassert.policy.packs import policy_packs
from finassert.policy.schema import SUPPORTED_VERSIONS
from finassert.reporting.artifact import ARTIFACT_SCHEMA_VERSION

MANIFEST_NAME = "release-manifest.json"
CHECKSUMS_NAME = "SHA256SUMS"
_MAX_FILE = 32 * 1024 * 1024
_MAX_CODE = 32 * 1024 * 1024


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n"


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _file_sha(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def _digest(code: dict[str, bytes]) -> str:
    digest = hashlib.sha256()
    for name, value in sorted(code.items()):
        digest.update(name.encode())
        digest.update(b"\0")
        digest.update(value)
    return digest.hexdigest()


def _safe(name: str) -> None:
    if "\\" in name or PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts:
        raise ValueError(f"unsafe archive path: {name!r}")


def _metadata(value: bytes) -> dict[str, Any]:
    metadata = message_from_bytes(value)
    for key in ("Name", "Version", "Requires-Python"):
        if len(metadata.get_all(key, [])) != 1:
            raise ValueError(f"expected exactly one metadata {key}")
    return {
        "name": metadata["Name"],
        "version": metadata["Version"],
        "requires_python": metadata["Requires-Python"],
        "extras": sorted(metadata.get_all("Provides-Extra", [])),
    }


def _payload(path: Path) -> tuple[dict[str, Any], dict[str, bytes]]:
    code: dict[str, bytes] = {}
    metadata: list[bytes] = []
    seen: set[str] = set()
    total = 0

    def add(name: str, size: int, read: Any) -> None:
        nonlocal total
        _safe(name)
        if name in seen or len(seen) >= 10000 or size > _MAX_FILE:
            raise ValueError("duplicate or oversized archive member/population")
        seen.add(name)
        if path.suffix == ".whl":
            selected = name.endswith(".py")
            meta = name.endswith(".dist-info/METADATA")
            relative = name
        else:
            parts = name.split("/", 1)
            relative = parts[1] if len(parts) == 2 else ""
            selected = relative.startswith("src/finassert/") and relative.endswith(".py")
            meta = relative == "PKG-INFO"
            relative = relative.removeprefix("src/")
        if selected or meta:
            total += size
            if total > _MAX_CODE:
                raise ValueError("archive code/metadata exceeds validation bound")
            value = read()
            if len(value) != size:
                raise ValueError("archive member length mismatch")
            if selected:
                if relative in code:
                    raise ValueError("duplicate packaged source")
                code[relative] = value
            if meta:
                metadata.append(value)

    if path.suffix == ".whl":
        with zipfile.ZipFile(path) as archive:
            for item in archive.infolist():
                if (item.external_attr >> 16) & 0o170000 == 0o120000:
                    raise ValueError("archive symlinks are not allowed")
                add(item.filename, item.file_size, lambda item=item: archive.read(item))
    else:
        with tarfile.open(path, "r:gz") as source_archive:
            for member in source_archive:
                if not (member.isfile() or member.isdir()):
                    raise ValueError("archive links/special members are not allowed")

                def read(item: tarfile.TarInfo = member) -> bytes:
                    handle = source_archive.extractfile(item)
                    if handle is None:
                        raise ValueError("expected a regular archive member")
                    with handle:
                        return handle.read()

                add(member.name, member.size, read)
    if len(metadata) != 1 or not code:
        raise ValueError("expected one package metadata record and Python source")
    return _metadata(metadata[0]), code


def _distributions(directory: Path) -> list[Path]:
    wheels, sdists = sorted(directory.glob("*.whl")), sorted(directory.glob("*.tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1:
        raise ValueError("expected exactly one wheel and one sdist")
    paths = wheels + sdists
    if any(p.is_symlink() or not p.is_file() for p in paths):
        raise ValueError("distribution artifacts must be regular files, not symlinks")
    return paths


def _source(source: dict[str, Any], *, allow_dirty: bool) -> None:
    if set(source) != {"repository", "commit", "dirty"}:
        raise ValueError("invalid source identity fields")
    if not isinstance(source["commit"], str) or not re.fullmatch(
        r"[0-9a-f]{40}|[0-9a-f]{64}", source["commit"]
    ):
        raise ValueError("source commit must be a full Git SHA")
    if source["repository"] != "https://github.com/thatquantguy44/finassert":
        raise ValueError("unexpected upstream repository identity")
    if type(source["dirty"]) is not bool:
        raise ValueError("source dirty flag must be boolean")
    if source["dirty"] and not allow_dirty:
        raise ValueError("dirty source is non-promotable")


def build_release_bundle(
    directory: str | Path,
    *,
    source_revision: str,
    dirty: bool = False,
) -> dict[str, Any]:
    """Write deterministic identity/checksum sidecars for the current producer code.

    Args:
        directory: Directory containing one wheel and one sdist.
        source_revision: Full Git commit of the producer checkout.
        dirty: Explicit development-only dirty marker; never silently promote it.

    Returns:
        The written version-1 manifest. No package is installed or published.
    """
    directory = Path(directory)
    source = {
        "repository": "https://github.com/thatquantguy44/finassert",
        "commit": source_revision,
        "dirty": dirty,
    }
    _source(source, allow_dirty=True)
    paths = _distributions(directory)
    package, wheel_code = _payload(paths[0])
    other, sdist_code = _payload(paths[1])
    producer = {
        "finassert/" + str(p.relative_to(Path(__file__).parent)).replace("\\", "/"): p.read_bytes()
        for p in Path(__file__).parent.rglob("*.py")
    }
    if package != other or package["name"] != "finassert" or package["version"] != __version__:
        raise ValueError("wheel/sdist/producer package metadata disagree")
    if wheel_code != sdist_code or wheel_code != producer:
        raise ValueError("wheel/sdist Python source differs from the producer tree")
    capabilities = {
        "schema_version": 1,
        **default_catalog().to_dict(),
        "packs": list(policy_packs()),
    }
    manifest = {
        "schema_version": 1,
        "source": source,
        "package": package,
        "package_source_sha256": _digest(wheel_code),
        "contracts": {
            "artifact": ARTIFACT_SCHEMA_VERSION,
            "policy": list(SUPPORTED_VERSIONS),
            "capabilities": 1,
        },
        "capabilities": capabilities,
        "capabilities_sha256": _sha(_json(capabilities).encode()),
        "artifacts": [
            {"filename": p.name, "size_bytes": p.stat().st_size, "sha256": _file_sha(p)}
            for p in paths
        ],
    }
    write_atomic(directory / MANIFEST_NAME, _json(manifest))
    lines = [f"{_file_sha(p)}  {p.name}\n" for p in [*paths, directory / MANIFEST_NAME]]
    write_atomic(
        directory / CHECKSUMS_NAME, "".join(sorted(lines, key=lambda line: line.split("  ")[1]))
    )
    verify_release_bundle(directory, allow_dirty=dirty)
    return manifest


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate manifest key: {key}")
        result[key] = value
    return result


def _verify_release_bundle(
    directory: str | Path,
    *,
    expected_manifest_sha256: str | None = None,
    allow_dirty: bool = False,
) -> dict[str, Any]:
    """Verify hashes, metadata, code and capabilities without executing candidates.

    Args:
        directory: Bundle directory.
        expected_manifest_sha256: Independently approved manifest digest, if supplied.
        allow_dirty: Explicit development inspection only, not promotion.

    Returns:
        The verified manifest; raises ValueError on a contract/integrity failure.
    """
    directory = Path(directory)
    path = directory / MANIFEST_NAME
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 4 * 1024 * 1024:
        raise ValueError("manifest must be a regular file")
    if expected_manifest_sha256 is not None and _file_sha(path) != expected_manifest_sha256:
        raise ValueError("manifest does not match the independently approved digest")
    manifest = json.loads(
        path.read_text(),
        object_pairs_hook=_unique,
        parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)),
    )
    expected = {
        "schema_version",
        "source",
        "package",
        "package_source_sha256",
        "contracts",
        "capabilities",
        "capabilities_sha256",
        "artifacts",
    }
    if (
        not isinstance(manifest, dict)
        or set(manifest) != expected
        or type(manifest["schema_version"]) is not int
        or manifest["schema_version"] != 1
    ):
        raise ValueError("unsupported release manifest schema")
    _source(manifest["source"], allow_dirty=allow_dirty)
    if manifest["contracts"] != {"artifact": 1, "policy": [1], "capabilities": 1}:
        raise ValueError("unsupported release contract versions")
    capabilities = manifest["capabilities"]
    if (
        not isinstance(capabilities, dict)
        or set(capabilities) != {"schema_version", "rules", "packs"}
        or capabilities["schema_version"] != 1
        or not isinstance(capabilities["rules"], list)
        or not isinstance(capabilities["packs"], list)
    ):
        raise ValueError("invalid capabilities schema")
    ids = [item["rule_id"] for item in capabilities["rules"]]
    if (
        not ids
        or len(ids) != len(set(ids))
        or _sha(_json(capabilities).encode()) != manifest["capabilities_sha256"]
    ):
        raise ValueError("capabilities identity mismatch")
    pack_ids = set()
    for pack in capabilities["packs"]:
        if (
            not isinstance(pack, dict)
            or pack.get("schema_version") != 1
            or type(pack.get("version")) is not int
            or pack["version"] < 1
            or pack.get("policy_schema_version") != 1
            or not isinstance(pack.get("pack_id"), str)
            or pack["pack_id"] in pack_ids
            or not isinstance(pack.get("datasets"), dict)
            or not pack["datasets"]
        ):
            raise ValueError("invalid capability pack manifest")
        pack_ids.add(pack["pack_id"])
        for dataset in pack["datasets"].values():
            if (
                not isinstance(dataset, dict)
                or set(dataset) != {"template", "required_rules"}
                or not isinstance(dataset["template"], str)
                or not isinstance(dataset["required_rules"], list)
                or any(rule_id not in ids for rule_id in dataset["required_rules"])
            ):
                raise ValueError("pack references unsupported capabilities")
    paths = _distributions(directory)
    entries = manifest["artifacts"]
    if (
        not isinstance(entries, list)
        or len(entries) != 2
        or {e.get("filename") for e in entries} != {p.name for p in paths}
    ):
        raise ValueError("artifact population mismatch")
    for entry in entries:
        if set(entry) != {"filename", "size_bytes", "sha256"}:
            raise ValueError("invalid artifact fields")
        name = entry["filename"]
        if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.+-]*", name):
            raise ValueError("unsafe artifact filename")
        artifact = directory / name
        if (
            type(entry["size_bytes"]) is not int
            or artifact.stat().st_size != entry["size_bytes"]
            or _file_sha(artifact) != entry["sha256"]
        ):
            raise ValueError(f"artifact integrity mismatch: {name}")
        metadata, code = _payload(artifact)
        if (
            metadata != manifest["package"]
            or metadata["name"] != "finassert"
            or _digest(code) != manifest["package_source_sha256"]
        ):
            raise ValueError("packaged metadata/source identity mismatch")
    checksum_path = directory / CHECKSUMS_NAME
    if checksum_path.is_symlink():
        raise ValueError("checksums must not be a symlink")
    expected_lines = sorted(f"{_file_sha(p)}  {p.name}" for p in [*paths, path])
    if sorted(checksum_path.read_text().splitlines()) != expected_lines:
        raise ValueError("SHA256SUMS mismatch")
    return manifest


def verify_release_bundle(
    directory: str | Path,
    *,
    expected_manifest_sha256: str | None = None,
    allow_dirty: bool = False,
) -> dict[str, Any]:
    """Verify a bundle offline, optionally against an independently pinned digest.

    Args:
        directory: Bundle containing the distributions and both sidecars.
        expected_manifest_sha256: Independently approved manifest digest.
        allow_dirty: Development inspection only; defaults to promotion checks.

    Returns:
        Verified version-1 manifest; malformed candidates raise ValueError.
    """
    try:
        return _verify_release_bundle(
            directory,
            expected_manifest_sha256=expected_manifest_sha256,
            allow_dirty=allow_dirty,
        )
    except (KeyError, TypeError, AttributeError, zipfile.BadZipFile, tarfile.TarError) as exc:
        raise ValueError(f"malformed release bundle: {exc}") from exc
