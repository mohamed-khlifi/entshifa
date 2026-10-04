"""Narrative render payloads. The text is generated, not a UI catalog string."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from ent.core.schemas.base import CamelModel
from ent.core.schemas.common import Laterality

NarrativeStatus = Literal["normal", "abnormal", "not_examined", "unknown"]


class NarrativeFindingIn(CamelModel):
    concept_code: str = Field(min_length=1, max_length=60)
    body_site_code: str | None = Field(default=None, max_length=60)
    map_region_code: str | None = Field(default=None, max_length=80)
    laterality: Laterality
    status: NarrativeStatus
    sort_index: int = Field(default=0, ge=0, le=10000)


class NarrativeRenderRequest(CamelModel):
    findings: list[NarrativeFindingIn] = Field(default_factory=list, max_length=200)


class NarrativeRenderRead(CamelModel):
    locale: str
    text: str
