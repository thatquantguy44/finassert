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

Only apply `non_negative` to fields, such as a long-only gross market value
policy, where negatives are economically invalid.
