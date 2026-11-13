# Portfolio validation

Weight summation checks an allocation identity; it does not impose a long-only
constraint. Negative weights may represent valid short positions.

```python
from decimal import Decimal
import finassert as fa

data = {"weight": [Decimal("0.30"), Decimal("-0.10"), Decimal("0.80")]}
report = fa.check(data, [fa.weights_sum_to_one(tolerance=Decimal("0"))])
assert report.passed
```

When a file holds several portfolios, name the column that identifies each one
and every portfolio must add up to one:

```python
rule = fa.weights_sum_to_one(column="weight", group_by=["portfolio"], tolerance=Decimal("0.0001"))
```

Failing portfolios are listed with their totals and row numbers. See
[Holdings of several portfolios](multi-portfolio-holdings.md) for a full policy.

Only apply `non_negative` to fields, such as a long-only gross market value
policy, where negatives are economically invalid.
