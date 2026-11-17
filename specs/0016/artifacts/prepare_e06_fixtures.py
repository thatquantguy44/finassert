"""Prepare disposable synthetic E-06 workbooks; never opens Excel or user files.

Run with the repository's Excel extra installed:
    PYTHONPATH=src .venv/bin/python specs/0016/artifacts/prepare_e06_fixtures.py /tmp/e06
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook
from openpyxl.utils.datetime import CALENDAR_MAC_1904, CALENDAR_WINDOWS_1900
from openpyxl.worksheet.filters import AutoFilter
from openpyxl.worksheet.table import Table, TableStyleInfo

from finassert.excel import policy_sheet_rows
from finassert.policy import parse_policy
from finassert.policy.templates import get_template


def prepare(destination: Path) -> None:
    """Write two epoch fixtures, policies and their actual byte identities."""
    destination.mkdir(parents=True, exist_ok=True)
    for name in ("long-only-holdings", "multi-portfolio-holdings"):
        (destination / f"{name}.yml").write_text(get_template(name).to_yaml(), encoding="utf-8")
    policies = {
        "ambiguous": {
            "version": 1,
            "rules": [{"rule": "in_range", "column": "value", "minimum": 0, "row_key": "id"}],
        },
        "missing": {
            "version": 1,
            "rules": [
                {
                    "rule": "forecast_coverage",
                    "period_start": "start",
                    "period_end": "end",
                    "first_period": "2026-10-01",
                    "periods": 2,
                    "group_by": ["entity"],
                    "currency": "ccy",
                    "expected_scope": [
                        {"entity": "A", "ccy": "USD"},
                        {"entity": "B", "ccy": "USD"},
                    ],
                }
            ],
        },
    }
    for name, policy in policies.items():
        parse_policy(policy)
        (destination / f"{name}.json").write_text(json.dumps(policy), encoding="utf-8")
    for epoch, calendar in (("1900", CALENDAR_WINDOWS_1900), ("1904", CALENDAR_MAC_1904)):
        book = Workbook()
        book.epoch = calendar
        sheet = book.active
        sheet.title = "Holdings O'Brien"
        rows = [
            ["portfolio", "ticker", "weight", "market_value", "nav", "date"],
            ["Alpha", "AAA", 0.4, -400, 1000, datetime(2026, 1, 1)],
            ["Alpha", "BBB", 0.6, 600, 1000, datetime(2026, 1, 1)],
            ["Totals", None, None, -99999, None, None],
        ]
        for r, row in enumerate(rows, 7):
            for c, value in enumerate(row, 3):
                sheet.cell(r, c, value)
        for r in (8, 9):
            sheet.cell(r, 5).number_format = "0.0%"
            sheet.cell(r, 8).number_format = "yyyy-mm-dd"
        sheet.row_dimensions[9].hidden = True
        table = Table(displayName="AcceptanceHoldings", ref="C7:H10", totalsRowCount=1)
        table._initialise_columns()
        for column, name in zip(table.tableColumns, rows[0], strict=True):
            column.name = name
        table.autoFilter = AutoFilter(ref="C7:H9")
        table.tableColumns[0].totalsRowLabel = "Totals"
        table.tableColumns[3].totalsRowLabel = "-99999"
        table.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
        sheet.add_table(table)
        sheet.freeze_panes = "C8"
        for column in "CDEFGH":
            sheet.column_dimensions[column].width = 20
        for name, values in (
            ("Ambiguous", [["id", "value"], [999, -1], [999, -2]]),
            (
                "Missing",
                [["entity", "ccy", "start", "end"], ["A", "USD", "2026-10-01", "2026-10-08"]],
            ),
            ("Formula", [["id", "value"], ["error", "=NA()"], ["ok", "=1+1"]]),
            ("finassert results", [["Unrelated output-name collision; preserve me", 42]]),
        ):
            target = book.create_sheet(name)
            for row in values:
                target.append(row)
        policy_sheet = book.create_sheet("finassert policy")
        for row in policy_sheet_rows(get_template("long-only-holdings").to_yaml()):
            policy_sheet.append(row)
        book.save(destination / f"holdings-{epoch}.xlsx")
    manifest = {
        path.name: {
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "size_bytes": path.stat().st_size,
        }
        for path in sorted(destination.iterdir())
        if path.is_file() and path.name != "identities.json"
    }
    (destination / "identities.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    prepare(Path(sys.argv[1]))
