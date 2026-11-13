from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from openpyxl import Workbook, load_workbook

import finassert as fa
from finassert._files import write_atomic
from finassert.core.exceptions import InvalidDataError
from finassert.core.models import ValidationReport, ValidationResult
from finassert.excel import write_report_xlsx
from finassert.loaders import parse_json, parse_xlsx
from finassert.reporting import build_artifact


def run_cli(folder: Path, *args: str) -> subprocess.CompletedProcess[str]:
    environment = {
        **os.environ,
        "PYTHONPATH": str(Path(__file__).parents[2] / "src"),
        "SOURCE_DATE_EPOCH": "1794528000",
    }
    return subprocess.run(
        [sys.executable, "-m", "finassert", *args],
        cwd=folder,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


def test_report_roundtrip_preserves_decimal_and_literal_strings(tmp_path: Path) -> None:
    amount = Decimal("12345678901234567890.123456789")
    result = ValidationResult(
        "=ID",
        "+Name",
        fa.Outcome.FAILED,
        fa.Severity.ERROR,
        "@message",
        observed=amount,
        expected=Decimal("-0.0100"),
        metadata={"hostile": "=1+1"},
    )
    report = ValidationReport((result,))
    path = tmp_path / "report.xlsx"
    write_report_xlsx(
        report,
        path,
        artifact=build_artifact(report, generated_at=datetime(2026, 11, 13, tzinfo=UTC)),
    )
    book = load_workbook(path, data_only=False)
    assert book.sheetnames == ["Summary", "Results", "Diagnostics"]
    row = list(book["Results"].values)[1]
    assert row[:5] == ("=ID", "+Name", "failed", "error", "@message")
    assert row[5:7] == (str(amount), "-0.0100")
    assert json.loads(row[8]) == {"hostile": "=1+1"}
    assert all(cell.data_type != "f" for sheet in book for cells in sheet for cell in cells)
    assert dict(book["Summary"].values)["failed"] == 1
    book.close()


def test_report_diagnostics_keep_complete_counts_with_bounded_rows(tmp_path: Path) -> None:
    report = fa.check({"v": [-1] * 100}, [fa.non_negative(column="v", max_violations=2)])
    path = tmp_path / "report.xlsx"
    write_report_xlsx(report, path)
    book = load_workbook(path)
    rows = list(book["Diagnostics"].values)[1:]
    assert len(rows) == 2
    assert all(row[1:5] == ("violations", 100, 2, True) for row in rows)
    assert [json.loads(row[5])["row"] for row in rows] == [0, 1]
    book.close()


@pytest.mark.parametrize("message", ["x" * 32768, "bad\x01text"])
def test_unrepresentable_report_never_replaces_existing_file(tmp_path: Path, message: str) -> None:
    path = tmp_path / "report.xlsx"
    path.write_bytes(b"previous report")
    report = ValidationReport(
        (ValidationResult("test.bad", "Bad", fa.Outcome.ERROR, fa.Severity.ERROR, message),)
    )
    with pytest.raises(ValueError):
        write_report_xlsx(report, path)
    assert path.read_bytes() == b"previous report"
    assert list(tmp_path.iterdir()) == [path]


def test_atomic_binary_output_cleans_up_on_replace_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "report.xlsx"
    path.write_bytes(b"original")

    def fail(*args: object) -> None:
        raise OSError("replace failed")

    monkeypatch.setattr(os, "replace", fail)
    with pytest.raises(OSError, match="replace failed"):
        write_atomic(path, b"new binary")
    assert path.read_bytes() == b"original"
    assert list(tmp_path.iterdir()) == [path]


def test_cli_workbook_region_json_and_xlsx_outputs(tmp_path: Path) -> None:
    source = tmp_path / "positions with spaces.xlsx"
    book = Workbook()
    sheet = book.active
    sheet.title = "Positions"
    for row in [["Daily positions"], [None], ["weight"], [0.25], [0.75], ["=SUM(A4:A5)"]]:
        sheet.append(row)
    book.save(source)
    book.close()
    before = source.read_bytes()
    (tmp_path / "policy.json").write_text(
        json.dumps({"version": 1, "rules": [{"rule": "weights_sum_to_one", "tolerance": "0"}]})
    )
    result = run_cli(
        tmp_path,
        "check",
        "--config",
        "policy.json",
        "--input",
        source.name,
        "--format",
        "xlsx",
        "--sheet",
        "Positions",
        "--header-row",
        "3",
        "--max-row",
        "5",
        "--output",
        "report.json",
        "--xlsx",
        "report.xlsx",
    )
    assert result.returncode == 0, result.stderr
    artifact = json.loads((tmp_path / "report.json").read_text())
    assert artifact["input"] == {
        "locator": source.name,
        "format": "xlsx",
        "sheet": "Positions",
        "header_row": 3,
        "max_row": 5,
    }
    assert artifact["report"]["results"][0]["observed"] == "1.00"
    assert source.read_bytes() == before
    output = load_workbook(tmp_path / "report.xlsx")
    assert list(output["Results"].values)[1][2] == "passed"
    output.close()
    parsed = parse_xlsx(before, sheet="Positions", header_row=3, max_row=5)
    assert parsed.column("weight")[1] == [4, 5]


@pytest.mark.parametrize(
    "args", [("--header-row", "0"), ("--header-row", "3", "--max-row", "2"), ("--header-row", "1")]
)
def test_cli_invalid_or_non_excel_region_is_usage_error(
    tmp_path: Path, args: tuple[str, ...]
) -> None:
    (tmp_path / "data.csv").write_text("weight\n1\n")
    (tmp_path / "policy.json").write_text('{"version":1,"rules":[]}')
    result = run_cli(tmp_path, "check", "--config", "policy.json", "--input", "data.csv", *args)
    assert result.returncode == 3


def test_cli_report_cannot_overwrite_policy_or_input(tmp_path: Path) -> None:
    (tmp_path / "policy.json").write_text('{"version":1,"rules":[]}')
    (tmp_path / "data.csv").write_text("weight\n1\n")
    for destination in ("policy.json", "data.csv"):
        before = (tmp_path / destination).read_bytes()
        result = run_cli(
            tmp_path,
            "check",
            "--config",
            "policy.json",
            "--input",
            "data.csv",
            "--xlsx",
            destination,
        )
        assert result.returncode == 3
        assert (tmp_path / destination).read_bytes() == before


@pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity"])
def test_json_input_rejects_non_json_numeric_constants(constant: str) -> None:
    with pytest.raises(InvalidDataError, match="non-JSON numeric constant"):
        parse_json('{"weight":[' + constant + "]}")
