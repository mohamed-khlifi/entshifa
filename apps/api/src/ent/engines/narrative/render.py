"""Order and render examination findings (feature specification §6.8)."""

from __future__ import annotations

import re
from collections.abc import Sequence

from ent.engines.narrative.grammar import GRAMMAR, NarrativeGrammar
from ent.engines.narrative.types import NarrativeFinding

VERSION = "1.1.0"
REFERENCE = (
    "Feature specification §6.8 and architecture §21: right before left, "
    "positives before negatives within a side, not-examined omitted. "
    "The report sentence groups negatives; the examination preview lists "
    "one finding per line under its side. Phrase templates are data on "
    "the finding concept."
)

_SIDE_RANK = {"right": 0, "midline": 1, "na": 2, "bilateral": 3, "left": 4}
_TOKEN = re.compile(r"\{\{([A-Za-z]+)\}\}")


class NarrativeLocaleError(Exception):
    """The locale has no narrative grammar. ``locale`` is a stable token."""

    def __init__(self, locale: str) -> None:
        self.locale = locale
        super().__init__(locale)


def render_examination_narrative(
    findings: Sequence[NarrativeFinding],
    *,
    locale: str,
) -> str:
    """Return one paragraph. Empty when every finding is not examined."""

    grammar = _grammar(locale)
    sentences: list[str] = []
    for side, group in _grouped(findings):
        clause = _side_clause(group, grammar)
        if clause:
            side_label = grammar.side.get(side, side)
            sentences.append(grammar.sentence.format(side=side_label, clauses=clause))
    return " ".join(sentences)


def render_examination_preview(
    findings: Sequence[NarrativeFinding],
    *,
    locale: str,
) -> str:
    """Return one finding per line, grouped under each side."""

    grammar = _grammar(locale)
    blocks: list[str] = []
    for side, group in _grouped(findings):
        lines = [line for line in (_phrase(item) for item in group) if line]
        if not lines:
            continue
        blocks.append("\n".join([grammar.side.get(side, side), *lines]))
    return "\n\n".join(blocks)


def _grammar(locale: str) -> NarrativeGrammar:
    grammar = GRAMMAR.get(locale)
    if grammar is None:
        raise NarrativeLocaleError(locale)
    return grammar


def _grouped(
    findings: Sequence[NarrativeFinding],
) -> list[tuple[str, list[NarrativeFinding]]]:
    visible = [item for item in findings if item.status != "not_examined"]
    ordered = sorted(visible, key=_sort_key)
    groups: list[tuple[str, list[NarrativeFinding]]] = []
    index = 0
    while index < len(ordered):
        side = ordered[index].laterality
        group: list[NarrativeFinding] = []
        while index < len(ordered) and ordered[index].laterality == side:
            group.append(ordered[index])
            index += 1
        groups.append((side, group))
    return groups


def _sort_key(item: NarrativeFinding) -> tuple[int, int, int, str]:
    polarity = 0 if item.status != "normal" else 1
    return (
        _SIDE_RANK.get(item.laterality, 9),
        polarity,
        item.sort_index,
        item.concept_code,
    )


def _side_clause(group: Sequence[NarrativeFinding], grammar: NarrativeGrammar) -> str:
    positives = [
        _phrase(item) for item in group if item.status != "normal" and _phrase(item)
    ]
    negatives = [
        _phrase(item) for item in group if item.status == "normal" and _phrase(item)
    ]
    parts: list[str] = []
    if positives:
        parts.append(grammar.clause_separator.join(positives))
    if negatives:
        parts.append(_join_group(negatives, grammar))
    return grammar.clause_separator.join(parts)


def _phrase(item: NarrativeFinding) -> str:
    template = item.phrase_template.strip()
    if not template:
        return item.body_site_label

    def replace(match: re.Match[str]) -> str:
        token = match.group(1)
        if token == "bodySite":
            return item.body_site_label
        return ""

    return _TOKEN.sub(replace, template).strip()


def _join_group(items: list[str], grammar: NarrativeGrammar) -> str:
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]}{grammar.list_final}{items[1]}"
    head = grammar.list_separator.join(items[:-1])
    return f"{head}{grammar.list_final}{items[-1]}"
