"""Tool server that lets AI assistants run finassert checks on local files.

The server speaks the Model Context Protocol over stdio, so desktop assistants
such as Claude can describe the available checks, help write a policy, and run
it against a file the user names. It needs the optional ``mcp`` package
(``finassert[assistant]``).

Every tool goes through the same policy, loader, and report code as the command
line. File access is limited to the folders given with ``--root`` (by default
the folder the server starts in). Tools only read files, except that
``check_data`` writes an HTML report when asked, and never overwrites one
unless told to.

Run with ``finassert-assistant --root /path/to/data``.
"""

from __future__ import annotations

import argparse
import os
from collections.abc import Sequence
from pathlib import Path, PureWindowsPath
from typing import Any

from finassert._files import write_atomic
from finassert._version import __version__
from finassert._xlsx import SheetError
from finassert.cli import exit_code
from finassert.core.exceptions import InvalidDataError, PolicyError
from finassert.loaders import TableSource, column_names, input_format_for, load_input
from finassert.policy import (
    POLICY_FORMATS,
    Policy,
    default_catalog,
    get_template,
    load_policy,
    parse_policy_text,
    policy_templates,
)
from finassert.policy.suggest import TemplateFit, fit_template, suggest_templates
from finassert.reporting import build_artifact, render_artifact_html

_PREVIEW_ROWS = 5
_MAX_LISTED = 20
_OUTCOME_WORDS = {0: "passed", 1: "failed", 2: "could_not_run"}

INSTRUCTIONS = """\
finassert checks financial data files (CSV, Excel .xlsx, JSON, Parquet) against
a policy: a short YAML list of named checks such as "weights add up to 1" or
"no negative values". Typical flow: call inspect_data to see a file's columns,
call suggest_policy to find the starter policy whose columns fit the file (or
pick checks with list_rules), confirm the policy with validate_policy, then run
check_data.

suggest_policy only proposes column matches. Show the user each match and get
their confirmation before running checks on the adapted policy; unmatched or
ambiguous columns need their decision.

When reporting results:
- An outcome of "error" means the check could not run (often a misspelled
  column). It is never a pass; say so plainly.
- Say which rows failed, using the row labels given (for CSV and Excel these
  are the row numbers shown in the spreadsheet).
- Repeat the policy's assumptions; the checks only mean something if they hold.
- Do not change tolerances or drop checks to make a file pass without the
  user's agreement.
"""


class Workspace:
    """Folders the server may read from, and write HTML reports into.

    Args:
        roots: Allowed folders. Paths are resolved, following symlinks, before
            they are compared, so links cannot reach outside the roots.
    """

    def __init__(self, roots: Sequence[str | os.PathLike[str]]) -> None:
        if not roots:
            raise ValueError("at least one root folder is required")
        self.roots = tuple(Path(root).expanduser().resolve(strict=True) for root in roots)
        for root in self.roots:
            if not root.is_dir():
                raise ValueError(f"{root} is not a folder")

    def path(self, value: str, *, must_exist: bool = True) -> Path:
        """Resolve ``value`` (absolute, or relative to the first root) inside a root."""
        # Resolving a network path (\\server\share or //server/share) can make
        # Windows connect and authenticate to that server, so refuse it first.
        if value.startswith(("\\\\", "//")) or PureWindowsPath(value).drive.startswith("\\\\"):
            raise PermissionError(f"{value!r} is a network path; use a folder on this computer")
        candidate = Path(value).expanduser()
        if not candidate.is_absolute():
            candidate = self.roots[0] / candidate
        resolved = candidate.resolve(strict=must_exist)
        if not any(resolved.is_relative_to(root) for root in self.roots):
            allowed = ", ".join(str(root) for root in self.roots)
            raise PermissionError(
                f"{value!r} is outside the folders this server may use: {allowed}"
            )
        return resolved


def list_rules() -> dict[str, Any]:
    """Describe every check a policy can name, in plain language."""
    return default_catalog().to_dict()


def list_templates() -> dict[str, Any]:
    """Describe the starter policies, including their YAML text."""
    return {
        "templates": [
            {**template.to_dict(), "yaml": template.to_yaml()} for template in policy_templates()
        ]
    }


def suggest_policy(
    workspace: Workspace,
    path: str,
    sheet: str | None = None,
    template: str | None = None,
) -> dict[str, Any]:
    """Rank starter policies by how well their columns match a data file's headers.

    Each suggestion lists which of the file's columns was matched to each column
    the template expects (and how), the adapted policy as YAML, and what to
    confirm. Matches are proposals, not decisions.
    """
    info = inspect_data(workspace, path, sheet)
    if not info["ok"]:
        return info
    columns = info["columns"]
    fits: tuple[TemplateFit, ...]
    if template:
        try:
            fits = (fit_template(get_template(template), columns),)
        except KeyError:
            names = [item.name for item in policy_templates()]
            return {"ok": False, "error": f"Unknown template {template!r}; use one of {names}."}
    else:
        fits = suggest_templates(columns)
    return {
        "ok": True,
        "columns": columns,
        "suggestions": [{**fit.to_dict(), "yaml": fit.adapted().to_yaml()} for fit in fits],
    }


def validate_policy(policy_text: str, policy_format: str = "yaml") -> dict[str, Any]:
    """Check a policy's text and list every problem with its line number."""
    try:
        policy = parse_policy_text(policy_text, format=policy_format)
    except PolicyError as exc:
        return {"ok": False, "issues": [issue.to_dict() for issue in exc.issues]}
    return {"ok": True, "policy": policy.describe()}


def inspect_data(workspace: Workspace, path: str, sheet: str | None = None) -> dict[str, Any]:
    """Return a data file's columns, row count, and first rows."""
    try:
        location = workspace.path(path)
        data = load_input(location, sheet=sheet)
    except SheetError as exc:
        if sheet is None and exc.sheets:
            return {
                "ok": False,
                "sheets": list(exc.sheets),
                "error": "The workbook has several sheets; pass the one to check as 'sheet'.",
            }
        return {"ok": False, "error": str(exc)}
    except (InvalidDataError, OSError) as exc:
        return {"ok": False, "error": _reason(exc)}
    columns = column_names(data)
    if isinstance(data, TableSource):
        rows, preview = data.row_count, data.preview(_PREVIEW_ROWS)
    elif isinstance(data, dict):
        rows = max((len(value) for value in data.values() if isinstance(value, list)), default=0)
        preview = []
    else:
        rows, preview = len(data), data[:_PREVIEW_ROWS]
    return {
        "ok": True,
        "path": str(location),
        "format": input_format_for(location),
        "columns": columns,
        "row_count": rows,
        "preview": [{str(key): _plain(value) for key, value in row.items()} for row in preview],
    }


def check_data(
    workspace: Workspace,
    path: str,
    *,
    policy_text: str | None = None,
    policy_format: str = "yaml",
    policy_path: str | None = None,
    template: str | None = None,
    sheet: str | None = None,
    html_report_path: str | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Run a policy against a data file and summarise every result.

    Exactly one of ``policy_text``, ``policy_path``, or ``template`` chooses the
    policy. ``html_report_path`` additionally writes the shareable HTML report.
    """
    chosen = [value for value in (policy_text, policy_path, template) if value is not None]
    if len(chosen) != 1:
        return {"ok": False, "error": "Give exactly one of policy_text, policy_path, or template."}
    try:
        policy = _policy(workspace, policy_text, policy_format, policy_path, template)
    except PolicyError as exc:
        return {"ok": False, "issues": [issue.to_dict() for issue in exc.issues]}
    except (KeyError, OSError) as exc:
        return {"ok": False, "error": _reason(exc)}
    try:
        location = workspace.path(path)
        data = load_input(location, sheet=sheet)
    except (InvalidDataError, OSError) as exc:
        return {"ok": False, "error": f"The data file could not be read: {_reason(exc)}"}

    report = policy.check(data)
    artifact = build_artifact(
        report,
        policy=policy,
        input_locator=str(location),
        input_format=input_format_for(location),
        input_sheet=sheet,
    )
    code = exit_code(report)
    result: dict[str, Any] = {
        "ok": True,
        "status": _OUTCOME_WORDS[code],
        "exit_code": code,
        "counts": report.counts_by_outcome,
        "policy": {
            "name": policy.name,
            "assumptions": list(policy.assumptions),
            "digest": policy.digest,
        },
        "results": [
            _summarise(item, described)
            for item, described in zip(
                artifact["report"]["results"], artifact["policy"]["rules"], strict=True
            )
        ],
        "html_report": None,
    }
    if html_report_path is not None:
        try:
            result["html_report"] = str(
                _write_report(
                    workspace, html_report_path, render_artifact_html(artifact), overwrite
                )
            )
        except (OSError, ValueError) as exc:
            result["html_report_error"] = _reason(exc)
    return result


def _policy(
    workspace: Workspace,
    policy_text: str | None,
    policy_format: str,
    policy_path: str | None,
    template: str | None,
) -> Policy:
    if template is not None:
        try:
            return get_template(template).policy()
        except KeyError:
            names = ", ".join(item.name for item in policy_templates())
            raise KeyError(f"unknown template {template!r}; available: {names}") from None
    if policy_path is not None:
        return load_policy(workspace.path(policy_path))
    assert policy_text is not None
    if policy_format not in POLICY_FORMATS:
        raise KeyError(f"policy_format must be one of: {', '.join(POLICY_FORMATS)}")
    return parse_policy_text(policy_text, format=policy_format)


def _summarise(result: dict[str, Any], described: dict[str, Any]) -> dict[str, Any]:
    metadata = result.get("metadata") or {}
    details = {
        key: value[:_MAX_LISTED] if isinstance(value, list) else value
        for key, value in metadata.items()
        if key in {"violations", "invalid_rows", "missing_rows", "violation_count", "column"}
    }
    return {
        "rule_id": result["rule_id"],
        "title": described.get("title") or result["rule_name"],
        "outcome": result["outcome"],
        "severity": result["severity"],
        "message": result["message"],
        "observed": result["observed"],
        "expected": result["expected"],
        "details": details,
    }


def _write_report(workspace: Workspace, value: str, html: str, overwrite: bool) -> Path:
    target = workspace.path(value, must_exist=False)
    if target.suffix.lower() not in {".html", ".htm"}:
        raise ValueError("the HTML report path must end in .html")
    if target.exists() and not overwrite:
        raise ValueError(f"{target} already exists; pass overwrite=true to replace it")
    write_atomic(target, html)
    return target


def _plain(value: Any) -> Any:
    if value is None or isinstance(value, bool | int | str):
        return value
    return str(value)


def _reason(exc: BaseException) -> str:
    if isinstance(exc, KeyError) and exc.args:
        return str(exc.args[0])
    if isinstance(exc, OSError) and exc.strerror and exc.filename:
        return f"{exc.strerror}: {exc.filename}"
    return str(exc)


def build_server(workspace: Workspace) -> Any:
    """Return an MCP server exposing the finassert tools for ``workspace``."""
    try:
        from mcp.server.mcpserver import MCPServer
        from mcp.types import ToolAnnotations
    except ImportError as exc:
        raise SystemExit(
            "The assistant server needs the MCP SDK: install 'finassert[assistant]'."
        ) from exc

    server = MCPServer(
        name="finassert",
        title="finassert financial data checks",
        instructions=INSTRUCTIONS,
        version=__version__,
    )
    read_only = ToolAnnotations(read_only_hint=True, open_world_hint=False)

    @server.tool(title="List available checks", annotations=read_only)
    def rules() -> dict[str, Any]:
        """List every check a policy can name, with when not to use it."""
        return list_rules()

    @server.tool(title="List starter policies", annotations=read_only)
    def templates() -> dict[str, Any]:
        """List starter policies with their assumptions and YAML text."""
        return list_templates()

    @server.tool(title="Suggest a policy for a data file", annotations=read_only)
    def suggest(path: str, sheet: str | None = None, template: str | None = None) -> dict[str, Any]:
        """Match starter policies to a data file's column names.

        Returns the best-fitting templates with the file column chosen for each
        expected column (and how confident the match is), plus the adapted YAML.
        Show the user the matches and ask them to confirm before running checks.
        """
        return suggest_policy(workspace, path, sheet, template)

    @server.tool(title="Validate a policy", annotations=read_only)
    def check_policy(policy_text: str, policy_format: str = "yaml") -> dict[str, Any]:
        """Check policy text (YAML or JSON); lists every problem with its line."""
        return validate_policy(policy_text, policy_format)

    @server.tool(title="Inspect a data file", annotations=read_only)
    def inspect(path: str, sheet: str | None = None) -> dict[str, Any]:
        """Show a data file's columns, row count, and first rows.

        Paths are absolute or relative to the server's first root folder. For an
        Excel workbook with several sheets, the sheet names are returned first.
        """
        return inspect_data(workspace, path, sheet)

    @server.tool(
        title="Run checks on a data file",
        annotations=ToolAnnotations(
            # With overwrite set, an existing HTML report can be replaced.
            read_only_hint=False,
            destructive_hint=True,
            open_world_hint=False,
        ),
    )
    def run_checks(
        path: str,
        policy_text: str | None = None,
        policy_format: str = "yaml",
        policy_path: str | None = None,
        template: str | None = None,
        sheet: str | None = None,
        html_report_path: str | None = None,
        overwrite: bool = False,
    ) -> dict[str, Any]:
        """Run a policy against a data file and return every result.

        Choose the policy with exactly one of policy_text, policy_path, or
        template. Pass html_report_path (ending in .html) to also save the
        shareable report; an existing file is replaced only if overwrite is true.
        """
        return check_data(
            workspace,
            path,
            policy_text=policy_text,
            policy_format=policy_format,
            policy_path=policy_path,
            template=template,
            sheet=sheet,
            html_report_path=html_report_path,
            overwrite=overwrite,
        )

    return server


def main(argv: Sequence[str] | None = None) -> int:
    """Start the assistant tool server on stdio."""
    parser = argparse.ArgumentParser(
        prog="finassert-assistant",
        description="Serve finassert checks to AI assistants over the Model Context Protocol.",
    )
    parser.add_argument(
        "--root",
        action="append",
        metavar="FOLDER",
        help="folder the server may read data and policies from (repeatable; default: here)",
    )
    arguments = parser.parse_args(argv)
    try:
        workspace = Workspace(arguments.root or [Path.cwd()])
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    build_server(workspace).run("stdio")
    return 0
