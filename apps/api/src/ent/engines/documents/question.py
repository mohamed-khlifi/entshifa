"""Clinical question text for an imaging request.

The doctor's own sentence wins. Otherwise the recorded complaint displays,
diagnosis displays, and assessment are joined in that order. This is not a
generated narrative: each part was already written or resolved.
"""

from __future__ import annotations

VERSION = "1.0.0"
REFERENCE = (
    "Feature specification §14.4: the imaging clinical question is written "
    "from the consultation. The doctor's text is kept verbatim."
)


def clinical_question(
    *,
    complaints: tuple[str, ...],
    diagnoses: tuple[str, ...],
    assessment: str | None,
    supplied: str | None,
) -> str:
    """Return the question stored on the imaging request."""

    text = (supplied or "").strip()
    if text:
        return text
    parts = [item.strip() for item in (*complaints, *diagnoses) if item.strip()]
    note = (assessment or "").strip()
    if note:
        parts.append(note)
    return " · ".join(parts)
