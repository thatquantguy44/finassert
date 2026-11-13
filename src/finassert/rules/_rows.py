"""Check each row on its own for rules that relate columns within a row."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any, Protocol

from finassert.adapters._column import extract_columns
from finassert.core.models import Outcome, ValidationResult
from finassert.numerical import Numeric, is_finite
from finassert.rules._helpers import is_blank
from finassert.rules.base import NullPolicy

RowCheck = Callable[[dict[str, Numeric]], dict[str, Any] | None]


class RowRule(Protocol):
    """What :func:`evaluate_rows` needs from a rule."""

    @property
    def null_policy(self) -> NullPolicy: ...

    @property
    def max_violations(self) -> int: ...

    def _row_result(
        self,
        outcome: Outcome,
        message: str,
        metadata: dict[str, Any],
        *,
        observed: Any = None,
        expected: Any = None,
    ) -> ValidationResult: ...


def evaluate_rows(
    rule: RowRule,
    data: Any,
    columns: Mapping[str, str],
    check: RowCheck,
    *,
    row_key: str | None,
    noun: str,
    description: dict[str, Any],
) -> ValidationResult:
    """Apply ``check`` to every row whose named columns are all numbers.

    ``columns`` maps each semantic field to its column. ``check`` receives the
    row's values by semantic name and returns ``None`` when the row passes, or a
    dict describing the failure. A row with a blank or non-numeric value cannot
    be checked: the result fails, or skips when ``null_policy`` is ``skip`` and
    the only problems are blanks. Blanks are never read as zero.

    Args:
        rule: The rule producing the result.
        data: Any supported input.
        columns: Semantic field name to physical column.
        check: Per-row test.
        row_key: Optional column whose values label rows in the report.
        noun: What a row is called in messages, such as ``"position"``.
        description: Facts recorded in the result's metadata.
    """
    names = list(columns.values())
    extracted, labels = extract_columns(data, names, row_key=row_key)
    context = {**description, "row_count": len(labels)}
    if not labels:
        return rule._row_result(Outcome.SKIPPED, "The file has no rows to check.", context)

    unusable: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []
    checked = 0
    for position, label in enumerate(labels):
        values: dict[str, Numeric] = {}
        blank: list[str] = []
        invalid: list[str] = []
        for semantic, column in columns.items():
            value = extracted[column][position]
            if is_blank(value):
                blank.append(semantic)
            elif not is_finite(value):
                invalid.append(semantic)
            else:
                values[semantic] = value
        if blank or invalid:
            entry: dict[str, Any] = {"row": label}
            if blank:
                entry["blank"] = blank
            if invalid:
                entry["invalid"] = invalid
            unusable.append(entry)
            continue
        checked += 1
        failure = check(values)
        if failure is not None:
            failed.append({"row": label, **failure})

    limit = rule.max_violations
    if unusable:
        only_blanks = all("invalid" not in item for item in unusable)
        if only_blanks and rule.null_policy is NullPolicy.SKIP:
            return rule._row_result(
                Outcome.SKIPPED,
                f"Skipped because {len(unusable)} row(s) have blank values.",
                {**context, "blank_rows": unusable[:limit]},
            )
        return rule._row_result(
            Outcome.FAILED,
            f"{len(unusable)} row(s) have blank or non-numeric values, so they cannot be checked.",
            {
                **context,
                "unusable_row_count": len(unusable),
                "unusable_rows": unusable[:limit],
                "unusable_rows_truncated": len(unusable) > limit,
            },
        )
    message = (
        f"{len(failed)} of {checked} {noun}(s) fail the check."
        if failed
        else f"All {checked} {noun}(s) pass the check."
    )
    return rule._row_result(
        Outcome.FAILED if failed else Outcome.PASSED,
        message,
        {
            **context,
            "checked_count": checked,
            "failed_count": len(failed),
            "failed_rows": failed[:limit],
            "failed_rows_truncated": len(failed) > limit,
        },
        observed=len(failed),
        expected=0,
    )
