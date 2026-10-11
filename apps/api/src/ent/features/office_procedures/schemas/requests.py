"""Short office-procedure write payloads (feature spec §7.4).

Due dates are recorded by the clinician. The server does not invent them.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from ent.core.schemas.base import CamelModel
from ent.core.schemas.common import Laterality
from ent.features.office_procedures.constants import (
    MUSCLES_BY_INDICATION,
    PACK_METHODS,
    SIDED,
    ContentLocale,
)
from ent.features.procedures.constants import AnesthesiaType, ToleranceValue

_NOTE = 2_000
_DOSE_MAX = Decimal("100")
_VOLUME_MAX = Decimal("30")


def _clean_pair(
    text: str | None,
    locale: ContentLocale | None,
    *,
    missing_locale: str,
) -> tuple[str | None, ContentLocale | None]:
    cleaned = text.strip() if text else ""
    if cleaned and locale is None:
        raise ValueError(missing_locale)
    if not cleaned:
        return None, None
    return cleaned, locale


class _ClinicianNote(CamelModel):
    note_text: str | None = Field(default=None, max_length=_NOTE)
    note_locale: ContentLocale | None = None

    @model_validator(mode="after")
    def note_locale_matches_text(self) -> Self:
        self.note_text, self.note_locale = _clean_pair(
            self.note_text,
            self.note_locale,
            missing_locale="note_locale",
        )
        return self


class EpistaxisWrite(_ClinicianNote):
    subtype: Literal["epistaxis_management"]
    site_found: bool
    bleeding_site: (
        Literal[
            "little_area",
            "septum",
            "inferior_turbinate",
            "nasal_floor",
            "nasopharynx",
        ]
        | None
    ) = None
    method: Literal[
        "silver_nitrate",
        "electrocautery",
        "anterior_pack",
        "posterior_pack",
        "balloon",
    ]
    pack_type: Literal["merocel", "rapid_rhino", "ribbon_gauze"] | None = None
    pack_removal_date: date | None = None
    systolic_bp: int = Field(ge=50, le=300)
    diastolic_bp: int = Field(ge=30, le=200)
    anticoagulant_status: Literal["yes", "no", "unknown"]
    advice_text: str | None = Field(default=None, max_length=_NOTE)
    advice_locale: ContentLocale | None = None

    @model_validator(mode="after")
    def epistaxis_fields(self) -> Self:
        self.advice_text, self.advice_locale = _clean_pair(
            self.advice_text,
            self.advice_locale,
            missing_locale="advice_locale",
        )
        if self.systolic_bp <= self.diastolic_bp:
            raise ValueError("blood_pressure")
        if self.site_found and self.bleeding_site is None:
            raise ValueError("bleeding_site")
        if not self.site_found:
            self.bleeding_site = None
        packed = self.method in PACK_METHODS
        if packed and self.pack_removal_date is None:
            raise ValueError("pack_removal_date")
        if self.method == "anterior_pack" and self.pack_type is None:
            raise ValueError("pack_type")
        if not packed:
            self.pack_type = None
            self.pack_removal_date = None
        if self.method != "anterior_pack":
            self.pack_type = None
        return self


class FineNeedleAspirationWrite(_ClinicianNote):
    subtype: Literal["fine_needle_aspiration"]
    site: Literal["thyroid", "parotid", "submandibular", "neck_node", "other"]
    site_note: str | None = Field(default=None, max_length=120)
    site_note_locale: ContentLocale | None = None
    needle_gauge: int = Field(ge=18, le=27)
    passes: int = Field(ge=1, le=10)
    ultrasound_guided: bool
    laboratory_text: str = Field(min_length=1, max_length=120)
    laboratory_locale: ContentLocale
    result_due_date: date

    @model_validator(mode="after")
    def site_note_when_other(self) -> Self:
        self.laboratory_text = self.laboratory_text.strip()
        if not self.laboratory_text:
            raise ValueError("laboratory_text")
        self.site_note, self.site_note_locale = _clean_pair(
            self.site_note,
            self.site_note_locale,
            missing_locale="site_note_locale",
        )
        if self.site == "other" and self.site_note is None:
            raise ValueError("site_note")
        if self.site != "other":
            self.site_note = None
            self.site_note_locale = None
        return self


class BiopsyWrite(_ClinicianNote):
    subtype: Literal["oral_pharyngeal_biopsy"]
    site: Literal[
        "oral_cavity",
        "tongue",
        "palate",
        "tonsil",
        "oropharynx",
        "hypopharynx",
    ]
    technique: Literal["punch", "incisional", "excisional"]
    laboratory_text: str = Field(min_length=1, max_length=120)
    laboratory_locale: ContentLocale
    result_due_date: date

    @model_validator(mode="after")
    def laboratory_present(self) -> Self:
        self.laboratory_text = self.laboratory_text.strip()
        if not self.laboratory_text:
            raise ValueError("laboratory_text")
        return self


class BotulinumInjectionSiteWrite(CamelModel):
    muscle: Literal[
        "thyroarytenoid",
        "lateral_cricoarytenoid",
        "parotid",
        "submandibular",
        "cricopharyngeus",
    ]
    side: Literal["right", "left", "bilateral", "midline"]
    dose_units: Decimal = Field(gt=0, le=_DOSE_MAX, max_digits=5, decimal_places=1)


class BotulinumWrite(_ClinicianNote):
    subtype: Literal["botulinum_injection"]
    indication: Literal["spasmodic_dysphonia", "sialorrhea", "cricopharyngeal"]
    injections: list[BotulinumInjectionSiteWrite] = Field(min_length=1, max_length=8)

    @model_validator(mode="after")
    def muscles_match_indication(self) -> Self:
        allowed = MUSCLES_BY_INDICATION[self.indication]
        if any(item.muscle not in allowed for item in self.injections):
            raise ValueError("muscle")
        return self


class PeritonsillarWrite(_ClinicianNote):
    subtype: Literal["peritonsillar_drainage"]
    method: Literal["aspiration", "incision"]
    volume_ml: Decimal = Field(gt=0, le=_VOLUME_MAX, max_digits=4, decimal_places=1)
    culture_sent: bool


class NasalFractureWrite(_ClinicianNote):
    subtype: Literal["nasal_fracture_reduction"]
    splint_type: Literal["thermoplastic", "plaster", "denver", "tape"]
    splint_removal_date: date


class SialendoscopyWrite(_ClinicianNote):
    subtype: Literal["sialendoscopy"]
    gland: Literal["parotid", "submandibular"]
    findings: list[Literal["stone", "stenosis", "mucus_plug"]] = Field(
        min_length=1,
        max_length=3,
    )
    stone_removed: bool
    follow_up_date: date

    @model_validator(mode="after")
    def stone_matches_findings(self) -> Self:
        unique = tuple(dict.fromkeys(self.findings))
        if len(unique) != len(self.findings):
            raise ValueError("findings")
        if self.stone_removed and "stone" not in self.findings:
            raise ValueError("stone_removed")
        return self


ShortProcedureWrite = Annotated[
    EpistaxisWrite
    | FineNeedleAspirationWrite
    | BiopsyWrite
    | BotulinumWrite
    | PeritonsillarWrite
    | NasalFractureWrite
    | SialendoscopyWrite,
    Field(discriminator="subtype"),
]


class _OfficeBody(CamelModel):
    encounter_public_id: str | None = Field(default=None, min_length=26, max_length=26)
    performed_at: datetime
    laterality: Laterality
    anesthesia: AnesthesiaType = "none"
    tolerance: ToleranceValue | None = None
    indication_text: str | None = Field(default=None, max_length=400)
    detail: ShortProcedureWrite

    @model_validator(mode="after")
    def sided_procedures(self) -> Self:
        if self.detail.subtype in SIDED and self.laterality.value not in {
            "right",
            "left",
        }:
            raise ValueError("laterality")
        text = (self.indication_text or "").strip()
        self.indication_text = text or None
        return self


class OfficeProcedureCreate(_OfficeBody):
    patient_public_id: str = Field(min_length=26, max_length=26)


class OfficeProcedureUpdate(_OfficeBody):
    version: int = Field(ge=1)
