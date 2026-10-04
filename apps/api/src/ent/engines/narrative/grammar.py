"""Per-locale sentence grammar for examination narratives.

These fragments are narrative data (architecture §21), not UI chrome.
Feature specification §6.8: right before left, positives before negatives,
negatives grouped, not-examined omitted.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class NarrativeGrammar:
    side: dict[str, str]
    sentence: str
    clause_separator: str
    list_separator: str
    list_final: str


GRAMMAR: dict[str, NarrativeGrammar] = {
    "en": NarrativeGrammar(
        side={
            "right": "Right",
            "left": "Left",
            "midline": "Midline",
            "bilateral": "Both sides",
            "na": "Side not applicable",
        },
        sentence="{side} — {clauses}.",
        clause_separator="; ",
        list_separator=", ",
        list_final=" and ",
    ),
    "fr": NarrativeGrammar(
        side={
            "right": "À droite",
            "left": "À gauche",
            "midline": "Ligne médiane",
            "bilateral": "Des deux côtés",
            "na": "Côté non applicable",
        },
        sentence="{side} — {clauses}.",
        clause_separator=" ; ",
        list_separator=", ",
        list_final=" et ",
    ),
    # VERIFY: Arabic side labels and joiners with a clinician.
    "ar": NarrativeGrammar(
        side={
            "right": "أيمن",
            "left": "أيسر",
            "midline": "ناصف",
            "bilateral": "الجانبان",
            "na": "دون جانب",
        },
        sentence="{side} — {clauses}.",
        clause_separator="؛ ",
        list_separator="، ",
        list_final=" و",
    ),
}

NARRATIVE_LOCALES = frozenset(GRAMMAR)
