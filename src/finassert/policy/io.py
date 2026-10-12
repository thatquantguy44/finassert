"""Read and write policy files.

JSON policies need no dependency. YAML policies require the optional
``PyYAML`` package (``finassert[yaml]`` or ``finassert[cli]``); writing YAML
does not.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from decimal import Decimal
from os import PathLike
from pathlib import Path
from typing import Any

from finassert.core.exceptions import PolicyError
from finassert.policy.catalog import RuleCatalog
from finassert.policy.issues import PolicyIssue, PolicyPath
from finassert.policy.schema import Policy, parse_policy

POLICY_FORMATS = ("yaml", "json")
_PLAIN_NAME = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*$")


def load_policy(
    path: str | PathLike[str],
    *,
    catalog: RuleCatalog | None = None,
    format: str | None = None,
) -> Policy:
    """Read, validate, and resolve a policy file.

    Args:
        path: Policy file location.
        catalog: Allowlisted factories; defaults to the built-in catalog.
        format: ``"yaml"`` or ``"json"``; inferred from the file extension
            when omitted.

    Raises:
        PolicyError: If the format is unknown or the document is invalid.
        OSError: If the file cannot be read.
    """
    location = Path(path)
    resolved_format = format or policy_format_for(location)
    text = location.read_text(encoding="utf-8-sig")
    return parse_policy_text(text, format=resolved_format, catalog=catalog)


def policy_format_for(path: Path) -> str:
    """Infer a policy format from a file extension."""
    suffix = path.suffix.lower()
    if suffix in {".yml", ".yaml"}:
        return "yaml"
    if suffix == ".json":
        return "json"
    raise PolicyError(
        (
            PolicyIssue(
                (),
                f"Cannot tell the policy format of {path.name!r}; "
                "use a .yml, .yaml, or .json file.",
            ),
        )
    )


def parse_policy_text(
    text: str,
    *,
    format: str,
    catalog: RuleCatalog | None = None,
) -> Policy:
    """Parse policy source text in ``format`` and resolve its rules."""
    if format == "yaml":
        document, lines = _read_yaml(text)
    elif format == "json":
        document, lines = _read_json(text), None
    else:
        raise PolicyError(
            (PolicyIssue((), f"Unknown policy format {format!r}; use 'yaml' or 'json'."),)
        )
    return parse_policy(document, catalog=catalog, lines=lines)


def dump_policy(policy: Policy) -> str:
    """Render a policy as YAML that :func:`load_policy` reads back identically.

    Text and exact decimals are double-quoted; binary floats are written in a
    form YAML 1.1 readers still recognize as floats.
    """
    document = policy.to_document()
    lines = ["# finassert policy", f"version: {document['version']}"]
    for key in ("name", "description"):
        if key in document:
            lines.append(f"{key}: {_scalar(document[key])}")
    if "assumptions" in document:
        lines.append("assumptions:")
        lines.extend(f"  - {_scalar(item)}" for item in document["assumptions"])
    if not document["rules"]:
        lines.append("rules: []")
    else:
        lines.append("rules:")
        for entry in document["rules"]:
            lines.append(f"  - rule: {_key_text(entry['rule'])}")
            for key, value in entry.items():
                if key == "rule":
                    continue
                if isinstance(value, Mapping):
                    lines.append(f"    {key}:")
                    lines.extend(f"      {inner}: {_scalar(item)}" for inner, item in value.items())
                else:
                    lines.append(f"    {key}: {_scalar(value)}")
    return "\n".join(lines) + "\n"


def _scalar(value: Any) -> str:
    if isinstance(value, bool) or value is None:
        raise TypeError("policies do not contain boolean or null values")
    if isinstance(value, Decimal):
        return json.dumps(str(value))
    if isinstance(value, float):
        return _yaml_float(value)
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return json.dumps(value)
    raise TypeError(f"cannot write {type(value).__name__} to a policy")


def _key_text(value: str) -> str:
    return value if _PLAIN_NAME.match(value) else _scalar(value)


def _yaml_float(value: float) -> str:
    # YAML 1.1 (PyYAML) needs a dot in the mantissa and a signed exponent.
    text = repr(value)
    if "e" in text:
        mantissa, exponent = text.split("e")
        if "." not in mantissa:
            mantissa += ".0"
        if exponent[0] not in "+-":
            exponent = "+" + exponent
        return f"{mantissa}e{exponent}"
    return text


def _read_json(text: str) -> Any:
    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise PolicyError(
                    (PolicyIssue((key,), f"Setting {key!r} appears more than once."),)
                )
            result[key] = value
        return result

    try:
        return json.loads(text, object_pairs_hook=unique_object)
    except json.JSONDecodeError as exc:
        raise PolicyError(
            (PolicyIssue((), f"The file is not valid JSON: {exc.msg}.", line=exc.lineno),)
        ) from exc


def _read_yaml(text: str) -> tuple[Any, dict[PolicyPath, int]]:
    try:
        import yaml
    except ImportError as exc:
        raise PolicyError(
            (
                PolicyIssue(
                    (),
                    "Reading YAML policies needs PyYAML. Install 'finassert[cli]' "
                    "or use a .json policy.",
                ),
            )
        ) from exc

    loader = yaml.SafeLoader(text)
    try:
        node = loader.get_single_node()
        if node is None:
            raise PolicyError((PolicyIssue((), "The policy file is empty."),))
        lines: dict[PolicyPath, int] = {}
        duplicates: list[PolicyIssue] = []
        _index_nodes(node, (), lines, duplicates)
        if duplicates:
            raise PolicyError(tuple(duplicates))
        document = loader.construct_document(node)
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        problem = getattr(exc, "problem", None) or str(exc)
        raise PolicyError(
            (
                PolicyIssue(
                    (),
                    f"The file is not valid YAML: {problem}.",
                    line=None if mark is None else mark.line + 1,
                ),
            )
        ) from exc
    finally:
        loader.dispose()
    return document, lines


def _index_nodes(
    node: Any,
    path: PolicyPath,
    lines: dict[PolicyPath, int],
    duplicates: list[PolicyIssue],
) -> None:
    import yaml

    if isinstance(node, yaml.MappingNode):
        seen: set[str] = set()
        for key_node, value_node in node.value:
            key = key_node.value if isinstance(key_node, yaml.ScalarNode) else str(key_node)
            line = key_node.start_mark.line + 1
            child: PolicyPath = (*path, key)
            if key in seen:
                duplicates.append(
                    PolicyIssue(child, f"Setting {key!r} appears more than once.", line=line)
                )
            seen.add(key)
            lines[child] = line
            _index_nodes(value_node, child, lines, duplicates)
    elif isinstance(node, yaml.SequenceNode):
        for index, item in enumerate(node.value):
            child = (*path, index)
            lines[child] = item.start_mark.line + 1
            _index_nodes(item, child, lines, duplicates)
