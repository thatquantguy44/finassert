"""Check built distributions the way a user would receive them.

Given a directory holding one wheel and one source distribution (``uv build``),
this verifies that both carry the version declared in ``pyproject.toml`` and
``src/finassert/_version.py``, that the source distribution has the files a
packager needs, and that the wheel installs into a fresh virtual environment
and runs the sample policy through the installed ``finassert`` command, with
the result the documentation promises.

Usage::

    python scripts/verify_dist.py dist [--tag v0.1.0]
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tarfile
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REQUIRED_IN_SDIST = (
    "LICENSE",
    "README.md",
    "CHANGELOG.md",
    "pyproject.toml",
    "examples/policy.yml",
    "examples/positions.csv",
    "src/finassert/py.typed",
    "web/index.html",
    "scripts/build_web.py",
)


def declared_versions() -> dict[str, str]:
    """Return the version written in each place that carries one."""
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    module = (ROOT / "src" / "finassert" / "_version.py").read_text(encoding="utf-8")
    match = re.search(r'__version__ = "([^"]+)"', module)
    return {
        "pyproject.toml": project["project"]["version"],
        "_version.py": match.group(1) if match else "<not found>",
    }


def main(argv: list[str] | None = None) -> int:
    """Verify the distributions and return a process exit code."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("dist", type=Path, help="directory with the wheel and sdist")
    parser.add_argument("--tag", help="release tag that must equal 'v' + the version")
    arguments = parser.parse_args(argv)

    problems: list[str] = []
    versions = declared_versions()
    if len(set(versions.values())) != 1:
        problems.append(f"versions disagree: {versions}")
    version = versions["pyproject.toml"]
    if arguments.tag is not None and arguments.tag != f"v{version}":
        problems.append(f"tag {arguments.tag!r} does not match version {version!r}")

    wheels = sorted(arguments.dist.glob("finassert-*.whl"))
    sdists = sorted(arguments.dist.glob("finassert-*.tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1:
        problems.append(f"expected one wheel and one sdist in {arguments.dist}")
        return _finish(problems)
    wheel, sdist = wheels[0], sdists[0]
    for path in (wheel, sdist):
        if not path.name.startswith(f"finassert-{version}"):
            problems.append(f"{path.name} does not carry version {version}")

    with tarfile.open(sdist) as archive:
        names = {name.split("/", 1)[1] for name in archive.getnames() if "/" in name}
    problems += [f"sdist is missing {name}" for name in REQUIRED_IN_SDIST if name not in names]

    problems += _check_installed_wheel(wheel, version)
    return _finish(problems)


def _check_installed_wheel(wheel: Path, version: str) -> list[str]:
    problems: list[str] = []
    with tempfile.TemporaryDirectory() as scratch:
        environment = Path(scratch) / "venv"
        subprocess.run([sys.executable, "-m", "venv", str(environment)], check=True)
        bin_dir = environment / ("Scripts" if sys.platform == "win32" else "bin")
        python = bin_dir / "python"
        subprocess.run(
            [str(python), "-m", "pip", "install", "--quiet", f"{wheel}[cli]"], check=True
        )
        # Run from a directory without the source tree so the installed copy is used.
        run = {"cwd": scratch, "capture_output": True, "text": True}
        located = subprocess.run(
            [
                str(python),
                "-c",
                "import finassert; print(finassert.__file__, finassert.__version__)",
            ],
            **run,  # type: ignore[call-overload]
        )
        location, _, installed = located.stdout.strip().rpartition(" ")
        if installed != version or "site-packages" not in location:
            problems.append(f"installed package is {located.stdout.strip()!r}, wanted {version}")
        command = bin_dir / "finassert"
        report = subprocess.run(
            [
                str(command),
                "check",
                "--config",
                str(ROOT / "examples" / "policy.yml"),
                "--input",
                str(ROOT / "examples" / "positions.csv"),
            ],
            **run,  # type: ignore[call-overload]
        )
        if report.returncode != 1 or "1 passed, 1 failed" not in report.stdout + report.stderr:
            problems.append(
                f"sample check gave exit {report.returncode}: {report.stdout}{report.stderr}"
            )
        templates = subprocess.run([str(command), "templates"], **run)  # type: ignore[call-overload]
        if templates.returncode != 0 or "cash-reconciliation" not in templates.stdout:
            problems.append("the installed command cannot list templates")
    return problems


def _finish(problems: list[str]) -> int:
    for problem in problems:
        print(f"FAIL: {problem}")
    if not problems:
        print("PASS: distributions verified")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
