import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from finassert import cli

POSITIONS = "ticker,weight,market_value\nAAA,0.40,100\nBBB,0.60,250\n"
POLICY = """\
version: 1
name: Daily positions
rules:
  - rule: weights_sum_to_one
    column: weight
    tolerance: "0.0001"
  - rule: non_negative
    column: market_value
"""


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    folder = tmp_path / "with spaces"
    folder.mkdir()
    (folder / "positions file.csv").write_text(POSITIONS, encoding="utf-8")
    (folder / "policy file.yml").write_text(POLICY, encoding="utf-8")
    return folder


def run(*arguments: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    environment = {**os.environ, "SOURCE_DATE_EPOCH": "1767225600"}
    return subprocess.run(
        [sys.executable, "-m", "finassert", *arguments],
        cwd=cwd,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


def check_args(*extra: str) -> list[str]:
    return ["check", "--config", "policy file.yml", "--input", "positions file.csv", *extra]


def test_passing_run_writes_reports_and_exits_zero(workspace: Path) -> None:
    (workspace / "out").mkdir()
    result = run(
        *check_args("--output", "out/report.json", "--html", "report page.html"),
        cwd=workspace,
    )
    assert result.returncode == cli.EXIT_PASSED, result.stderr
    assert result.stdout.startswith("finassert PASS: 2 passed")
    artifact = json.loads((workspace / "out" / "report.json").read_text(encoding="utf-8"))
    assert artifact["schema_version"] == 1
    assert artifact["generated_at"] == "2026-01-01T00:00:00Z"
    assert artifact["input"] == {"locator": "positions file.csv", "format": "csv"}
    assert artifact["policy"]["name"] == "Daily positions"
    assert artifact["policy"]["digest"].startswith("sha256:")
    assert artifact["report"]["passed"] is True
    page = (workspace / "report page.html").read_text(encoding="utf-8")
    assert "All 2 check(s) passed." in page
    assert not list(workspace.rglob("*.tmp"))


def test_reports_are_deterministic_with_source_date_epoch(workspace: Path) -> None:
    run(*check_args("--output", "a.json"), cwd=workspace)
    run(*check_args("--output", "b.json"), cwd=workspace)
    assert (workspace / "a.json").read_bytes() == (workspace / "b.json").read_bytes()


def test_failure_exits_one(workspace: Path) -> None:
    (workspace / "positions file.csv").write_text(
        "weight,market_value\n0.5,-1\n0.5,1\n", encoding="utf-8"
    )
    result = run(*check_args(), cwd=workspace)
    assert result.returncode == cli.EXIT_FAILED
    assert "finassert FAIL: 1 passed, 1 failed" in result.stdout


def test_error_wins_over_failure(workspace: Path) -> None:
    (workspace / "positions file.csv").write_text("weight\n0.5\n", encoding="utf-8")
    result = run(*check_args(), cwd=workspace)
    assert result.returncode == cli.EXIT_ERROR
    assert "column 'market_value' was not found" in result.stdout


def test_invalid_policy_exits_three_with_line_numbers(workspace: Path) -> None:
    (workspace / "policy file.yml").write_text(
        "version: 1\nrules:\n  - rule: non_negativ\n    column: x\n", encoding="utf-8"
    )
    result = run(*check_args("--output", "report.json"), cwd=workspace)
    assert result.returncode == cli.EXIT_USAGE
    assert "line 3, rules[1].rule: Unknown rule 'non_negativ'" in result.stderr
    assert "Did you mean 'non_negative'?" in result.stderr
    assert not (workspace / "report.json").exists()


@pytest.mark.parametrize(
    "arguments",
    [
        [],
        ["check"],
        ["check", "--config", "p.yml"],
        ["frobnicate"],
        ["check", "--config", "p.yml", "--input", "x.csv", "--format", "xlsx"],
    ],
)
def test_usage_errors_exit_three(workspace: Path, arguments: list[str]) -> None:
    assert run(*arguments, cwd=workspace).returncode == cli.EXIT_USAGE


def test_missing_policy_file_exits_three(workspace: Path) -> None:
    result = run("check", "--config", "nope.yml", "--input", "positions file.csv", cwd=workspace)
    assert result.returncode == cli.EXIT_USAGE
    assert "cannot read policy 'nope.yml'" in result.stderr


@pytest.mark.parametrize(
    ("filename", "content", "message"),
    [
        ("missing.csv", None, "cannot read input 'missing.csv'"),
        ("bad.csv", "a,a\n1,2\n", "appears more than once"),
        ("data.ods", "", "cannot tell the format"),
        ("data.xls", "", "re-save it as .xlsx"),
    ],
)
def test_input_problems_exit_four(
    workspace: Path, filename: str, content: str | None, message: str
) -> None:
    if content is not None:
        (workspace / filename).write_text(content, encoding="utf-8")
    result = run("check", "--config", "policy file.yml", "--input", filename, cwd=workspace)
    assert result.returncode == cli.EXIT_IO
    assert message in result.stderr


def test_explicit_formats_override_extensions(workspace: Path) -> None:
    (workspace / "data.txt").write_text('{"weight": [1], "market_value": [1]}', encoding="utf-8")
    (workspace / "policy.txt").write_text(
        json.dumps({"version": 1, "rules": [{"rule": "weights_sum_to_one"}]}),
        encoding="utf-8",
    )
    result = run(
        "check",
        "--config",
        "policy.txt",
        "--policy-format",
        "json",
        "--input",
        "data.txt",
        "--format",
        "json",
        "--quiet",
        cwd=workspace,
    )
    assert result.returncode == cli.EXIT_PASSED, result.stderr
    assert result.stdout == ""


def test_output_paths_must_differ(workspace: Path) -> None:
    same = run(*check_args("--output", "r.out", "--html", "r.out"), cwd=workspace)
    assert same.returncode == cli.EXIT_USAGE
    overwrite = run(*check_args("--output", "positions file.csv"), cwd=workspace)
    assert overwrite.returncode == cli.EXIT_USAGE
    assert (workspace / "positions file.csv").read_text(encoding="utf-8") == POSITIONS


def test_missing_output_directory_exits_four(workspace: Path) -> None:
    result = run(*check_args("--output", "absent/report.json"), cwd=workspace)
    assert result.returncode == cli.EXIT_IO
    assert "cannot write report" in result.stderr


def test_failed_write_keeps_previous_report_and_exits_four(
    workspace: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(workspace)
    (workspace / "report.json").write_text("previous", encoding="utf-8")

    def refuse(source: str, target: object) -> None:
        raise PermissionError(13, "Permission denied")

    monkeypatch.setattr(cli.os, "replace", refuse)
    code = cli.main(check_args("--output", "report.json", "--quiet"))

    assert code == cli.EXIT_IO
    assert "cannot write report: Permission denied" in capsys.readouterr().err
    assert (workspace / "report.json").read_text(encoding="utf-8") == "previous"
    assert not list(workspace.glob("*.tmp"))


def test_empty_rule_set_passes(workspace: Path) -> None:
    (workspace / "policy file.yml").write_text("version: 1\nrules: []\n", encoding="utf-8")
    result = run(*check_args(), cwd=workspace)
    assert result.returncode == cli.EXIT_PASSED
    assert "0 passed, 0 failed" in result.stdout


def test_cli_results_match_python_api(workspace: Path) -> None:
    from finassert.loaders import load_input
    from finassert.policy import load_policy

    run(*check_args("--output", "report.json"), cwd=workspace)
    artifact = json.loads((workspace / "report.json").read_text(encoding="utf-8"))
    policy = load_policy(workspace / "policy file.yml")
    expected = policy.check(load_input(workspace / "positions file.csv"))
    assert artifact["report"] == expected.to_dict()


def test_help_and_version(workspace: Path) -> None:
    help_text = run("--help", cwd=workspace)
    assert help_text.returncode == 0
    assert "Exit codes: 0 passed" in help_text.stdout
    check_help = run("check", "--help", cwd=workspace)
    assert "--html FILE" in check_help.stdout
    version = run("--version", cwd=workspace)
    assert version.stdout.startswith("finassert ")


def test_rules_command_describes_catalog(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["rules"]) == cli.EXIT_PASSED
    text = capsys.readouterr().out
    assert "Portfolio weights add up to 100%" in text
    assert "Do not use when:" in text
    assert "column (required)" in text

    assert cli.main(["rules", "--json"]) == cli.EXIT_PASSED
    catalog = json.loads(capsys.readouterr().out)
    assert [rule["name"] for rule in catalog["rules"]] == [
        "cash_reconciles",
        "drift_within_band",
        "gross_within_limit",
        "in_range",
        "market_value_reconciles",
        "nav_reconciles",
        "net_within_limit",
        "no_duplicates",
        "non_negative",
        "position_rolls_forward",
        "position_within_limit",
        "required_fields",
        "simple_return_reconciles",
        "turnover_within_limit",
        "weights_match_market_values",
        "weights_sum_to_one",
    ]


def test_interrupt_writes_nothing(
    workspace: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(workspace)

    def interrupt(*_: object, **__: object) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(cli, "load_input", interrupt)
    assert cli.main(check_args("--output", "report.json")) == 130
    assert not (workspace / "report.json").exists()
    assert "interrupted" in capsys.readouterr().err


def test_reports_get_normal_file_permissions(workspace: Path) -> None:
    previous = os.umask(0o022)
    try:
        run(*check_args("--output", "report.json", "--html", "report.html"), cwd=workspace)
    finally:
        os.umask(previous)
    for name in ("report.json", "report.html"):
        assert (workspace / name).stat().st_mode & 0o777 == 0o644
    (workspace / "report.json").chmod(0o600)
    run(*check_args("--output", "report.json"), cwd=workspace)
    assert (workspace / "report.json").stat().st_mode & 0o777 == 0o600


def test_non_utf8_policy_exits_three(workspace: Path) -> None:
    (workspace / "policy file.yml").write_bytes(b"version: 1\nname: caf\xe9\nrules: []\n")
    result = run(*check_args(), cwd=workspace)
    assert result.returncode == cli.EXIT_USAGE
    assert "not UTF-8" in result.stderr


def test_excel_input_with_sheet_choice(workspace: Path) -> None:
    import io

    from openpyxl import Workbook

    book = Workbook()
    book.active.title = "Notes"
    book.active.append(["text"])
    positions = book.create_sheet("Positions")
    for row in [["weight", "market_value"], [0.4, 100], [0.6, -1]]:
        positions.append(row)
    buffer = io.BytesIO()
    book.save(buffer)
    (workspace / "book.xlsx").write_bytes(buffer.getvalue())

    ambiguous = run("check", "--config", "policy file.yml", "--input", "book.xlsx", cwd=workspace)
    assert ambiguous.returncode == cli.EXIT_USAGE
    assert "has 2 sheets ('Notes', 'Positions'); choose one; pass one with --sheet NAME" in (
        ambiguous.stderr
    )

    result = run(
        "check",
        "--config",
        "policy file.yml",
        "--input",
        "book.xlsx",
        "--sheet",
        "Positions",
        "--output",
        "report.json",
        cwd=workspace,
    )
    assert result.returncode == cli.EXIT_FAILED, result.stderr
    artifact = json.loads((workspace / "report.json").read_text(encoding="utf-8"))
    assert artifact["input"] == {"locator": "book.xlsx", "format": "xlsx", "sheet": "Positions"}
    violations = artifact["report"]["results"][1]["metadata"]["violations"]
    assert violations == [{"row": 3, "value": -1}]


def test_sheet_option_needs_an_excel_input(workspace: Path) -> None:
    result = run(*check_args("--sheet", "Data"), cwd=workspace)
    assert result.returncode == cli.EXIT_USAGE
    assert "a sheet can only be chosen for Excel (.xlsx) input" in result.stderr


def test_parquet_input(workspace: Path) -> None:
    import pyarrow as pa
    import pyarrow.parquet as pq

    pq.write_table(
        pa.table({"weight": [0.5, 0.5], "market_value": [1.0, 2.0]}),
        workspace / "positions.parquet",
    )
    result = run(
        "check", "--config", "policy file.yml", "--input", "positions.parquet", cwd=workspace
    )
    assert result.returncode == cli.EXIT_PASSED, result.stderr


def test_init_writes_a_template_and_refuses_to_overwrite(workspace: Path) -> None:
    listing = run("templates", cwd=workspace)
    assert listing.returncode == cli.EXIT_PASSED
    assert "long-only-holdings: Long-only holdings file" in listing.stdout

    created = run("init", "--template", "target-allocation", "--output", "new.yml", cwd=workspace)
    assert created.returncode == cli.EXIT_PASSED, created.stderr
    assert "Before relying on it:" in created.stdout
    assert "finassert template 'target-allocation'" in (workspace / "new.yml").read_text(
        encoding="utf-8"
    )

    again = run("init", "--template", "target-allocation", "--output", "new.yml", cwd=workspace)
    assert again.returncode == cli.EXIT_USAGE
    assert "already exists; pass --force" in again.stderr
    forced = run(
        "init",
        "--template",
        "long-only-holdings",
        "--output",
        "new.yml",
        "--force",
        cwd=workspace,
    )
    assert forced.returncode == cli.EXIT_PASSED
    assert "long-only-holdings" in (workspace / "new.yml").read_text(encoding="utf-8")


def test_init_suggests_the_closest_template(workspace: Path) -> None:
    result = run("init", "--template", "long-only", cwd=workspace)
    assert result.returncode == cli.EXIT_USAGE
    assert "Did you mean 'long-only-holdings'?" in result.stderr
    assert not (workspace / "policy.yml").exists()


ODD = "Fund,Security,Wt,MV (Base),NAV\nA,X,0.5,10,20\nA,Y,0.5,10,20\n"


def test_suggest_lists_fits_with_every_match_explained(workspace: Path) -> None:
    (workspace / "odd.csv").write_text(ODD, encoding="utf-8")

    result = run("suggest", "--input", "odd.csv", cwd=workspace)

    assert result.returncode == cli.EXIT_PASSED
    assert "1. multi-portfolio-holdings" in result.stdout
    assert "5 of 5 columns matched" in result.stdout
    assert "'portfolio' is your column 'Fund' (known name match)" in result.stdout
    assert "proposals" in result.stdout


def test_suggest_writes_a_policy_that_runs_on_the_file(workspace: Path) -> None:
    (workspace / "odd.csv").write_text(ODD, encoding="utf-8")

    written = run("suggest", "--input", "odd.csv", "--output", "odd.yml", cwd=workspace)
    checked = run("check", "--config", "odd.yml", "--input", "odd.csv", cwd=workspace)

    assert written.returncode == cli.EXIT_PASSED
    assert "Wrote odd.yml from the 'multi-portfolio-holdings' template" in written.stdout
    assert "Confirm the columns finassert matched" in written.stdout
    assert checked.returncode == cli.EXIT_PASSED, checked.stdout + checked.stderr


def test_suggest_refuses_to_replace_a_file_and_unknown_templates(workspace: Path) -> None:
    (workspace / "odd.csv").write_text(ODD, encoding="utf-8")
    (workspace / "odd.yml").write_text("keep", encoding="utf-8")

    clash = run("suggest", "--input", "odd.csv", "--output", "odd.yml", cwd=workspace)
    unknown = run("suggest", "--input", "odd.csv", "--template", "nav-reconcilation", cwd=workspace)

    assert clash.returncode == cli.EXIT_USAGE and "pass --force" in clash.stderr
    assert (workspace / "odd.yml").read_text(encoding="utf-8") == "keep"
    assert unknown.returncode == cli.EXIT_USAGE
    assert "Did you mean 'nav-reconciliation'?" in unknown.stderr


def test_suggest_with_no_fit_says_so_and_writes_nothing(workspace: Path) -> None:
    (workspace / "other.csv").write_text("Name,Notes\nx,y\n", encoding="utf-8")

    listed = run("suggest", "--input", "other.csv", cwd=workspace)
    written = run("suggest", "--input", "other.csv", "--output", "p.yml", cwd=workspace)

    assert listed.returncode == cli.EXIT_PASSED and "No starter policy fits" in listed.stdout
    assert written.returncode == cli.EXIT_USAGE
    assert not (workspace / "p.yml").exists()


def test_suggest_json_and_a_chosen_template(workspace: Path) -> None:
    (workspace / "odd.csv").write_text(ODD, encoding="utf-8")

    result = run(
        "suggest", "--input", "odd.csv", "--template", "nav-reconciliation", "--json", cwd=workspace
    )

    payload = json.loads(result.stdout)
    assert payload["columns"] == ["Fund", "Security", "Wt", "MV (Base)", "NAV"]
    (suggestion,) = payload["suggestions"]
    assert suggestion["name"] == "nav-reconciliation"
    assert suggestion["document"]["rules"][0]["group_by"] == ["Fund"]


def test_suggest_reports_unreadable_input(workspace: Path) -> None:
    result = run("suggest", "--input", "missing.csv", cwd=workspace)

    assert result.returncode == cli.EXIT_IO


WARN_POLICY = """\
version: 1
rules:
  - rule: weights_sum_to_one
    column: weight
    tolerance: "0.0001"
  - rule: non_negative
    column: market_value
    severity: warning
"""
NEGATIVE = "ticker,weight,market_value\nAAA,0.40,100\nBBB,0.60,-250\n"


def test_warning_severity_failures_do_not_fail_the_run(workspace: Path) -> None:
    (workspace / "warn.yml").write_text(WARN_POLICY, encoding="utf-8")
    (workspace / "neg.csv").write_text(NEGATIVE, encoding="utf-8")

    result = run("check", "--config", "warn.yml", "--input", "neg.csv", cwd=workspace)

    assert result.returncode == cli.EXIT_PASSED
    assert "finassert PASS (1 warning)" in result.stdout
    assert "[warning] arithmetic.non_negative" in result.stdout


def test_fail_on_makes_warnings_fail_the_run(workspace: Path) -> None:
    (workspace / "warn.yml").write_text(WARN_POLICY, encoding="utf-8")
    (workspace / "neg.csv").write_text(NEGATIVE, encoding="utf-8")

    strict = run(
        "check", "--config", "warn.yml", "--input", "neg.csv", "--fail-on", "warning", cwd=workspace
    )
    lenient = run(
        "check", "--config", "warn.yml", "--input", "neg.csv", "--fail-on", "error", cwd=workspace
    )

    assert strict.returncode == cli.EXIT_FAILED
    assert "Failing because --fail-on warning counts these warnings as failures." in strict.stdout
    assert lenient.returncode == cli.EXIT_PASSED
    bad = run(
        "check", "--config", "warn.yml", "--input", "neg.csv", "--fail-on", "fatal", cwd=workspace
    )
    assert bad.returncode == cli.EXIT_USAGE


def test_a_warning_level_check_that_cannot_run_still_exits_2(workspace: Path) -> None:
    policy = WARN_POLICY.replace("column: market_value", "column: no_such_column")
    (workspace / "warn.yml").write_text(policy, encoding="utf-8")
    (workspace / "neg.csv").write_text(NEGATIVE, encoding="utf-8")

    result = run("check", "--config", "warn.yml", "--input", "neg.csv", cwd=workspace)

    assert result.returncode == cli.EXIT_ERROR


def test_the_json_report_and_html_record_warnings(workspace: Path) -> None:
    (workspace / "warn.yml").write_text(WARN_POLICY, encoding="utf-8")
    (workspace / "neg.csv").write_text(NEGATIVE, encoding="utf-8")

    result = run(
        "check", "--config", "warn.yml", "--input", "neg.csv",
        "--output", "r.json", "--html", "r.html", cwd=workspace,
    )  # fmt: skip

    report = json.loads((workspace / "r.json").read_text(encoding="utf-8"))["report"]
    assert result.returncode == cli.EXIT_PASSED
    assert report["passed"] is True and report["warnings"] == 1
    assert "Passed with warnings" in (workspace / "r.html").read_text(encoding="utf-8")
