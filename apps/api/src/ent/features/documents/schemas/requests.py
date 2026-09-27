"""Document request bodies."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from ent.core.schemas.base import CamelModel

LocaleCode = Literal["en", "fr", "ar"]
DirectionCode = Literal["ltr", "rtl"]
CategoryCode = Literal[
    "consultation_report",
    "endoscopy_report",
    "audiology_report",
    "prescription",
    "certificate",
    "imaging_request",
    "referral_letter",
    "handout",
    "consent",
    "quote",
    "operative_note",
    "tumor_board",
    "patient_summary",
]
PlaceholderType = Literal[
    "string",
    "integer",
    "date",
    "code",
    "code_list",
    "text_list",
]
RecipientType = Literal["patient", "referrer", "insurer", "other"]
RecipientChannel = Literal["print", "download"]


class PlaceholderSpec(CamelModel):
    type: PlaceholderType
    required: bool = True


class DocumentTemplateCreate(CamelModel):
    code: str = Field(min_length=1, max_length=60, pattern=r"^[a-z][a-z0-9_]*$")
    category: CategoryCode
    placeholders: dict[str, PlaceholderSpec]


class PageSetup(CamelModel):
    size: Literal["A4"] = "A4"
    orientation: Literal["portrait", "landscape"] = "portrait"
    margin_top_mm: int = Field(default=16, ge=5, le=40)
    margin_bottom_mm: int = Field(default=16, ge=5, le=40)
    margin_left_mm: int = Field(default=14, ge=5, le=40)
    margin_right_mm: int = Field(default=14, ge=5, le=40)
    title: str = Field(min_length=1, max_length=200)


class DocumentTemplatePreview(CamelModel):
    locale: LocaleCode
    direction: DirectionCode
    header_html: str = ""
    body_html: str = Field(min_length=1)
    footer_html: str = ""
    css: str = ""
    placeholders: dict[str, PlaceholderSpec]
    page_setup: PageSetup


class DocumentTemplateVersionCreate(CamelModel):
    locale: LocaleCode
    direction: DirectionCode
    header_html: str = ""
    body_html: str = Field(min_length=1)
    footer_html: str = ""
    css: str = ""
    page_setup: PageSetup


class DocumentCreate(CamelModel):
    patient_public_id: str = Field(min_length=26, max_length=26)
    template_code: str = Field(min_length=1, max_length=60)
    locale: LocaleCode | None = None


class DocumentFinalize(CamelModel):
    body_override_html: str | None = None


class DocumentRecipientCreate(CamelModel):
    recipient_type: RecipientType
    name: str = Field(min_length=1, max_length=160)
    channel: RecipientChannel = "print"
    address: str | None = Field(default=None, max_length=190)
    locale: LocaleCode | None = None


def placeholder_map(raw: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Normalize stored JSON into the shape the engine expects."""

    normalized: dict[str, dict[str, Any]] = {}
    for key, value in raw.items():
        if isinstance(value, dict):
            normalized[key] = {
                "type": value.get("type"),
                "required": bool(value.get("required", True)),
            }
    return normalized
