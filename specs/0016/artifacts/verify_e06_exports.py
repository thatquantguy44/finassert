"""Compare retained E-06 native exports with each other and the actual CLI.

This does not drive Excel or establish host acceptance. Supply files actually
saved from one native run; never substitute generated exports as native evidence.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from openpyxl import load_workbook
from openpyxl.utils.cell import range_boundaries
from openpyxl.utils.datetime import CALENDAR_MAC_1904

from finassert._excel_evidence import parse_context
from finassert.excel import results_sheet
from finassert.policy import load_policy
from finassert.workbook import read_workbook


def require(condition: bool, message: str) -> None:
    """Fail with a useful acceptance mismatch, including under optimized Python."""
    if not condition:
        raise ValueError(message)


def without_verification(artifact: dict[str, Any]) -> dict[str, Any]:
    """Allow only the per-action verification timestamp to differ between views."""
    result = copy.deepcopy(artifact)
    parse_context(result["input"]["excel"])
    result["input"]["excel"].pop("verified_at")
    return result


def verify(
    artifact_path: Path,
    html_path: Path,
    workbook_path: Path,
    policy_path: Path,
    results_name: str,
) -> dict[str, Any]:
    """Check native JSON/HTML/sheet parity, epoch, exact bounds and CLI results."""
    before = hashlib.sha256(workbook_path.read_bytes()).hexdigest()
    artifact = json.loads(artifact_path.read_text())
    context = parse_context(artifact["input"]["excel"])
    require(
        artifact["input"]["format"] == "excel-range"
        and artifact["input"]["locator"] == context["address"],
        "Artifact locator differs from its live source context",
    )
    quoted_sheet = "'" + context["worksheet_name"].replace("'", "''") + "'"
    require(
        context["address"].rsplit("!", 1)[0] in {context["worksheet_name"], quoted_sheet},
        "Address and worksheet name disagree",
    )
    html = html_path.read_text()
    embedded = re.search(r'id="finassert-report">(.*?)</script>', html, re.S)
    require(embedded is not None, "HTML has no embedded canonical artifact")
    html_artifact = json.loads(embedded[1])
    require(
        without_verification(artifact) == without_verification(html_artifact),
        "JSON and HTML artifacts differ beyond verified_at",
    )
    policy = load_policy(policy_path)
    require(policy.describe() == artifact["policy"], "Policy differs from the native run")
    bounds = range_boundaries(context["address"].rsplit("!", 1)[-1])
    c1, r1, c2, r2 = bounds
    require(
        r1 == context["header_row"]
        and r2 - r1 == context["physical_data_row_count"]
        and c2 - c1 + 1 == context["column_count"],
        "Source provenance and address bounds disagree",
    )
    book = load_workbook(workbook_path, data_only=False)
    try:
        require(
            (book.epoch == CALENDAR_MAC_1904) == (context["date_system"] == "1904"),
            "Workbook epoch differs from the explicit native interpretation",
        )
        source = book[context["worksheet_name"]]
        bound_headers = tuple(source.cell(r1, c).value for c in range(c1, c2 + 1))
        output = book[results_name]
        actual = [
            ["" if cell.value is None else cell.value for cell in row] for row in output.iter_rows()
        ]
        # Every action can reverify the same snapshot. Validate the sheet's time
        # through the same strict context contract before comparing all cells.
        fields = {row[0]: row[1] for row in actual if len(row) > 1}
        sheet_artifact = copy.deepcopy(artifact)
        sheet_artifact["input"]["excel"]["verified_at"] = fields.get("Excel verified at")
        parse_context(sheet_artifact["input"]["excel"])
        expected, _ = results_sheet(sheet_artifact)
        require(actual == expected, "Results sheet differs from canonical rows/counts/caps")
        require(
            not any(cell.data_type == "f" for row in output for cell in row),
            "Results sheet contains a formula",
        )
    finally:
        book.close()
    data = read_workbook(workbook_path, sheet=context["worksheet_name"], header_row=r1, max_row=r2)
    require(
        data.headers == bound_headers,
        "CLI worksheet region includes headers outside the bound rectangle",
    )
    require(
        len(data.column(data.headers[0])[0]) == context["data_row_count"],
        "Parsed row count differs from the native capture",
    )
    with tempfile.TemporaryDirectory(prefix="finassert-e06-cli-") as temporary:
        cli_path = Path(temporary) / "cli.json"
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "finassert",
                "check",
                "--input",
                str(workbook_path),
                "--sheet",
                context["worksheet_name"],
                "--header-row",
                str(r1),
                "--max-row",
                str(r2),
                "--config",
                str(policy_path),
                "--output",
                str(cli_path),
            ],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        require(cli_path.is_file(), f"CLI produced no artifact (exit {completed.returncode})")
        cli = json.loads(cli_path.read_text())
        require(cli["report"] == artifact["report"], "CLI and native canonical reports differ")
        require(cli["policy"] == artifact["policy"], "CLI and native policies differ")
    require(
        hashlib.sha256(workbook_path.read_bytes()).hexdigest() == before,
        "Acceptance verification changed the workbook",
    )
    return {
        "status": "PASS",
        "scope": "Retained files and CLI; host execution recorded separately",
        "source": context["address"],
        "date_system": context["date_system"],
        "policy_digest": artifact["policy"]["digest"],
        "snapshot_sha256": context["snapshot_sha256"],
        "files_sha256": {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (artifact_path, html_path, workbook_path, policy_path)
        },
    }


def main() -> int:
    """Verify explicitly supplied acceptance files; do not discover user workbooks."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path, required=True, dest="artifact")
    parser.add_argument("--html", type=Path, required=True)
    parser.add_argument("--workbook", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--results-sheet", required=True)
    args = parser.parse_args()
    try:
        print(
            json.dumps(
                verify(args.artifact, args.html, args.workbook, args.policy, args.results_sheet),
                indent=2,
            )
        )
    except (ValueError, KeyError, OSError, subprocess.TimeoutExpired) as exc:
        parser.exit(1, f"FAIL: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
