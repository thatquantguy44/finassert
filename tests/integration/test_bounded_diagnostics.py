"""Compare complete results to the pre-optimization scalar implementation.

The fixture was captured on 5ec995984037f26255ee10895b4d4bb37838a179.
It fingerprints both direct rule results and normalized reports, including every
message, numeric value, label, count, truncation flag, and serialized diagnostic.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterator
from decimal import Decimal
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

import finassert as fa

REFERENCE = Path(__file__).parents[1] / "fixtures" / "bounded-diagnostics-reference.json"


def parity_cases() -> Iterator[tuple[str, dict[str, list[Any]], Any]]:
    """Exercise dense failures, blank precedence, corrupt tails and stable order."""
    for domain in ("float", "decimal"):
        number = Decimal if domain == "decimal" else float
        for cap in (0, 1, 20):
            common = {"max_violations": cap}
            for variant in ("dense", "blank", "invalid_tail", "empty", "blank_group_tail"):
                size = 0 if variant == "empty" else 64
                weights = [number((-2, 1, 3, -2)[i % 4]) for i in range(size)]
                groups: list[Any] = [f"G{i % 29:02}" for i in range(size)]
                if variant in {"blank", "invalid_tail"}:
                    weights[:23] = [None] * 23  # type: ignore[list-item]
                if variant == "invalid_tail":
                    weights[-1] = "corrupt"  # type: ignore[assignment]
                if variant == "blank_group_tail":
                    groups[-1] = None
                data = {
                    "w": weights,
                    "target": [number(0)] * size,
                    "mv": [number(1)] * size,
                    "price": [number(2)] * size,
                    "base": [number(100)] * size,
                    "group": groups,
                    "row": [("book", i % 7) for i in range(size)],
                    # A is first but becomes duplicated after B: duplicate-key
                    # order must follow first appearance, not discovery order.
                    "key": (["A", "B", "B"] + ["C"] * 58 + ["A", None, [1]])[:size],
                }
                rules = {
                    "required": fa.required_fields(columns=["w", "key"], **common),
                    "position": fa.position_within_limit(
                        value="w", base="base", maximum=number("0.001"), row_key="row", **common
                    ),
                    "match": fa.weights_match_market_values(
                        weight="w", market_value="mv", row_key="row", **common
                    ),
                    "drift": fa.drift_within_band(
                        weight="w",
                        target_weight="target",
                        band=number("0.1"),
                        total_limit=number(1),
                        row_key="row",
                        **common,
                    ),
                    "turnover": fa.turnover_within_limit(
                        weight="w",
                        previous_weight="target",
                        maximum=number(1),
                        sides="one_way",
                        row_key="row",
                        **common,
                    ),
                }
                for policy in ("fail", "ignore", "skip"):
                    options = {**common, "null_policy": policy}
                    rules.update(
                        {
                            f"nonnegative_{policy}": fa.non_negative(column="w", **options),
                            f"range_{policy}": fa.in_range(
                                column="w",
                                minimum=number(0),
                                maximum=number(1),
                                row_key="row",
                                **options,
                            ),
                            f"weights_{policy}": fa.weights_sum_to_one(column="w", **options),
                            f"grouped_{policy}": fa.weights_sum_to_one(
                                column="w", group_by=["group"], **options
                            ),
                            f"duplicates_{policy}": fa.no_duplicates(columns=["key"], **options),
                        }
                    )
                    if policy != "ignore":
                        rules[f"rows_{policy}"] = fa.market_value_reconciles(
                            quantity="w",
                            price="price",
                            market_value="mv",
                            row_key="row",
                            **options,
                        )
                for name, rule in rules.items():
                    yield f"{domain}/{cap}/{variant}/{name}", data, rule
    # Diagnostic arithmetic still runs on failures beyond the retained prefix.
    yield (
        "overflow_after_cap",
        {"w": [0.0, 1e308]},
        fa.in_range(column="w", maximum=-1e308, max_violations=1),
    )


def payload(data: Any, rule: Any) -> dict[str, Any]:
    """Include direct evaluation exceptions as well as engine error results."""
    try:
        direct = rule.evaluate(data).to_dict()
    except Exception as exc:
        direct = {"exception": type(exc).__name__, "message": str(exc)}
    return {"direct": direct, "report": fa.check(data, [rule]).to_dict()}


def fingerprint(value: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


@pytest.mark.parametrize("adapter", ["mapping", "pandas"])
@pytest.mark.parametrize("case", list(parity_cases()), ids=lambda case: case[0])
def test_complete_scalar_reference_parity(case: Any, adapter: str) -> None:
    name, data, rule = case
    expected = json.loads(REFERENCE.read_text())["fingerprints"][name]
    actual = payload(pd.DataFrame(data) if adapter == "pandas" else data, rule)
    assert fingerprint(actual) == expected, actual
