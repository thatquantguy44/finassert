"""Partition rows into groups for reconciliation rules."""

from __future__ import annotations

from collections.abc import Callable, Collection, Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol

from finassert.adapters._column import extract_columns
from finassert.adapters.contracts import ColumnMapping
from finassert.core.exceptions import GroupAggregationError, InvalidDataError
from finassert.core.models import Outcome, ValidationResult
from finassert.numerical import Numeric, is_finite
from finassert.rules._helpers import is_blank
from finassert.rules.base import NullPolicy
from finassert.rules.grouped import aggregate_ordered, order_value

_ORDER_FIELD = "order"


@dataclass(slots=True)
class Group:
    """Observations of one group, in physical row order.

    Attributes:
        identity: Group-key name to value, in declared key order.
        values: Semantic field to its present values.
        orders: Semantic field to ordering keys aligned with ``values``.
        rows: Diagnostic labels of the group's rows.
    """

    identity: dict[str, Any]
    values: dict[str, list[Numeric]]
    orders: dict[str, list[tuple[int, Any]]]
    rows: list[Any] = field(default_factory=list)

    def aggregate(self, semantic: str, mapping: ColumnMapping) -> Numeric:
        """Reduce one field with its configured aggregation."""
        return aggregate_ordered(
            self.values[semantic],
            self.orders[semantic],
            mapping.aggregation_for(semantic),
        )


@dataclass(slots=True)
class Collected:
    """Groups plus the rows that could not join one.

    Attributes:
        groups: Groups in order of first appearance.
        unusable_rows: Rows, in file order, with blank required values
            (``blank``) or non-numeric values or ordering values (``invalid``).
        row_count: Number of rows read.
    """

    groups: list[Group]
    unusable_rows: list[dict[str, Any]]
    row_count: int

    @property
    def has_blanks(self) -> bool:
        """Return whether any unusable row has a blank value."""
        return any(item.get("blank") for item in self.unusable_rows)


def collect_groups(
    data: Any,
    mapping: ColumnMapping,
    semantics: Sequence[str],
    *,
    blank_allowed: Collection[str] = (),
) -> Collected:
    """Read the mapped columns and partition rows by the mapping's group keys.

    A row with a blank group key cannot be placed, so it is an evaluation error.
    A blank value makes the row unusable unless the field is in
    ``blank_allowed``, in which case the blank is left out of that field only.
    A non-finite or non-numeric value, or an ordering value that is not a number
    or ISO date, also makes the row unusable. Unusable rows do not join a group.

    Raises:
        InvalidDataError: If a group key is blank or columns are misaligned.
        ColumnNotFoundError: If a mapped column is absent.
    """
    physical = {semantic: mapping.resolve(semantic) for semantic in semantics}
    names = [*physical.values(), *mapping.grouping_columns]
    use_order = mapping.order_key is not None and mapping.uses_ordered_aggregation
    if use_order:
        names.append(mapping.order_key)  # type: ignore[arg-type]
    columns, labels = extract_columns(data, names, row_key=mapping.row_key)

    groups: dict[tuple[Any, ...], Group] = {}
    unusable_rows: list[dict[str, Any]] = []
    for position, label in enumerate(labels):
        key = tuple(columns[group_key.column][position] for group_key in mapping.group_keys)
        if any(is_blank(value) for value in key):
            raise InvalidDataError(f"row {label!r} has a blank value in a grouping column")

        missing: list[str] = []
        invalid: list[str] = []
        present: dict[str, Numeric] = {}
        for semantic, column in physical.items():
            value = columns[column][position]
            if is_blank(value):
                if semantic not in blank_allowed:
                    missing.append(semantic)
            elif not is_finite(value):
                invalid.append(semantic)
            else:
                present[semantic] = value
        order: tuple[int, Any] = (0, 0)
        if use_order:
            raw = columns[mapping.order_key][position]  # type: ignore[index]
            if is_blank(raw):
                missing.append(_ORDER_FIELD)
            else:
                try:
                    order = order_value(raw)
                except GroupAggregationError:
                    invalid.append(_ORDER_FIELD)
        if missing or invalid:
            entry: dict[str, Any] = {"row": label}
            if missing:
                entry["blank"] = missing
            if invalid:
                entry["invalid"] = invalid
            unusable_rows.append(entry)
            continue

        group = groups.get(key)
        if group is None:
            group = Group(
                identity={
                    group_key.name: value
                    for group_key, value in zip(mapping.group_keys, key, strict=True)
                },
                values={semantic: [] for semantic in semantics},
                orders={semantic: [] for semantic in semantics},
            )
            groups[key] = group
        group.rows.append(label)
        for semantic, value in present.items():
            group.values[semantic].append(value)
            group.orders[semantic].append(order)
    return Collected(
        groups=list(groups.values()),
        unusable_rows=unusable_rows,
        row_count=len(labels),
    )


GroupCheck = Callable[[Group], dict[str, Any] | None]

_MAX_ROWS_LISTED = 20


@dataclass(frozen=True, slots=True)
class Wording:
    """Phrases a grouped rule uses in its result messages.

    Attributes:
        action: Verb for what the rule does, as in "no rows to reconcile".
        passes: Verb phrase when a group passes, as in "reconcile".
        fails: Verb phrase when a group fails, as in "do not reconcile".
        unusable: Phrase for groups with blank rows, as in "cannot be reconciled".
        file_passes: Singular of ``passes`` for a whole file, as in "reconciles".
        file_fails: Singular of ``fails`` for a whole file.
    """

    action: str
    passes: str
    fails: str
    unusable: str
    file_passes: str
    file_fails: str


class GroupedRule(Protocol):
    """What :func:`evaluate_groups` needs from a rule."""

    @property
    def mapping(self) -> ColumnMapping: ...

    @property
    def null_policy(self) -> NullPolicy: ...

    @property
    def max_violations(self) -> int: ...

    def _grouped_result(
        self,
        outcome: Outcome,
        message: str,
        metadata: dict[str, Any],
        *,
        observed: Any = None,
        expected: Any = None,
    ) -> ValidationResult: ...


def evaluate_groups(
    rule: GroupedRule,
    data: Any,
    semantics: Sequence[str],
    check: GroupCheck,
    *,
    blank_allowed: Sequence[str] = (),
    wording: Wording,
    description: dict[str, Any],
) -> ValidationResult:
    """Evaluate one grouped rule: collect groups, apply ``check`` to each, report.

    ``check`` returns ``None`` for a passing group or a dict describing the
    failure. A :class:`GroupAggregationError` raised by it becomes an
    ``inconsistent_rows`` failure of that group. Rows with blank or non-numeric
    values make the result fail, or skip it when ``null_policy`` is ``skip`` and
    only blanks are present.
    """
    collected = collect_groups(data, rule.mapping, semantics, blank_allowed=blank_allowed)
    context = {
        **description,
        "group_keys": [key.name for key in rule.mapping.group_keys],
        "row_count": collected.row_count,
    }
    if collected.row_count == 0:
        return rule._grouped_result(
            Outcome.SKIPPED,
            f"The file has no rows to {wording.action}.",
            {**context, "group_count": 0},
        )
    unusable = collected.unusable_rows
    only_blanks = all("invalid" not in item for item in unusable)
    if collected.has_blanks and only_blanks and rule.null_policy is NullPolicy.SKIP:
        # Skipping covers blanks only: a non-numeric value is corrupt data and
        # must fail even when other rows are blank.
        blank = [item for item in unusable if item.get("blank")]
        return rule._grouped_result(
            Outcome.SKIPPED,
            f"Skipped because {len(blank)} row(s) have blank values.",
            {**context, "blank_rows": blank[: rule.max_violations]},
        )
    if unusable:
        return rule._grouped_result(
            Outcome.FAILED,
            f"{len(unusable)} row(s) have blank or non-numeric values, so their groups "
            f"{wording.unusable}.",
            {
                **context,
                "unusable_row_count": len(unusable),
                "unusable_rows": unusable[: rule.max_violations],
                "unusable_rows_truncated": len(unusable) > rule.max_violations,
            },
        )

    failed: list[dict[str, Any]] = []
    for group in collected.groups:
        try:
            failure = check(group)
        except GroupAggregationError as exc:
            failure = {"reason": "inconsistent_rows", "detail": str(exc)}
        if failure is not None:
            failed.append(
                {
                    "group": group.identity,
                    **failure,
                    "row_count": len(group.rows),
                    "rows": group.rows[:_MAX_ROWS_LISTED],
                }
            )
    count = len(collected.groups)
    grouped = bool(rule.mapping.group_keys)
    noun = "group" if grouped else "file"
    if failed:
        message = (
            f"{len(failed)} of {count} {noun}(s) {wording.fails}."
            if grouped
            else f"The file {wording.file_fails}."
        )
    else:
        message = (
            f"All {count} {noun}(s) {wording.passes}."
            if grouped
            else f"The file {wording.file_passes}."
        )
    return rule._grouped_result(
        Outcome.FAILED if failed else Outcome.PASSED,
        message,
        {
            **context,
            "group_count": count,
            "failed_group_count": len(failed),
            "failed_groups": failed[: rule.max_violations],
            "failed_groups_truncated": len(failed) > rule.max_violations,
        },
        observed=len(failed),
        expected=0,
    )
