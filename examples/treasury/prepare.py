"""Explicit synthetic-example mapping; no joining, netting, coercing nulls or defaults."""

from decimal import Decimal, localcontext
from typing import Any

from finassert.numerical import is_finite


def prepare_cash_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Copy rows and derive combined flows; input columns retain their identity."""
    prepared = []
    for row in rows:
        combined = {}
        for target, names in (
            ("total_inflows", ("receipts", "financing_inflows")),
            ("total_outflows", ("payments", "financing_outflows")),
        ):
            values = [row[name] for name in names]
            if not all(is_finite(value) and value >= 0 for value in values):
                raise ValueError(
                    f"{row.get('row_id')!r}: {names} require finite positive magnitudes"
                )
            amounts = [Decimal(str(value)) for value in values]
            with localcontext() as context:
                context.prec = max(
                    28,
                    max(a.adjusted() for a in amounts)
                    - min(int(a.as_tuple().exponent) for a in amounts)
                    + 3,
                )
                combined[target] = sum(amounts, Decimal(0))
        prepared.append({**row, **combined})
    return prepared
