import json
import re
from datetime import UTC, datetime
from html.parser import HTMLParser

import finassert as fa
from finassert.policy import parse_policy
from finassert.reporting import build_artifact, render_artifact_html, to_html

MOMENT = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)


class _Collector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tags: list[tuple[str, dict[str, str | None]]] = []
        self.scripts: list[str] = []
        self._in_script = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tags.append((tag, dict(attrs)))
        self._in_script = tag == "script"

    def handle_endtag(self, tag: str) -> None:
        self._in_script = False

    def handle_data(self, data: str) -> None:
        if self._in_script:
            self.scripts.append(data)


def parse(page: str) -> _Collector:
    collector = _Collector()
    collector.feed(page)
    return collector


def embedded_artifact(page: str) -> dict[str, object]:
    match = re.search(
        r'<script type="application/json" id="finassert-report">\n(.*)\n</script>', page, re.S
    )
    assert match is not None
    result: dict[str, object] = json.loads(match.group(1))
    return result


def test_report_embeds_artifact_and_shows_outcomes() -> None:
    policy = parse_policy(
        {
            "version": 1,
            "name": "Daily positions",
            "assumptions": ["One portfolio per file"],
            "rules": [
                {"rule": "weights_sum_to_one"},
                {"rule": "non_negative", "column": "market_value"},
                {"rule": "non_negative", "column": "missing"},
            ],
        }
    )
    report = policy.check({"weight": [0.5, 0.5], "market_value": [1, -2]})
    page = to_html(report, policy=policy, input_locator="positions.csv", generated_at=MOMENT)

    assert page.startswith("<!doctype html>")
    assert "<title>Daily positions — finassert</title>" in page
    assert "1 check(s) failed and 1 could not run out of 3." in page
    assert "Portfolio weights add up to 100%" in page
    assert "One portfolio per file" in page
    assert "Could not run" in page
    assert "2026-01-02T03:04:05Z" in page
    artifact = embedded_artifact(page)
    assert artifact == build_artifact(
        report, policy=policy, input_locator="positions.csv", generated_at=MOMENT
    )


def test_report_is_self_contained() -> None:
    report = fa.check({"weight": [1]}, [fa.weights_sum_to_one()])
    page = to_html(report, generated_at=MOMENT)
    collector = parse(page)

    for tag, attrs in collector.tags:
        assert "src" not in attrs, tag
        assert "href" not in attrs, tag
        if tag == "script":
            assert attrs.get("type") == "application/json"
    assert "@import" not in page
    assert "url(" not in page
    assert "http://" not in page and "https://" not in page


def test_untrusted_text_is_escaped() -> None:
    hostile = '<script>alert(1)</script>"&'
    report = fa.check(
        {hostile: [-1]},
        [fa.non_negative(column=hostile)],
    )
    page = to_html(report, title=hostile, generated_at=MOMENT)
    collector = parse(page)

    assert "<script>alert" not in page
    assert [tag for tag, _ in collector.tags].count("script") == 1
    artifact = embedded_artifact(page)
    results = artifact["report"]["results"]  # type: ignore[index]
    assert results[0]["metadata"]["column"] == hostile


def test_passed_and_empty_reports_render() -> None:
    passed = to_html(fa.check({"weight": [1]}, [fa.weights_sum_to_one()]), generated_at=MOMENT)
    assert "All 1 check(s) passed." in passed
    assert "<details><summary>Details</summary>" in passed

    empty = to_html(fa.check({}, []), generated_at=MOMENT)
    assert "No checks were run" in empty
    assert "This policy contains no checks." in empty


def test_skipped_counts_are_explained() -> None:
    report = fa.check({"weight": [None]}, [fa.weights_sum_to_one(null_policy="skip")])
    page = to_html(report, generated_at=MOMENT)
    assert "0 check(s) passed and 1 were skipped." in page


def test_long_diagnostic_lists_are_capped() -> None:
    report = fa.check(
        {"v": [-1] * 80},
        [fa.non_negative(column="v", max_violations=80)],
    )
    page = to_html(report, generated_at=MOMENT)
    assert "Showing 50 of 80." in page


def test_render_is_deterministic_for_a_fixed_artifact() -> None:
    report = fa.check({"weight": [0.2, 0.2]}, [fa.weights_sum_to_one()])
    artifact = build_artifact(report, generated_at=MOMENT)
    assert render_artifact_html(artifact) == render_artifact_html(artifact)


def test_rule_descriptions_require_matching_results() -> None:
    policy = parse_policy({"version": 1, "rules": [{"rule": "weights_sum_to_one"}]})
    other = fa.check({"x": [1]}, [fa.non_negative(column="x")])
    page = to_html(other, policy=policy, generated_at=MOMENT)
    assert '">1. Financial values are nonnegative</h3>' in page
    assert "1. Portfolio weights add up to 100%" not in page


def test_reason_codes_read_as_words() -> None:
    rule = fa.nav_reconciles(market_value="mv", nav="nav", group_by=["fund"])
    report = fa.check({"fund": ["F"], "mv": [1], "nav": [2]}, [rule])
    page = to_html(report, generated_at=MOMENT)
    assert "<td>Does not reconcile</td>" in page
    assert (
        embedded_artifact(page)["report"]["results"][0]["metadata"]["failed_groups"][0][  # type: ignore[index]
            "reason"
        ]
        == "does_not_reconcile"
    )
