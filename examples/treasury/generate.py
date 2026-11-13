"""Regenerate deterministic synthetic treasury fixtures, with no real book data."""

from __future__ import annotations

import csv
import json
from datetime import date, timedelta
from decimal import Decimal
from itertools import product
from pathlib import Path
from typing import Any

from finassert.policy import dump_policy, parse_policy

ROOT = Path(__file__).resolve().parent


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    """Write a fixture with fixed column and row order."""
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    """Write sixteen independent series and small reproducible failure recipes."""
    scope = [
        {
            "forecast_as_of": vintage,
            "entity_id": entity,
            "currency": currency,
            "scenario_id": scenario,
        }
        for vintage, entity, currency, scenario in product(
            ["2026-10-01", "2026-10-02"],
            ["Alpha", "Beta"],
            ["USD", "EUR"],
            ["base", "downside"],
        )
    ]
    anchor = date(2026, 10, 5)
    cash: list[dict[str, Any]] = []
    facilities: list[dict[str, Any]] = []
    for group_index, group in enumerate(scope):
        opening, drawn = Decimal("1000.00"), Decimal("100.00")
        for week in range(13):
            start = (anchor + timedelta(days=7 * week)).isoformat()
            end = (anchor + timedelta(days=7 * (week + 1))).isoformat()
            receipts = Decimal("20.00") if group["scenario_id"] == "base" else Decimal("10.00")
            payment, draw = Decimal("30.00"), Decimal("5.00")
            closing = opening + receipts - payment + draw
            cash.append(
                {
                    "row_id": f"cash-{group_index:02}-{week:02}",
                    **group,
                    "period_start": start,
                    "period_end": end,
                    "opening_cash": opening,
                    "receipts": receipts,
                    "payments": payment,
                    "financing_inflows": draw,
                    "financing_outflows": Decimal("0.00"),
                    "cash_adjustments": Decimal("0.00"),
                    "closing_cash": closing,
                    "restricted_cash": Decimal("10.00"),
                    "minimum_buffer": Decimal("500.00"),
                }
            )
            facilities.append(
                {
                    "row_id": f"facility-{group_index:02}-{week:02}",
                    **group,
                    "facility_id": "revolver",
                    "period_start": start,
                    "period_end": end,
                    "opening_drawn": drawn,
                    "draws": draw,
                    "repayments": Decimal("0.00"),
                    "closing_drawn": drawn + draw,
                    "commitment": Decimal("1000.00"),
                    "unavailable_amount": Decimal("0.00"),
                    "maturity_date": "2028-01-01",
                }
            )
            opening, drawn = closing, drawn + draw
    write_csv(ROOT / "cash-forecast.csv", cash)
    write_csv(ROOT / "facilities.csv", facilities)
    (ROOT / "expected-scope.json").write_text(json.dumps(scope, indent=2) + "\n")
    common = {
        "period_start": "period_start",
        "period_end": "period_end",
        "group_by": ["forecast_as_of", "entity_id", "scenario_id"],
        "currency": "currency",
        "expected_scope": scope,
        "first_period": anchor.isoformat(),
        "periods": 13,
        "row_key": "row_id",
    }
    policy = parse_policy(
        {
            "version": 1,
            "name": "Synthetic 13-week coverage and continuity",
            "assumptions": [
                "Synthetic amounts in currency major units, with no conversion or netting.",
                "One row per vintage/entity/currency/scenario/calendar week; end is exclusive.",
                "Expected scope includes series absent from the input.",
                "Payments are positive magnitudes; receipts/payments exclude financing flows.",
                "This policy checks coverage and continuity only, not liquidity or capacity.",
            ],
            "rules": [
                {"rule": "forecast_coverage", **common},
                {
                    "rule": "cash_continuity",
                    **common,
                    "opening_cash": "opening_cash",
                    "closing_cash": "closing_cash",
                    "tolerance": "0.01",
                    "null_policy": "fail",
                },
            ],
        }
    )
    (ROOT / "policy.yml").write_text(dump_policy(policy))
    cases = [
        {
            "name": "missing_week",
            "dataset": "cash-forecast.csv",
            "operation": "remove",
            "row_ids": ["cash-00-05"],
            "coverage": "failed",
            "continuity": "error",
        },
        {
            "name": "missing_series",
            "dataset": "cash-forecast.csv",
            "operation": "remove",
            "row_ids": [f"cash-00-{n:02}" for n in range(13)],
            "coverage": "failed",
            "continuity": "error",
        },
        {
            "name": "duplicate_week",
            "dataset": "cash-forecast.csv",
            "operation": "duplicate",
            "row_ids": ["cash-00-05"],
            "coverage": "failed",
            "continuity": "error",
        },
        {
            "name": "disconnected_cash",
            "dataset": "cash-forecast.csv",
            "operation": "replace",
            "row_ids": ["cash-00-05"],
            "values": {"opening_cash": "900.00"},
            "coverage": "passed",
            "continuity": "failed",
        },
        {
            "name": "cash_shortfall",
            "dataset": "cash-forecast.csv",
            "operation": "replace",
            "row_ids": ["cash-00-12"],
            "values": {"minimum_buffer": "1000.00"},
            "coverage": "passed",
            "continuity": "passed",
            "future_buffer": "failed",
        },
        {
            "name": "facility_overdraw",
            "dataset": "facilities.csv",
            "operation": "replace",
            "row_ids": ["facility-00-12"],
            "values": {"commitment": "160.00"},
            "future_capacity": "failed",
        },
    ]
    (ROOT / "failure-cases.json").write_text(json.dumps(cases, indent=2) + "\n")


if __name__ == "__main__":
    main()
