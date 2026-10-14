import importlib.util
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[2]


def load_verifier() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "verify_dist", ROOT / "scripts" / "verify_dist.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_every_declared_version_agrees() -> None:
    versions = load_verifier().declared_versions()

    assert len(set(versions.values())) == 1, versions


def test_a_mismatched_release_tag_is_refused(tmp_path: Path) -> None:
    verifier = load_verifier()

    assert verifier.main([str(tmp_path), "--tag", "v999.0.0"]) == 1


def test_the_changelog_has_an_unreleased_section() -> None:
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

    assert "## [Unreleased]" in text
