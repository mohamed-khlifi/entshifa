"""Accent- and case-folded person names for clinic-scoped search.

Arabic letters are preserved so a second script stored on the same patient
stays searchable. This is not a transliteration table.
"""

from __future__ import annotations

import unicodedata

VERSION = "1.0.0"
REFERENCE = (
    "Unicode Standard Annex #15 (NFKD compatibility decomposition) and "
    "Unicode case folding. Combining marks are removed so Latin accents "
    "fold together (Bén -> ben). Non-Latin letters, including Arabic, are kept."
)

_MAX_NORMALIZED_LENGTH = 190


def fold_name_part(value: str) -> str:
    """Fold one name token for search. Empty input returns an empty string."""

    decomposed = unicodedata.normalize("NFKD", value)
    without_marks = "".join(
        character for character in decomposed if not unicodedata.combining(character)
    )
    return " ".join(without_marks.casefold().split())


def build_name_normalized(
    *,
    first_name: str,
    last_name: str,
    first_name_alt: str | None = None,
    last_name_alt: str | None = None,
) -> str:
    """Build the indexed search key from both scripts, without duplicate tokens."""

    parts: list[str] = []
    seen: set[str] = set()
    for raw in (first_name, last_name, first_name_alt, last_name_alt):
        if raw is None:
            continue
        folded = fold_name_part(raw)
        if not folded or folded in seen:
            continue
        seen.add(folded)
        parts.append(folded)
    return " ".join(parts)[:_MAX_NORMALIZED_LENGTH]


def normalize_phone(value: str | None) -> str | None:
    """Digit-only phone so formatting and a leading plus do not hide duplicates."""

    if value is None:
        return None
    digits = "".join(character for character in value if character.isdigit())
    return digits or None


def like_contains_pattern(folded_query: str) -> str:
    """Escape LIKE metacharacters and wrap the folded query for contains-search."""

    escaped = folded_query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"
