"""Adapt a deterministic function into a named rule."""

import finassert as fa

has_cash = fa.custom_rule(
    "portfolio.has_cash_record",
    "Portfolio contains a cash record",
    lambda rows: any(row["asset_class"] == "cash" for row in rows),
)
report = fa.check([{"asset_class": "equity"}, {"asset_class": "cash"}], [has_cash])
print(report.summary())
