"""Safe file writing shared by the command line and the assistant server."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


def write_atomic(path: Path, text: str) -> None:
    """Write ``text`` to ``path`` so readers see the old file or the new one, never part.

    The new file gets the mode a plain write would give it, or keeps the mode of
    the file it replaces.
    """
    directory = path.parent if str(path.parent) else Path(".")
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=directory,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        temporary = Path(handle.name)
        try:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
            # Temporary files are owner-only; give the report the mode a plain
            # write would have, keeping an existing report's mode if there is one.
            os.chmod(handle.name, _report_mode(path))
        except BaseException:
            handle.close()
            temporary.unlink(missing_ok=True)
            raise
    try:
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def _report_mode(path: Path) -> int:
    try:
        return path.stat().st_mode & 0o777
    except OSError:
        umask = os.umask(0)
        os.umask(umask)
        return 0o666 & ~umask
