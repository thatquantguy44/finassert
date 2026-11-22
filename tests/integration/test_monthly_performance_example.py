"""Keep the P-05 worked workbook executable through the public Excel path."""

from __future__ import annotations

import json
import posixpath
import subprocess
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from finassert.cli import main as cli_main
from finassert.loaders import load_input
from finassert.policy import load_policy

EXAMPLE = Path(__file__).resolve().parents[2] / "examples" / "monthly-performance"
MAIN = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
PACKAGE_REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"


def _audit_sheet_path(source: zipfile.ZipFile) -> str:
    workbook = ElementTree.fromstring(source.read("xl/workbook.xml"))
    relation_id = next(
        sheet.attrib[f"{REL}id"]
        for sheet in workbook.findall(f"{MAIN}sheets/{MAIN}sheet")
        if sheet.attrib["name"] == "Audit input"
    )
    relationships = ElementTree.fromstring(source.read("xl/_rels/workbook.xml.rels"))
    target = next(
        relation.attrib["Target"]
        for relation in relationships.findall(f"{PACKAGE_REL}Relationship")
        if relation.attrib["Id"] == relation_id
    )
    return (
        target.lstrip("/")
        if target.startswith("/")
        else posixpath.normpath(posixpath.join("xl", target))
    )


def _correct_june_strategy_cumulative(source: Path, destination: Path) -> None:
    with zipfile.ZipFile(source) as archive:
        audit_sheet = _audit_sheet_path(archive)
        with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as corrected:
            for item in archive.infolist():
                contents = archive.read(item.filename)
                if item.filename == audit_sheet:
                    root = ElementTree.fromstring(contents)
                    cell = next(
                        candidate
                        for candidate in root.iter(f"{MAIN}c")
                        if candidate.attrib.get("r") == "E15"
                    )
                    value = cell.find(f"{MAIN}v")
                    assert value is not None
                    value.text = "0.061520150601"
                    contents = ElementTree.tostring(root, encoding="utf-8", xml_declaration=True)
                corrected.writestr(item, contents)


def _workbook_data(path: Path):
    return load_input(path, format="xlsx", sheet="Audit input", header_row=5, max_row=17)


def test_workbook_reports_the_seeded_source_row_and_passes_after_correction(tmp_path: Path) -> None:
    workbook = EXAMPLE / "monthly-performance-audit.xlsx"
    policy = load_policy(EXAMPLE / "policy.yml")

    failing = policy.check(_workbook_data(workbook)).results[0]

    assert failing.outcome.value == "failed"
    assert failing.metadata["tie_out"]["comparison_count"] == 24
    diagnostic = next(item for item in failing.diagnostics if item.kind == "tie_out_violations")
    finding = diagnostic.observations[0]
    assert finding["source_row"] == "src-2024-06"
    assert finding["period_end"] == "2024-06-30"
    assert finding["expected"] == "0.061520150601"
    assert finding["observed"] == "0.071520150601"

    corrected_path = tmp_path / workbook.name
    _correct_june_strategy_cumulative(workbook, corrected_path)
    corrected = policy.check(_workbook_data(corrected_path)).results[0]

    assert corrected.outcome.value == "passed"
    assert corrected.metadata["reference"] == failing.metadata["reference"]

    failing_report = tmp_path / "failing-report.json"
    failing_exit_code = cli_main(
        [
            "check",
            "--config",
            str(EXAMPLE / "policy.yml"),
            "--input",
            str(workbook),
            "--format",
            "xlsx",
            "--sheet",
            "Audit input",
            "--header-row",
            "5",
            "--max-row",
            "17",
            "--output",
            str(failing_report),
            "--quiet",
        ]
    )
    corrected_exit_code = cli_main(
        [
            "check",
            "--config",
            str(EXAMPLE / "policy.yml"),
            "--input",
            str(corrected_path),
            "--format",
            "xlsx",
            "--sheet",
            "Audit input",
            "--header-row",
            "5",
            "--max-row",
            "17",
            "--quiet",
        ]
    )

    assert failing_exit_code == 1
    assert corrected_exit_code == 0
    assert (
        json.loads(failing_report.read_text())["report"]
        == policy.check(_workbook_data(workbook)).to_dict()
    )


def test_python_example_accepts_the_expected_seeded_failure() -> None:
    completed = subprocess.run(
        [sys.executable, str(EXAMPLE / "run_audit.py"), "--expect", "failed"],
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert completed.returncode == 0, completed.stderr
    assert "Outcome: failed" in completed.stdout
    assert "src-2024-06" in completed.stdout
