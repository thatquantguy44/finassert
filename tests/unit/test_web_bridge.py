import json

import pytest

from finassert import web
from finassert.policy import parse_policy_text

CSV = "ticker,weight,market_value\nAAA,0.40,100\nBBB,0.60,-5\n"


def test_catalog_lists_built_in_rules() -> None:
    names = [item["name"] for item in json.loads(web.catalog())["rules"]]
    assert names == [
        "cash_continuity",
        "cash_reconciles",
        "drift_within_band",
        "forecast_coverage",
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


def test_inspect_csv_and_json_inputs() -> None:
    info = json.loads(web.inspect_input(CSV, "positions.csv"))
    assert info == {
        "ok": True,
        "columns": ["ticker", "weight", "market_value"],
        "row_count": 2,
        "preview": [
            {"ticker": "AAA", "weight": "0.40", "market_value": 100},
            {"ticker": "BBB", "weight": "0.60", "market_value": -5},
        ],
        "notes": [],
    }
    columns = json.loads(web.inspect_input('{"w": [0.5, 0.5]}', "data.json"))
    assert columns["columns"] == ["w"] and columns["row_count"] == 2
    records = json.loads(web.inspect_input('[{"w": 1}, {"w": 2, "x": 3}]', "data.JSON"))
    assert records["columns"] == ["w", "x"] and records["row_count"] == 2


def test_inspect_reports_unreadable_input() -> None:
    info = json.loads(web.inspect_input("a,a\n", "bad.csv"))
    assert info["ok"] is False
    assert "more than once" in info["error"]


def test_read_policy_returns_editable_text_values() -> None:
    text = (
        "version: 1\nname: P\nrules:\n  - rule: weights_sum_to_one\n    tolerance: 0.001\n"
        "  - rule: non_negative\n    column: mv\n    max_violations: 3\n"
    )
    result = json.loads(web.read_policy(text, "policy.yml"))
    assert result == {
        "ok": True,
        "policy": {
            "version": 1,
            "name": "P",
            "rules": [
                {"rule": "weights_sum_to_one", "tolerance": {"$float": "0.001"}},
                {"rule": "non_negative", "column": "mv", "max_violations": 3},
            ],
        },
    }
    issues = json.loads(web.read_policy('{"version": 1}', "policy.json"))
    assert issues["ok"] is False
    assert "Missing 'rules'" in issues["issues"][0]["text"]


def test_run_returns_reports_and_the_exact_policy_that_ran() -> None:
    document = {
        "version": 1,
        "name": "Browser policy",
        "rules": [
            {"rule": "weights_sum_to_one", "column": "weight", "tolerance": "0.0001"},
            {"rule": "non_negative", "column": "market_value", "max_violations": 5},
        ],
    }
    result = json.loads(web.run(CSV, "positions.csv", json.dumps(document)))

    assert result["ok"] is True
    assert result["passed"] is False
    assert result["counts"] == {"passed": 1, "failed": 1, "error": 0, "skipped": 0}
    assert result["html"].startswith("<!doctype html>")
    artifact = json.loads(result["artifact_json"])
    assert artifact["input"] == {"locator": "positions.csv", "format": "csv"}

    exported = parse_policy_text(result["policy_yaml"], format="yaml")
    assert exported.digest == artifact["policy"]["digest"]
    rerun = exported.check(web.parse_csv(CSV))
    assert rerun.to_dict() == artifact["report"]


def test_run_reports_policy_and_input_problems() -> None:
    bad_policy = json.loads(web.run(CSV, "p.csv", json.dumps({"version": 1, "rules": [{}]})))
    assert bad_policy["ok"] is False and bad_policy["issues"]

    good = json.dumps({"version": 1, "rules": []})
    bad_input = json.loads(web.run("a,a\n", "p.csv", good))
    assert bad_input["ok"] is False
    assert bad_input["error"].startswith("The data file could not be read")


def test_inspect_handles_columns_of_different_lengths() -> None:
    info = json.loads(web.inspect_input('{"a": [1, 2, 3], "b": [1]}', "data.json"))
    assert info["ok"] is True
    assert info["preview"][2] == {"a": 3, "b": None}


def test_unknown_extensions_are_rejected_like_the_cli() -> None:
    assert json.loads(web.inspect_input("weight\n1\n", "data.txt"))["ok"] is False
    policy = json.loads(web.read_policy("version: 1\nrules: []\n", "policy.txt"))
    assert policy["ok"] is False
    assert "Cannot tell the policy format" in policy["issues"][0]["text"]


@pytest.mark.parametrize(
    "tolerance",
    ["0.0001", '"0.0001"', "1", "{absolute: 1, relative: 0.5}", "{}", "{relative: '0.1'}"],
)
def test_unedited_policy_runs_with_the_cli_fingerprint(tolerance: str) -> None:
    text = f"version: 1\nrules:\n  - rule: weights_sum_to_one\n    tolerance: {tolerance}\n"
    cli_policy = parse_policy_text(text, format="yaml")
    editable = json.loads(web.read_policy(text, "policy.yml"))["policy"]
    # The app sends back exactly what it loaded when nothing is edited.
    result = json.loads(web.run("weight\n1\n", "d.csv", json.dumps(editable)))
    artifact = json.loads(result["artifact_json"])
    assert artifact["policy"]["digest"] == cli_policy.digest
    exported = parse_policy_text(result["policy_yaml"], format="yaml")
    assert exported.to_document() == cli_policy.to_document()


def test_malformed_number_tags_are_reported_not_crashed() -> None:
    document = {
        "version": 1,
        "rules": [{"rule": "weights_sum_to_one", "tolerance": {"$float": "abc"}}],
    }
    result = json.loads(web.run("weight\n1\n", "d.csv", json.dumps(document)))
    assert result["ok"] is False and result["issues"]


def _workbook(*sheets: tuple[str, list[list[object]]]) -> bytes:
    import io

    from openpyxl import Workbook

    book = Workbook()
    book.remove(book.active)
    for title, rows in sheets:
        sheet = book.create_sheet(title)
        for row in rows:
            sheet.append(row)
    buffer = io.BytesIO()
    book.save(buffer)
    return buffer.getvalue()


class _JsBytes:
    """Stand-in for the proxy Pyodide passes for a JavaScript Uint8Array."""

    def __init__(self, data: bytes) -> None:
        self._data = data

    def to_py(self) -> memoryview:
        return memoryview(self._data)


def test_workbook_with_several_sheets_asks_for_a_sheet() -> None:
    data = _JsBytes(_workbook(("Notes", [["x"]]), ("Positions", [["weight"], [0.5], [0.5]])))
    ask = json.loads(web.inspect_input(data, "book.xlsx"))
    assert ask["ok"] is False and ask["sheets"] == ["Notes", "Positions"]

    info = json.loads(web.inspect_input(data, "book.xlsx", "Positions"))
    assert info["ok"] is True
    assert info["columns"] == ["weight"] and info["row_count"] == 2

    document = json.dumps({"version": 1, "rules": [{"rule": "weights_sum_to_one"}]})
    result = json.loads(web.run(data, "book.xlsx", document, "Positions"))
    assert result["passed"] is True
    assert json.loads(result["artifact_json"])["input"]["sheet"] == "Positions"


def test_single_sheet_workbook_opens_directly() -> None:
    data = _workbook(("Only", [["weight"], [1]]))
    info = json.loads(web.inspect_input(data, "book.xlsx"))
    assert info["ok"] is True and info["preview"] == [{"weight": 1}]


def test_browser_rejects_formats_it_cannot_open() -> None:
    result = json.loads(web.inspect_input(b"PAR1", "data.parquet"))
    assert result["ok"] is False
    assert "cannot be opened in the browser" in result["error"]
    assert json.loads(web.inspect_input("a\n1\n", "data.csv", "Sheet"))["ok"] is False


def test_templates_are_offered_in_editable_form() -> None:
    offered = json.loads(web.templates())["templates"]
    names = [item["name"] for item in offered]
    assert names == sorted(names) and "long-only-holdings" in names
    holdings = offered[names.index("long-only-holdings")]
    assert holdings["policy"]["assumptions"]
    result = json.loads(
        web.run("weight,market_value\n0.5,1\n0.5,1\n", "d.csv", json.dumps(holdings["policy"]))
    )
    assert result["passed"] is True


@pytest.mark.parametrize("limit", ["1.3", '"1.30"', "2", '"-0.5"'])
def test_unedited_limits_run_with_the_cli_fingerprint(limit: str) -> None:
    text = (
        f"version: 1\nrules:\n  - rule: net_within_limit\n    value: weight\n    maximum: {limit}\n"
    )
    cli_policy = parse_policy_text(text, format="yaml")
    editable = json.loads(web.read_policy(text, "policy.yml"))["policy"]
    result = json.loads(web.run("weight\n1\n", "d.csv", json.dumps(editable)))
    artifact = json.loads(result["artifact_json"])
    assert artifact["policy"]["digest"] == cli_policy.digest
    exported = parse_policy_text(result["policy_yaml"], format="yaml")
    assert exported.to_document() == cli_policy.to_document()


def test_suggest_ranks_templates_and_returns_editable_adapted_policies() -> None:
    columns = json.dumps(["Fund", "Security", "Wt", "MV (Base)", "NAV"])

    result = json.loads(web.suggest(columns))

    assert result["ok"] is True
    best = result["suggestions"][0]
    assert best["name"] == "multi-portfolio-holdings"
    assert (best["matched"], best["expected"]) == (5, 5)
    assert best["policy"]["rules"][2]["group_by"] == ["Fund"]
    assert "document" not in best
    assert any("Confirm the columns" in line for line in best["adapt"])

    chosen = json.loads(web.suggest(columns, "long-only-holdings"))["suggestions"]
    assert [item["name"] for item in chosen] == ["long-only-holdings"]
    assert json.loads(web.suggest("[]", "no-such"))["ok"] is False
    assert json.loads(web.suggest(json.dumps(["Name"])))["suggestions"] == []


def test_run_reports_warnings_without_failing_the_run() -> None:
    document = {
        "version": 1,
        "rules": [
            {"rule": "non_negative", "column": "weight", "severity": "warning"},
        ],
    }

    result = json.loads(web.run("weight\n0.5\n-0.1\n", "d.csv", json.dumps(document)))

    assert result["passed"] is True and result["warnings"] == 1
    assert result["counts"]["failed"] == 1
    assert "Passed with warnings" in result["html"]


def selected_cells(**extra: object) -> str:
    cells = {
        "values": [["portfolio", "weight"], ["A", 0.6], ["A", 0.4], ["B", "#N/A"]],
        "valueTypes": [
            ["String"] * 2,
            ["String", "Double"],
            ["String", "Double"],
            ["String", "Error"],
        ],
        "firstRow": 4,
        **extra,
    }
    return json.dumps(cells)


def test_cells_selected_in_excel_are_inspected_and_noted() -> None:
    info = json.loads(web.inspect_input(selected_cells(), "Sheet1!A4:B7", None, "excel-range"))

    assert info["ok"] is True
    assert info["columns"] == ["portfolio", "weight"] and info["row_count"] == 3
    assert "1 cell(s) show Excel errors" in info["notes"][0]
    assert json.loads(web.inspect_input(CSV, "positions.csv"))["notes"] == []


def test_checks_run_on_selected_cells_with_the_sheets_row_numbers() -> None:
    document = {
        "version": 1,
        "rules": [{"rule": "non_negative", "column": "weight"}],
    }

    result = json.loads(
        web.run(selected_cells(), "Sheet1!A4:B7", json.dumps(document), None, "excel-range")
    )

    assert result["ok"] is True and result["passed"] is False
    artifact = json.loads(result["artifact_json"])
    assert artifact["input"] == {"locator": "Sheet1!A4:B7", "format": "excel-range"}
    assert artifact["report"]["results"][0]["metadata"]["invalid_rows"] == [7]


def test_selected_cells_that_cannot_be_read_are_reported() -> None:
    document = json.dumps({"version": 1, "rules": []})

    bad = json.loads(web.run("not json", "Sheet1!A1", document, None, "excel-range"))
    empty = json.loads(
        web.inspect_input(json.dumps({"values": []}), "Sheet1!A1", None, "excel-range")
    )
    unknown = json.loads(web.inspect_input("{}", "x", None, "xml"))

    assert bad["ok"] is False and "could not be read" in bad["error"]
    assert empty["ok"] is False and "first row holds the column names" in empty["error"]
    assert unknown["ok"] is False


def test_the_results_sheet_rows_come_from_the_artifact() -> None:
    document = {"version": 1, "rules": [{"rule": "non_negative", "column": "weight"}]}
    result = json.loads(
        web.run(selected_cells(), "Sheet1!A4:B7", json.dumps(document), None, "excel-range")
    )

    sheet = json.loads(web.results_sheet(result["artifact_json"]))
    rows, bold = sheet["rows"], sheet["boldRows"]

    assert rows[0][0] == "finassert results" and bold[0] == 0
    assert rows[bold[1]] == ["Check", "Result", "Severity", "Row", "Details"]
    assert rows[bold[1] + 1][:3] == ["No negative values", "Failed", "error"]
    assert rows[bold[1] + 2][3] == 7
    assert {len(row) for row in rows} == {5}
