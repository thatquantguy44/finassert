"""Self-contained HTML reports for people who do not read JSON.

The renderer is a pure view over a report artifact: it adds no judgement of
its own, makes no network requests, and embeds the artifact verbatim so the
file remains machine-readable.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime
from html import escape
from typing import TYPE_CHECKING, Any

from finassert.core.models import ValidationReport
from finassert.reporting.artifact import build_artifact

if TYPE_CHECKING:
    from finassert.policy.schema import Policy

_MAX_LISTED_VALUES = 50

_OUTCOME_TEXT = {
    "passed": ("Passed", "✓", "The data satisfied this check."),
    "failed": ("Failed", "✗", "The data broke this check."),
    "error": (
        "Could not run",
        "!",
        "The check did not run, so it is not a pass. This usually means a missing "
        "column or a value that could not be read.",
    ),
    "skipped": ("Skipped", "○", "The check was not evaluated, as its settings allow."),
}

_STYLE = """
:root {
  color-scheme: light dark;
  --bg: #f7f7f5; --surface: #ffffff; --text: #1d1d1b; --muted: #5d5d58;
  --border: #dcdcd6; --pass: #1f7a3d; --pass-bg: #e6f4ea; --fail: #b3261e;
  --fail-bg: #fce8e6; --error: #8a4b00; --error-bg: #fff1dc; --skip: #4d5562;
  --skip-bg: #eceef1; --code: #f0f0ec;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #141413; --surface: #1e1e1c; --text: #ececea; --muted: #a8a8a2;
    --border: #3a3a36; --pass: #7dd69b; --pass-bg: #173322; --fail: #f2a29b;
    --fail-bg: #3d1a17; --error: #f5c27a; --error-bg: #3a2a12; --skip: #c3c8d0;
    --skip-bg: #2a2d32; --code: #2a2a27;
  }
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--bg); color: var(--text);
  font: 16px/1.5 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
}
main { max-width: 960px; margin: 0 auto; padding: 32px 16px 48px; }
h1 { font-size: 1.6rem; margin: 0 0 4px; }
h2 { font-size: 1.15rem; margin: 32px 0 12px; }
h3 { font-size: 1.05rem; margin: 0; }
p { margin: 8px 0; }
.subtitle { color: var(--muted); margin: 0 0 20px; }
code {
  font: 0.85em ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  background: var(--code); padding: 1px 5px; border-radius: 4px; overflow-wrap: anywhere;
}
.banner {
  border-radius: 10px; padding: 16px 20px; border: 1px solid var(--border);
  display: flex; gap: 14px; align-items: center;
}
.banner .icon { font-size: 1.8rem; font-weight: 700; line-height: 1; }
.banner strong { display: block; font-size: 1.2rem; }
.banner.passed { background: var(--pass-bg); color: var(--pass); }
.banner.failed { background: var(--fail-bg); color: var(--fail); }
.banner p { color: var(--text); margin: 2px 0 0; }
.counts { display: flex; flex-wrap: wrap; gap: 8px; margin: 16px 0 0; padding: 0; }
.counts li { list-style: none; }
.pill {
  display: inline-flex; align-items: center; gap: 6px; padding: 2px 10px;
  border-radius: 999px; font-size: 0.9rem; font-weight: 600; white-space: nowrap;
}
.pill.passed { background: var(--pass-bg); color: var(--pass); }
.pill.failed { background: var(--fail-bg); color: var(--fail); }
.pill.error { background: var(--error-bg); color: var(--error); }
.pill.skipped { background: var(--skip-bg); color: var(--skip); }
.card {
  background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
  padding: 16px 20px; margin: 12px 0;
}
.card.failed { border-left: 5px solid var(--fail); }
.card.error { border-left: 5px solid var(--error); }
.card.skipped { border-left: 5px solid var(--skip); }
.card.passed { border-left: 5px solid var(--pass); }
.card header { display: flex; flex-wrap: wrap; gap: 8px 12px; align-items: center; }
.meta { color: var(--muted); font-size: 0.9rem; }
.message { font-weight: 500; }
table { border-collapse: collapse; width: 100%; margin: 8px 0; font-size: 0.92rem; }
th, td {
  text-align: left; padding: 6px 10px; border-bottom: 1px solid var(--border);
  vertical-align: top; overflow-wrap: anywhere;
}
th { color: var(--muted); font-weight: 600; width: 32%; overflow-wrap: normal; }
.rows th { width: auto; }
.table-wrap { overflow-x: auto; }
details summary { cursor: pointer; color: var(--muted); margin-top: 8px; }
dl.legend { display: grid; grid-template-columns: max-content 1fr; gap: 6px 12px; margin: 0; }
dl.legend dd { margin: 0; }
ul.assumptions { margin: 4px 0; padding-left: 20px; }
footer { margin-top: 40px; color: var(--muted); font-size: 0.85rem; }
@media (max-width: 520px) {
  main { padding: 20px 12px 40px; }
  .card { padding: 14px; }
  th { width: auto; min-width: 7.5em; }
}
@media print {
  body { background: #fff; color: #000; }
  .card, .banner { break-inside: avoid; }
  details { display: block; }
}
"""


def to_html(
    report: ValidationReport,
    *,
    policy: Policy | None = None,
    input_locator: str | None = None,
    input_format: str | None = None,
    input_sheet: str | None = None,
    generated_at: datetime | None = None,
    title: str | None = None,
) -> str:
    """Render ``report`` as a self-contained HTML page.

    Args:
        report: Results to render.
        policy: Policy whose rule descriptions and assumptions are shown.
        input_locator: Input description exactly as the user supplied it.
        input_format: Loader format used for the input.
        input_sheet: Worksheet read from a workbook input, if any.
        generated_at: Timestamp to record; defaults to the current UTC time.
        title: Page heading; defaults to the policy name.
    """
    artifact = build_artifact(
        report,
        policy=policy,
        input_locator=input_locator,
        input_format=input_format,
        input_sheet=input_sheet,
        generated_at=generated_at,
    )
    return render_artifact_html(artifact, title=title)


def render_artifact_html(artifact: Mapping[str, Any], *, title: str | None = None) -> str:
    """Render a report artifact produced by :func:`build_artifact` as HTML."""
    report = artifact["report"]
    policy = artifact.get("policy") or {}
    heading = title or policy.get("name") or "Validation report"
    results = report["results"]
    descriptions = _rule_descriptions(policy, results)

    parts = [
        "<!doctype html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<meta name="generator" content="finassert">',
        f"<title>{_text(heading)} — finassert</title>",
        f"<style>{_STYLE}</style>",
        "</head>",
        "<body>",
        "<main>",
        f"<h1>{_text(heading)}</h1>",
        '<p class="subtitle">finassert validation report</p>',
        _banner(report),
        _context(artifact),
        _assumptions(policy),
        _legend(),
        "<h2>Checks</h2>",
    ]
    if not results:
        parts.append('<p class="meta">This policy contains no checks.</p>')
    for index, result in enumerate(results):
        parts.append(_result_card(index, result, descriptions[index]))
    parts.extend(
        [
            "<footer>",
            f"<p>Generated by finassert {_text(artifact['tool']['version'])}. "
            "The machine-readable report is embedded in this file as "
            "<code>script#finassert-report</code>.</p>",
            "</footer>",
            "</main>",
            '<script type="application/json" id="finassert-report">',
            _embedded_json(artifact),
            "</script>",
            "</body>",
            "</html>",
        ]
    )
    return "\n".join(part for part in parts if part) + "\n"


def _banner(report: Mapping[str, Any]) -> str:
    counts = report["counts_by_outcome"]
    total = sum(counts.values())
    passed = bool(report["passed"])
    if total == 0:
        headline, detail = "Passed", "No checks were run, so nothing was found wrong."
    elif passed:
        headline = "Passed"
        detail = (
            f"All {total} check(s) passed."
            if not counts["skipped"]
            else (f"{counts['passed']} check(s) passed and {counts['skipped']} were skipped.")
        )
    else:
        headline = "Failed"
        problems = []
        if counts["failed"]:
            problems.append(f"{counts['failed']} check(s) failed")
        if counts["error"]:
            problems.append(f"{counts['error']} could not run")
        detail = " and ".join(problems) + f" out of {total}."
    state = "passed" if passed else "failed"
    icon = "✓" if passed else "✗"
    items = "".join(
        f'<li><span class="pill {outcome}">{_text(_OUTCOME_TEXT[outcome][0])}: '
        f"{counts[outcome]}</span></li>"
        for outcome in ("passed", "failed", "error", "skipped")
    )
    return (
        f'<section class="banner {state}" role="status" aria-live="polite">'
        f'<span class="icon" aria-hidden="true">{icon}</span>'
        f"<div><strong>{headline}</strong><p>{_text(detail)}</p></div></section>"
        f'<ul class="counts" aria-label="Results by outcome">{items}</ul>'
    )


def _context(artifact: Mapping[str, Any]) -> str:
    rows: list[tuple[str, Any]] = []
    source = artifact.get("input") or {}
    if source.get("locator"):
        rows.append(("Input", source["locator"]))
    if source.get("format"):
        rows.append(("Input format", source["format"]))
    if source.get("sheet"):
        rows.append(("Sheet", source["sheet"]))
    policy = artifact.get("policy") or {}
    if policy.get("description"):
        rows.append(("Policy description", policy["description"]))
    if policy.get("digest"):
        rows.append(("Policy fingerprint", policy["digest"]))
    rows.append(("Generated (UTC)", artifact["generated_at"]))
    rows.append(("finassert version", artifact["tool"]["version"]))
    body = "".join(f'<tr><th scope="row">{_text(k)}</th><td>{_text(v)}</td></tr>' for k, v in rows)
    return f'<h2>About this run</h2><div class="table-wrap"><table>{body}</table></div>'


def _assumptions(policy: Mapping[str, Any]) -> str:
    assumptions = policy.get("assumptions") or []
    if not assumptions:
        return ""
    items = "".join(f"<li>{_text(item)}</li>" for item in assumptions)
    return (
        "<h2>Assumptions</h2><p>These checks are only meaningful if the following hold:</p>"
        f'<ul class="assumptions">{items}</ul>'
    )


def _legend() -> str:
    entries = "".join(
        f'<dt><span class="pill {outcome}"><span aria-hidden="true">{icon}</span> '
        f"{_text(label)}</span></dt><dd>{_text(meaning)}</dd>"
        for outcome, (label, icon, meaning) in _OUTCOME_TEXT.items()
    )
    return f'<h2>How to read this report</h2><dl class="legend">{entries}</dl>'


def _rule_descriptions(
    policy: Mapping[str, Any], results: list[Mapping[str, Any]]
) -> list[Mapping[str, Any]]:
    described = policy.get("rules") or []
    if len(described) == len(results) and all(
        item.get("rule_id") == result["rule_id"]
        for item, result in zip(described, results, strict=True)
    ):
        return list(described)
    return [{} for _ in results]


def _result_card(index: int, result: Mapping[str, Any], description: Mapping[str, Any]) -> str:
    outcome = result["outcome"]
    label, icon, _ = _OUTCOME_TEXT.get(outcome, (outcome, "?", ""))
    title = description.get("title") or result["rule_name"]
    summary = description.get("summary")
    parts = [
        f'<article class="card {_text(outcome)}" aria-labelledby="check-{index}">',
        "<header>",
        f'<span class="pill {_text(outcome)}"><span aria-hidden="true">{icon}</span> '
        f"{_text(label)}</span>",
        f'<h3 id="check-{index}">{index + 1}. {_text(title)}</h3>',
        "</header>",
        f'<p class="meta">Rule <code>{_text(result["rule_id"])}</code> · severity '
        f"{_text(result['severity'])}</p>",
    ]
    if summary:
        parts.append(f"<p>{_text(summary)}</p>")
    parts.append(f'<p class="message">{_text(result["message"])}</p>')
    parts.append(_measurements(result))
    parts.append(_metadata(result.get("metadata") or {}, open_details=outcome != "passed"))
    parts.append("</article>")
    return "".join(part for part in parts if part)


def _measurements(result: Mapping[str, Any]) -> str:
    rows = [
        (name, result.get(key))
        for name, key in (
            ("Observed", "observed"),
            ("Expected", "expected"),
            ("Allowed difference", "tolerance"),
        )
        if result.get(key) is not None
    ]
    if not rows:
        return ""
    body = "".join(
        f'<tr><th scope="row">{_text(name)}</th><td>{_value(value)}</td></tr>'
        for name, value in rows
    )
    return f'<div class="table-wrap"><table>{body}</table></div>'


def _metadata(metadata: Mapping[str, Any], *, open_details: bool) -> str:
    if not metadata:
        return ""
    sections: list[str] = []
    scalars: list[tuple[str, Any]] = []
    for key, value in metadata.items():
        if isinstance(value, list) and value and all(isinstance(item, Mapping) for item in value):
            sections.append(_record_table(key, value))
        elif isinstance(value, list):
            if value:
                scalars.append((key, value))
        else:
            scalars.append((key, value))
    if scalars:
        body = "".join(
            f'<tr><th scope="row">{_text(_humanize(key))}</th><td>{_value(value)}</td></tr>'
            for key, value in scalars
        )
        sections.insert(0, f'<div class="table-wrap"><table>{body}</table></div>')
    state = " open" if open_details else ""
    return f"<details{state}><summary>Details</summary>{''.join(sections)}</details>"


def _record_table(key: str, records: list[Mapping[str, Any]]) -> str:
    columns: list[str] = []
    for record in records:
        for column in record:
            if column not in columns:
                columns.append(str(column))
    shown = records[:_MAX_LISTED_VALUES]
    head = "".join(f'<th scope="col">{_text(_humanize(column))}</th>' for column in columns)
    body = "".join(
        "<tr>" + "".join(f"<td>{_value(record.get(column))}</td>" for column in columns) + "</tr>"
        for record in shown
    )
    note = (
        f'<p class="meta">Showing {len(shown)} of {len(records)}.</p>'
        if len(records) > len(shown)
        else ""
    )
    return (
        f'<p class="meta">{_text(_humanize(key))}</p>'
        f'<div class="table-wrap"><table class="rows"><thead><tr>{head}</tr></thead>'
        f"<tbody>{body}</tbody></table></div>{note}"
    )


def _value(value: Any) -> str:
    if value is None:
        return '<span class="meta">—</span>'
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, Mapping):
        return ", ".join(f"{_text(_humanize(k))} {_value(v)}" for k, v in value.items())
    if isinstance(value, list):
        shown = ", ".join(_value(item) for item in value[:_MAX_LISTED_VALUES])
        extra = len(value) - _MAX_LISTED_VALUES
        return shown + (f" … and {extra} more" if extra > 0 else "")
    return _text(value)


def _humanize(key: str) -> str:
    return str(key).replace("_", " ").capitalize()


def _text(value: Any) -> str:
    return escape(str(value), quote=True)


def _embedded_json(artifact: Mapping[str, Any]) -> str:
    text = json.dumps(artifact, indent=2, sort_keys=True, allow_nan=False, ensure_ascii=True)
    return text.replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e")
