"""Strict validation of policy documents into executable rules."""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from types import MappingProxyType
from typing import Any

from finassert.core.engine import check
from finassert.core.exceptions import PolicyError
from finassert.core.models import ValidationReport
from finassert.core.protocols import Rule
from finassert.numerical import Tolerance
from finassert.policy.catalog import (
    ParameterKind,
    ParameterSpec,
    RuleCatalog,
    RuleFactorySpec,
    default_catalog,
)
from finassert.policy.issues import PolicyIssue, PolicyPath, closest, line_for

SUPPORTED_VERSIONS = (1,)
_TOP_LEVEL_KEYS = ("version", "name", "description", "assumptions", "rules")
_TOLERANCE_KEYS = ("absolute", "relative")
_DECIMAL_TEXT = re.compile(r"^[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?$")


@dataclass(frozen=True, slots=True)
class PolicyRule:
    """One resolved policy entry.

    Args:
        factory: Canonical factory name.
        parameters: Parameters exactly as supplied, after type validation.
        rule: Configured rule instance.
    """

    factory: str
    parameters: Mapping[str, Any]
    rule: Rule

    def to_document(self) -> dict[str, Any]:
        """Return the entry as it would be written in a policy file."""
        return {"rule": self.factory, **self.parameters}


@dataclass(frozen=True, slots=True)
class Policy:
    """A validated, versioned collection of configured rules.

    ``Policy`` objects are created by :func:`parse_policy` or the loaders in
    :mod:`finassert.policy`; every field reflects the document that was read.
    """

    version: int
    entries: tuple[PolicyRule, ...]
    name: str | None = None
    description: str | None = None
    assumptions: tuple[str, ...] = ()
    catalog: RuleCatalog = field(default_factory=default_catalog, repr=False, compare=False)

    @property
    def rules(self) -> tuple[Rule, ...]:
        """Return configured rules in policy order."""
        return tuple(entry.rule for entry in self.entries)

    @property
    def digest(self) -> str:
        """Return a SHA-256 digest of the canonical policy document."""
        canonical = json.dumps(
            self.to_document(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
            default=_canonical_value,
        )
        return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def check(self, data: Any, *, raise_on_error: bool = False) -> ValidationReport:
        """Evaluate this policy's rules against ``data`` with :func:`finassert.check`."""
        return check(data, self.rules, raise_on_error=raise_on_error)

    def to_document(self) -> dict[str, Any]:
        """Return the policy as a document accepted by :func:`parse_policy`."""
        document: dict[str, Any] = {"version": self.version}
        if self.name is not None:
            document["name"] = self.name
        if self.description is not None:
            document["description"] = self.description
        if self.assumptions:
            document["assumptions"] = list(self.assumptions)
        document["rules"] = [entry.to_document() for entry in self.entries]
        return document

    def describe(self) -> dict[str, Any]:
        """Return JSON-compatible policy context for report artifacts."""
        return {
            "name": self.name,
            "description": self.description,
            "assumptions": list(self.assumptions),
            "version": self.version,
            "digest": self.digest,
            "rules": [
                {
                    "rule_id": entry.rule.rule_id,
                    "factory": entry.factory,
                    "title": self.catalog.resolve(entry.factory).title,
                    "summary": self.catalog.resolve(entry.factory).summary,
                }
                for entry in self.entries
            ],
        }


def parse_policy(
    document: Any,
    *,
    catalog: RuleCatalog | None = None,
    lines: Mapping[PolicyPath, int] | None = None,
) -> Policy:
    """Validate a policy document and construct its rules.

    Every problem is collected before raising so a user can fix them together.
    Nothing is corrected automatically.

    Args:
        document: Parsed policy, such as the result of reading YAML or JSON.
            Quoted numeric text in tolerances and numbers becomes ``Decimal``.
        catalog: Allowlisted factories; defaults to :func:`default_catalog`.
        lines: Optional source line for each document path, used in issues.

    Raises:
        PolicyError: If the document is not a valid policy.
    """
    catalog = catalog or default_catalog()
    issues = _Issues(lines)
    if not isinstance(document, Mapping):
        issues.add((), "A policy must be a set of named settings starting with 'version: 1'.")
        raise PolicyError(issues.items)

    for key in document:
        if key not in _TOP_LEVEL_KEYS:
            issues.add(
                (str(key),),
                f"Unknown setting {key!r}. Allowed settings: {', '.join(_TOP_LEVEL_KEYS)}.",
                suggestion=closest(key, _TOP_LEVEL_KEYS),
            )

    version = document.get("version")
    if "version" not in document:
        issues.add((), "Missing 'version'. Add 'version: 1' at the top of the policy.")
    elif type(version) is not int or version not in SUPPORTED_VERSIONS:
        supported = ", ".join(str(item) for item in SUPPORTED_VERSIONS)
        issues.add(("version",), f"Unsupported version {version!r}; supported: {supported}.")

    name = _optional_text(document, "name", issues)
    description = _optional_text(document, "description", issues)
    assumptions = _assumptions(document.get("assumptions"), issues)

    entries: list[PolicyRule] = []
    raw_rules = document.get("rules")
    if "rules" not in document:
        issues.add((), "Missing 'rules'. Add a 'rules:' list naming at least one check.")
    elif not isinstance(raw_rules, list):
        issues.add(("rules",), "'rules' must be a list of checks, each starting with '- rule:'.")
    else:
        for index, raw_entry in enumerate(raw_rules):
            entry = _entry(index, raw_entry, catalog, issues)
            if entry is not None:
                entries.append(entry)

    if issues.items:
        raise PolicyError(issues.items)
    assert isinstance(version, int)
    return Policy(
        version=version,
        entries=tuple(entries),
        name=name,
        description=description,
        assumptions=assumptions,
        catalog=catalog,
    )


class _Issues:
    def __init__(self, lines: Mapping[PolicyPath, int] | None) -> None:
        self._lines = lines
        self._items: list[PolicyIssue] = []

    @property
    def items(self) -> tuple[PolicyIssue, ...]:
        return tuple(self._items)

    def add(self, path: PolicyPath, message: str, *, suggestion: str | None = None) -> None:
        self._items.append(
            PolicyIssue(
                path=path,
                message=message,
                line=line_for(path, self._lines),
                suggestion=suggestion,
            )
        )


def _optional_text(document: Mapping[str, Any], key: str, issues: _Issues) -> str | None:
    value = document.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        issues.add((key,), f"'{key}' must be text.")
        return None
    return value


def _assumptions(value: Any, issues: _Issues) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        issues.add(("assumptions",), "'assumptions' must be a list of sentences.")
        return ()
    for index, item in enumerate(value):
        if not isinstance(item, str):
            issues.add(("assumptions", index), "Each assumption must be text.")
    return tuple(item for item in value if isinstance(item, str))


def _entry(
    index: int,
    raw_entry: Any,
    catalog: RuleCatalog,
    issues: _Issues,
) -> PolicyRule | None:
    path: PolicyPath = ("rules", index)
    if not isinstance(raw_entry, Mapping):
        issues.add(path, "Each check must be a set of settings starting with 'rule:'.")
        return None
    reference = raw_entry.get("rule")
    if "rule" not in raw_entry:
        issues.add(path, "Missing 'rule'. Name the check to run, for example 'rule: non_negative'.")
        return None
    if not isinstance(reference, str):
        issues.add((*path, "rule"), "'rule' must be the name of a check.")
        return None
    try:
        spec = catalog.resolve(reference)
    except KeyError:
        known = ", ".join(catalog.names())
        issues.add(
            (*path, "rule"),
            f"Unknown rule {reference!r}. Available rules: {known}.",
            suggestion=closest(reference, catalog.references()),
        )
        return None

    count_before = len(issues.items)
    accepted = [parameter.name for parameter in spec.parameters]
    parameters: dict[str, Any] = {}
    for key, value in raw_entry.items():
        if key == "rule":
            continue
        if key not in accepted:
            issues.add(
                (*path, str(key)),
                f"Rule {spec.name!r} has no setting {key!r}. Its settings: {', '.join(accepted)}.",
                suggestion=closest(key, accepted),
            )
            continue
        parameter = spec.parameter(key)
        normalized = _parameter_value(parameter, value, (*path, key), issues)
        if normalized is not _INVALID:
            parameters[key] = normalized
    for parameter in spec.parameters:
        if parameter.required and parameter.name not in raw_entry:
            issues.add(
                path,
                f"Rule {spec.name!r} needs '{parameter.name}': {parameter.description}",
            )
    if len(issues.items) != count_before:
        return None
    try:
        rule = spec.factory(**_factory_arguments(parameters))
    except (TypeError, ValueError) as exc:
        issues.add(path, f"Rule {spec.name!r} could not be configured: {exc}")
        return None
    return _resolved(spec, parameters, rule)


def _resolved(spec: RuleFactorySpec, parameters: dict[str, Any], rule: Rule) -> PolicyRule:
    return PolicyRule(factory=spec.name, parameters=MappingProxyType(parameters), rule=rule)


_INVALID = object()


def _parameter_value(
    parameter: ParameterSpec,
    value: Any,
    path: PolicyPath,
    issues: _Issues,
) -> Any:
    if parameter.kind is ParameterKind.TEXT:
        if not isinstance(value, str) or not value.strip():
            issues.add(path, f"'{parameter.name}' must be nonempty text.")
            return _INVALID
        return value
    if parameter.kind is ParameterKind.RECORDS:
        if (
            not isinstance(value, list)
            or not value
            or not all(
                isinstance(item, dict)
                and item
                and all(
                    isinstance(key, str) and key.strip() and isinstance(cell, str) and cell.strip()
                    for key, cell in item.items()
                )
                for item in value
            )
        ):
            issues.add(path, f"'{parameter.name}' must be a nonempty list of text mappings.")
            return _INVALID
        return [dict(item) for item in value]
    if parameter.kind is ParameterKind.COLUMN:
        if not isinstance(value, str) or not value.strip():
            issues.add(path, f"'{parameter.name}' must be a column name written as text.")
            return _INVALID
        return value
    if parameter.kind is ParameterKind.COLUMNS:
        if not isinstance(value, list) or not all(
            isinstance(item, str) and item.strip() for item in value
        ):
            issues.add(path, f"'{parameter.name}' must be a list of column names.")
            return _INVALID
        if len(set(value)) != len(value):
            issues.add(path, f"'{parameter.name}' names a column more than once.")
            return _INVALID
        return list(value)
    if parameter.kind is ParameterKind.CHOICE:
        if not isinstance(value, str) or value not in parameter.choices:
            issues.add(
                path,
                f"'{parameter.name}' must be one of: {', '.join(parameter.choices)}.",
                suggestion=closest(value, parameter.choices),
            )
            return _INVALID
        return value
    if parameter.kind is ParameterKind.INTEGER:
        if type(value) is not int:
            issues.add(path, f"'{parameter.name}' must be a whole number.")
            return _INVALID
        if parameter.minimum is not None and value < parameter.minimum:
            issues.add(path, f"'{parameter.name}' must be at least {parameter.minimum}.")
            return _INVALID
        return value
    if parameter.kind is ParameterKind.NUMBER:
        return _number(
            value,
            path,
            issues,
            subject=f"'{parameter.name}'",
            allow_negative=parameter.allow_negative,
        )
    return _tolerance_value(parameter, value, path, issues)


def _tolerance_value(
    parameter: ParameterSpec,
    value: Any,
    path: PolicyPath,
    issues: _Issues,
) -> Any:
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if key not in _TOLERANCE_KEYS:
                issues.add(
                    (*path, str(key)),
                    f"Unknown tolerance setting {key!r}; use 'absolute' and/or 'relative'.",
                    suggestion=closest(key, _TOLERANCE_KEYS),
                )
                continue
            number = _number(item, (*path, key), issues)
            if number is not _INVALID:
                result[key] = number
        if not parameter.allow_relative and result.get("relative", 0) != 0:
            issues.add(
                (*path, "relative"),
                f"'{parameter.name}' for this rule supports only an absolute amount.",
            )
            return _INVALID
        return result
    return _number(value, path, issues)


def _number(
    value: Any,
    path: PolicyPath,
    issues: _Issues,
    *,
    subject: str = "A tolerance",
    allow_negative: bool = False,
) -> Any:
    """Read a plain number: quoted decimal text stays exact, bare numbers keep their type."""
    number: Any
    if isinstance(value, str):
        text = value.strip()
        if not _DECIMAL_TEXT.match(text):
            issues.add(
                path,
                f'{value!r} is not a plain number. Write digits only, such as "0.0001"; '
                "commas, percent signs, and currency symbols are not accepted.",
            )
            return _INVALID
        try:
            number = Decimal(text)
        except InvalidOperation:  # pragma: no cover - guarded by the pattern
            issues.add(path, f"{value!r} is not a valid number.")
            return _INVALID
    elif type(value) in (int, float):
        number = value
        if isinstance(value, float) and not math.isfinite(value):
            issues.add(path, f"{subject} must be a finite number.")
            return _INVALID
    else:
        example = '"1.25"' if allow_negative else '"0.0001"'
        issues.add(path, f"{subject} must be a number, such as {example}.")
        return _INVALID
    if number < 0 and not allow_negative:
        issues.add(path, f"{subject} cannot be negative.")
        return _INVALID
    return number


def _factory_arguments(parameters: Mapping[str, Any]) -> dict[str, Any]:
    arguments: dict[str, Any] = {}
    for key, value in parameters.items():
        if isinstance(value, Mapping):
            arguments[key] = Tolerance(**value)
        else:
            arguments[key] = value
    return arguments


def _canonical_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return {"$decimal": str(value)}
    if isinstance(value, Mapping):
        return dict(value)
    raise TypeError(f"cannot canonicalize {type(value).__name__}")
