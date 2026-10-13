"""Suggest which template fits a data file, and which column plays which part.

Templates name the columns they expect (``market_value``, ``closing_balance``).
Real files call them ``Mkt Val`` or ``Ending Balance``. This module proposes a
match for each expected column from the file's headers so a person can confirm
it, instead of editing every column name by hand.

Matching is deliberately conservative and always explains itself:

* a header equal to the expected name (ignoring case and punctuation) is an
  ``exact`` match;
* a header equal to a well-known name for the same concept (``qty`` for
  ``quantity``) is a ``known name``;
* a header that contains a multi-word known name (``Market Value (Base)``) is
  ``contains``, and the one with the fewest extra words wins;
* a header one or two typos away from a known name is ``similar``.

When two headers fit equally well, or two expected columns want the same
header, nothing is chosen and the candidates are listed. Nothing is ever
applied silently: the result is a proposal for a person to confirm.
"""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any

from finassert.policy.catalog import ParameterKind, RuleCatalog, default_catalog
from finassert.policy.templates import PolicyTemplate, _thaw, policy_templates

EXACT = "exact"
KNOWN = "known name"
CONTAINS = "contains"
SIMILAR = "similar"
_TIERS = (EXACT, KNOWN, CONTAINS, SIMILAR)

_SIMILARITY = 0.88
_MIN_SIMILAR_LENGTH = 6

# Each concept lists, separated by "|", the names people give a column of that
# kind. Names are plain words; matching ignores case, punctuation, and camelCase.
_CONCEPTS: dict[str, str] = {
    "portfolio": (
        "portfolio|fund|account|acct|book|strategy|mandate|portfolio code|portfolio id|"
        "portfolio name|fund code|fund name|fund id|account number|account id|"
        "account name"
    ),
    "ticker": (
        "ticker|symbol|security|instrument|isin|cusip|sedol|figi|identifier|asset|"
        "security id|security name|instrument id|instrument name|security identifier|"
        "asset name"
    ),
    "weight": (
        "weight|wt|portfolio weight|weight pct|pct of nav|percent of nav|pct nav|"
        "allocation|allocation pct|pct weight"
    ),
    "target_weight": (
        "target weight|target allocation|model weight|target wt|target|tgt weight|"
        "strategic weight|target pct|target weight pct"
    ),
    "market_value": (
        "market value|mkt value|mkt val|mktval|market val|mv|value|position value|"
        "position mv|current value|market value base|market value local|mv base|"
        "mv local"
    ),
    "nav": ("nav|net asset value|fund nav|portfolio nav|total nav|net assets|nav base"),
    "quantity": (
        "quantity|qty|shares|units|nominal|quantity held|shares held|number of shares|"
        "no of shares|position size"
    ),
    "price": (
        "price|px|unit price|last price|close price|closing price|market price|"
        "price local|price base"
    ),
    "currency": ("currency|ccy|cur|curr|currency code|base currency|local currency|iso currency"),
    "date": (
        "date|as of|as of date|asof|business date|value date|trade date|valuation date|"
        "report date|position date|cob date|cob|reporting date"
    ),
    "opening_balance": (
        "opening balance|open balance|opening cash|beginning balance|begin balance|"
        "beginning cash|opening bal|open bal|start balance|previous balance|"
        "opening cash balance|beginning cash balance"
    ),
    "closing_balance": (
        "closing balance|close balance|ending balance|closing cash|end balance|"
        "ending cash|closing bal|end bal|closing cash balance|ending cash balance"
    ),
    "inflows": (
        "inflows|inflow|deposits|receipts|cash in|cash inflows|cash received|credits|total inflows"
    ),
    "outflows": (
        "outflows|outflow|withdrawals|payments|cash out|cash outflows|cash paid|debits|"
        "total outflows"
    ),
    "cash_income": (
        "cash income|interest income|interest|cash pnl|cash p l|cash income expense|"
        "interest and fees"
    ),
    "beginning_value": (
        "beginning value|begin value|opening value|start value|bmv|"
        "beginning market value|opening market value|beginning mv|start mv|value start|"
        "starting value"
    ),
    "ending_value": (
        "ending value|end value|closing value|emv|ending market value|"
        "closing market value|ending mv|end mv|value end"
    ),
    "return": (
        "return|ret|total return|reported return|period return|twr|return pct|"
        "rate of return|ror|gross return|net return|performance"
    ),
}


def normalize(name: object) -> str:
    """Return a header as lower-case words: ``"Mkt_Val (USD)"`` becomes ``"mkt val usd"``."""
    text = str(name).replace("%", " pct ")
    text = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", text)
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text.lower()).split())


def _build_index() -> tuple[dict[str, str], dict[str, tuple[str, ...]]]:
    owners: dict[str, str] = {}
    names: dict[str, tuple[str, ...]] = {}
    for concept, aliases in _CONCEPTS.items():
        words = [normalize(concept), *map(normalize, aliases.split("|"))]
        normalized = tuple(dict.fromkeys(words))
        names[concept] = normalized
        for alias in normalized:
            if owners.setdefault(alias, concept) != concept:
                raise AssertionError(f"{alias!r} names two concepts")  # pragma: no cover
    return owners, names


_OWNER, _NAMES = _build_index()


@dataclass(frozen=True, slots=True)
class ColumnMatch:
    """What a template's expected column was matched to in a data file.

    Attributes:
        expected: The column name the template uses.
        column: The file's header chosen for it, or ``None``.
        how: ``"exact"``, ``"known name"``, ``"contains"``, or ``"similar"``;
            ``None`` when no column was chosen.
        candidates: Headers that fit equally well when the choice was ambiguous.
    """

    expected: str
    column: str | None
    how: str | None = None
    candidates: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible description."""
        return {
            "expected": self.expected,
            "column": self.column,
            "how": self.how,
            "candidates": list(self.candidates),
        }

    @property
    def sentence(self) -> str:
        """Return the match in plain words."""
        if self.column is not None:
            return f"'{self.expected}' is your column '{self.column}' ({self.how} match)"
        if self.candidates:
            options = ", ".join(f"'{item}'" for item in self.candidates)
            return f"'{self.expected}' could be any of {options}; choose one"
        return f"no column in your file matches '{self.expected}'"


@dataclass(frozen=True, slots=True)
class TemplateFit:
    """How well a template's expected columns match a file's headers.

    Attributes:
        template: The template as written.
        matches: One entry per distinct column the template expects.
    """

    template: PolicyTemplate
    matches: tuple[ColumnMatch, ...]

    @property
    def matched(self) -> tuple[ColumnMatch, ...]:
        """Return the matches that chose a column."""
        return tuple(match for match in self.matches if match.column is not None)

    @property
    def fraction(self) -> float:
        """Return the share of expected columns that were matched."""
        return len(self.matched) / len(self.matches) if self.matches else 0.0

    def adapted(self) -> PolicyTemplate:
        """Return the template with matched columns renamed to the file's headers.

        Unmatched columns keep the template's name, and the adaptation notes say
        what to confirm and what to fix, so the proposal is never silent.
        """
        mapping = {match.expected: match.column for match in self.matched}
        notes: list[str] = []
        renamed = [match for match in self.matched if match.column != match.expected]
        if renamed:
            notes.append(
                "Confirm the columns finassert matched from your file: "
                + "; ".join(match.sentence for match in renamed)
                + "."
            )
        notes += [f"Fix this before running: {m.sentence}." for m in self.matches if not m.column]
        document = _rename(_thaw(self.template.document), mapping, default_catalog())
        return PolicyTemplate(
            name=self.template.name,
            title=self.template.title,
            summary=self.template.summary,
            adapt=(*notes, *self.template.adapt),
            document=document,
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible description, including the adapted policy."""
        adapted = self.adapted()
        return {
            "name": self.template.name,
            "title": self.template.title,
            "summary": self.template.summary,
            "matched": len(self.matched),
            "expected": len(self.matches),
            "matches": [match.to_dict() for match in self.matches],
            "adapt": list(adapted.adapt),
            "document": _thaw(adapted.document),
        }


def expected_columns(document: Any, catalog: RuleCatalog | None = None) -> tuple[str, ...]:
    """Return the distinct column names a policy document refers to, in order."""
    found: dict[str, None] = {}
    _walk(document, catalog or default_catalog(), lambda name: found.setdefault(name))
    return tuple(found)


def _rename(document: Any, mapping: dict[str, str | None], catalog: RuleCatalog) -> Any:
    result = _thaw(document)
    _walk(result, catalog, None, mapping)
    return result


def _walk(
    document: Any,
    catalog: RuleCatalog,
    visit: Any,
    mapping: dict[str, str | None] | None = None,
) -> None:
    for entry in document.get("rules", []):
        try:
            spec = catalog.resolve(entry["rule"])
        except KeyError:
            continue
        for key, value in list(entry.items()):
            if key == "rule":
                continue
            try:
                kind = spec.parameter(key).kind
            except KeyError:
                continue
            if kind is ParameterKind.COLUMN and isinstance(value, str):
                if mapping is None:
                    visit(value)
                elif mapping.get(value):
                    entry[key] = mapping[value]
            elif kind is ParameterKind.COLUMNS and isinstance(value, list):
                for position, item in enumerate(value):
                    if mapping is None:
                        visit(item)
                    elif mapping.get(item):
                        value[position] = mapping[item]


def _candidates(expected: str, headers: Sequence[str]) -> tuple[int, list[tuple[str, int]]]:
    """Return the best match tier and the headers at that tier with their extra-word counts."""
    target = normalize(expected)
    concept = _OWNER.get(target)
    aliases = _NAMES[concept] if concept else (target,)
    best = len(_TIERS)
    found: list[tuple[str, int]] = []
    for header in headers:
        words = normalize(header)
        if not words:
            continue
        tier, extra = _score(words, target, aliases)
        if tier is None:
            continue
        if tier < best:
            best, found = tier, []
        if tier == best:
            found.append((header, extra))
    return best, found


def _score(words: str, target: str, aliases: tuple[str, ...]) -> tuple[int | None, int]:
    if words == target:
        return 0, 0
    if words in aliases:
        return 1, 0
    tokens = set(words.split())
    contained = [
        len(tokens) - len(alias.split())
        for alias in aliases
        if len(alias.split()) > 1 and set(alias.split()) <= tokens
    ]
    if contained:
        return 2, min(contained)
    if len(words) >= _MIN_SIMILAR_LENGTH and any(
        len(alias) >= _MIN_SIMILAR_LENGTH
        and SequenceMatcher(None, words, alias).ratio() >= _SIMILARITY
        for alias in aliases
    ):
        return 3, 0
    return None, 0


def match_columns(expected: Iterable[str], headers: Sequence[str]) -> tuple[ColumnMatch, ...]:
    """Match each expected column name to at most one header, or explain why not."""
    headers = list(dict.fromkeys(str(header) for header in headers))
    choices: dict[str, ColumnMatch] = {}
    for name in dict.fromkeys(expected):
        tier, found = _candidates(name, headers)
        if not found:
            choices[name] = ColumnMatch(name, None)
            continue
        if tier == 2:
            fewest = min(extra for _, extra in found)
            found = [(header, extra) for header, extra in found if extra == fewest]
        names = tuple(header for header, _ in found)
        if len(names) == 1:
            choices[name] = ColumnMatch(name, names[0], _TIERS[tier])
        else:
            choices[name] = ColumnMatch(name, None, None, names)

    # Two expected columns may not share a header: the better match keeps it.
    claims: dict[str, list[str]] = defaultdict(list)
    for name, match in choices.items():
        if match.column is not None:
            claims[match.column].append(name)
    for header, claimants in claims.items():
        if len(claimants) < 2:
            continue
        rank = {name: _TIERS.index(choices[name].how or SIMILAR) for name in claimants}
        top = min(rank.values())
        winners = [name for name in claimants if rank[name] == top]
        for name in claimants:
            if len(winners) == 1 and name == winners[0]:
                continue
            choices[name] = ColumnMatch(name, None, None, (header,))
    return tuple(choices.values())


def fit_template(
    template: PolicyTemplate,
    columns: Sequence[str],
    *,
    catalog: RuleCatalog | None = None,
) -> TemplateFit:
    """Match one template's expected columns against a file's headers."""
    expected = expected_columns(_thaw(template.document), catalog)
    return TemplateFit(template, match_columns(expected, columns))


def suggest_templates(
    columns: Sequence[str],
    *,
    catalog: RuleCatalog | None = None,
    minimum_fraction: float = 0.5,
) -> tuple[TemplateFit, ...]:
    """Rank the built-in templates by how well they fit a file's headers.

    Templates matching fewer than ``minimum_fraction`` of their columns are left
    out. The best fit comes first; ties favor the template that matched more
    columns, then the one that sorts first by name.
    """
    fits = [fit_template(template, columns, catalog=catalog) for template in policy_templates()]
    useful = [fit for fit in fits if fit.matched and fit.fraction >= minimum_fraction]
    return tuple(
        sorted(useful, key=lambda fit: (-fit.fraction, -len(fit.matched), fit.template.name))
    )
