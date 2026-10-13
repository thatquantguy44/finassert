import io
import json
import sys
from pathlib import Path
from typing import Any

import anyio
import pytest
from openpyxl import Workbook

from finassert.assistant import (
    Workspace,
    check_data,
    inspect_data,
    list_rules,
    list_templates,
    validate_policy,
)

ROOT = Path(__file__).resolve().parents[2]
POLICY = (ROOT / "examples" / "policy.yml").read_text(encoding="utf-8")
POSITIONS = (ROOT / "examples" / "positions.csv").read_text(encoding="utf-8")


@pytest.fixture
def workspace(tmp_path: Path) -> Workspace:
    data = tmp_path / "data"
    data.mkdir()
    (data / "positions.csv").write_text(POSITIONS, encoding="utf-8")
    (data / "policy.yml").write_text(POLICY, encoding="utf-8")
    (tmp_path / "secret.csv").write_text("weight\n1\n", encoding="utf-8")
    return Workspace([data])


def test_catalog_and_templates_are_described() -> None:
    assert [rule["name"] for rule in list_rules()["rules"]] == [
        "cash_reconciles",
        "nav_reconciles",
        "no_duplicates",
        "non_negative",
        "required_fields",
        "weights_sum_to_one",
    ]
    templates = list_templates()["templates"]
    by_name = {template["name"]: template for template in templates}
    assert sorted(by_name) == [
        "cash-reconciliation",
        "long-only-holdings",
        "multi-portfolio-holdings",
        "nav-reconciliation",
        "target-allocation",
    ]
    assert by_name["long-only-holdings"]["yaml"].startswith("# Long-only holdings file")
    assert all(template["document"]["assumptions"] for template in templates)


def test_validate_policy_reports_lines_and_suggestions() -> None:
    assert validate_policy(POLICY)["ok"] is True
    result = validate_policy("version: 1\nrules:\n  - rule: non_negativ\n")
    assert result["ok"] is False
    assert result["issues"][0]["line"] == 3
    assert result["issues"][0]["suggestion"] == "non_negative"


def test_check_with_a_policy_file_reports_failing_rows(workspace: Workspace) -> None:
    result = check_data(workspace, "positions.csv", policy_path="policy.yml")

    assert result["ok"] is True
    assert result["status"] == "failed" and result["exit_code"] == 1
    assert result["policy"]["assumptions"]
    failing = result["results"][1]
    assert failing["title"] == "No negative values"
    assert failing["details"]["violations"] == [{"row": 5, "value": -1500000}]


def test_check_with_policy_text_or_template(workspace: Workspace) -> None:
    from_text = check_data(workspace, "positions.csv", policy_text=POLICY)
    from_file = check_data(workspace, "positions.csv", policy_path="policy.yml")
    assert from_text["results"] == from_file["results"]
    assert from_text["policy"]["digest"] == from_file["policy"]["digest"]

    template = check_data(workspace, "positions.csv", template="long-only-holdings")
    assert template["status"] == "could_not_run"
    assert template["exit_code"] == 2
    assert "column 'market_value' was not found" in template["results"][2]["message"]


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        ({}, "exactly one of"),
        ({"policy_text": POLICY, "template": "long-only-holdings"}, "exactly one of"),
        ({"template": "long-only"}, "unknown template 'long-only'"),
        ({"policy_text": POLICY, "policy_format": "toml"}, "policy_format must be one of"),
        ({"policy_path": "missing.yml"}, "No such file"),
    ],
)
def test_check_argument_problems_are_explained(
    workspace: Workspace, arguments: dict[str, Any], message: str
) -> None:
    result = check_data(workspace, "positions.csv", **arguments)
    assert result["ok"] is False
    assert message in result["error"]


def test_invalid_policy_text_returns_issues(workspace: Workspace) -> None:
    result = check_data(workspace, "positions.csv", policy_text="version: 2\nrules: []\n")
    assert result["ok"] is False
    assert "Unsupported version 2" in result["issues"][0]["text"]


def test_files_outside_the_roots_are_refused(workspace: Workspace, tmp_path: Path) -> None:
    for path in ("../secret.csv", str(tmp_path / "secret.csv")):
        result = inspect_data(workspace, path)
        assert result["ok"] is False
        assert "outside the folders this server may use" in result["error"]
    link = workspace.roots[0] / "link.csv"
    link.symlink_to(tmp_path / "secret.csv")
    assert "outside the folders" in inspect_data(workspace, "link.csv")["error"]
    escaped = check_data(workspace, "positions.csv", policy_path="../secret.csv")
    assert "outside the folders" in escaped["error"]


@pytest.mark.parametrize("path", ["\\\\server\\share\\a.csv", "//server/share/a.csv"])
def test_network_paths_are_refused_before_resolving(workspace: Workspace, path: str) -> None:
    result = inspect_data(workspace, path)
    assert result["ok"] is False
    assert "is a network path" in result["error"]


def test_inspect_csv_and_multi_sheet_workbook(workspace: Workspace) -> None:
    info = inspect_data(workspace, "positions.csv")
    assert info["columns"] == ["ticker", "description", "weight", "Mkt Val (USD)"]
    assert info["row_count"] == 5 and info["format"] == "csv"
    assert info["preview"][0]["weight"] == "0.30"

    book = Workbook()
    book.active.title = "Notes"
    book.create_sheet("Positions").append(["weight"])
    buffer = io.BytesIO()
    book.save(buffer)
    (workspace.roots[0] / "book.xlsx").write_bytes(buffer.getvalue())
    ask = inspect_data(workspace, "book.xlsx")
    assert ask["ok"] is False and ask["sheets"] == ["Notes", "Positions"]
    assert inspect_data(workspace, "book.xlsx", sheet="Positions")["columns"] == ["weight"]


def test_html_report_is_written_only_where_allowed(workspace: Workspace) -> None:
    result = check_data(
        workspace, "positions.csv", policy_path="policy.yml", html_report_path="out/report.html"
    )
    assert "html_report_error" in result  # the folder does not exist

    result = check_data(
        workspace, "positions.csv", policy_path="policy.yml", html_report_path="report.html"
    )
    report = Path(result["html_report"])
    assert report.read_text(encoding="utf-8").startswith("<!doctype html>")
    assert report.stat().st_mode & 0o777 == 0o644

    again = check_data(
        workspace, "positions.csv", policy_path="policy.yml", html_report_path="report.html"
    )
    assert "already exists" in again["html_report_error"]
    replaced = check_data(
        workspace,
        "positions.csv",
        policy_path="policy.yml",
        html_report_path="report.html",
        overwrite=True,
    )
    assert replaced["html_report"] == str(report)

    for target, message in (("report.txt", "must end in .html"), ("../x.html", "outside")):
        refused = check_data(
            workspace, "positions.csv", policy_path="policy.yml", html_report_path=target
        )
        assert message in refused["html_report_error"]


def test_workspace_requires_existing_folders(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="at least one root"):
        Workspace([])
    with pytest.raises(FileNotFoundError):
        Workspace([tmp_path / "missing"])
    file = tmp_path / "file.txt"
    file.write_text("x", encoding="utf-8")
    with pytest.raises(ValueError, match="is not a folder"):
        Workspace([file])


def test_server_speaks_mcp_over_stdio(workspace: Workspace) -> None:
    from mcp import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    root = str(workspace.roots[0])
    params = StdioServerParameters(
        command=sys.executable,
        args=["-c", f"from finassert.assistant import main; main(['--root', {root!r}])"],
    )

    async def session() -> tuple[Any, list[str], Any]:
        async with stdio_client(params) as (read, write), ClientSession(read, write) as client:
            initialized = await client.initialize()
            tools = await client.list_tools()
            result = await client.call_tool(
                "run_checks", {"path": "positions.csv", "policy_path": "policy.yml"}
            )
            return initialized, [tool.name for tool in tools.tools], result

    initialized, names, result = anyio.run(session)
    assert initialized.server_info.name == "finassert"
    assert "never a pass" in initialized.instructions
    assert names == ["rules", "templates", "check_policy", "inspect", "run_checks"]
    assert result.is_error is False
    payload = result.structured_content or json.loads(result.content[0].text)
    assert payload["status"] == "failed"
