"""Inputs for the examination narrative renderer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

NarrativeLocale = Literal["en", "fr", "ar"]
NarrativeLaterality = Literal["right", "left", "midline", "bilateral", "na"]
NarrativeStatus = Literal["normal", "abnormal", "not_examined", "unknown"]


@dataclass(frozen=True, slots=True)
class NarrativeFinding:
    """One map finding already resolved to a locale phrase template."""

    laterality: str
    status: str
    sort_index: int
    body_site_label: str
    phrase_template: str
    concept_code: str = ""
