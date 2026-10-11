"""Otology write payloads. Follow-up dates are resolved on the server."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import Field, model_validator

from ent.core.schemas.base import CamelModel
from ent.core.schemas.common import Laterality
from ent.features.otology.constants import (
    ContentLocale,
    DeviceStatus,
    DoseUnit,
    ExamMethod,
    MobilityValue,
    RinneValue,
    StructureStatus,
    WeberValue,
)
from ent.features.procedures.constants import (
    AnesthesiaType,
    ProcedureSetting,
    ToleranceValue,
)

_NOTE = 10_000
_DOSE_MAX = Decimal("100")


class OtologyStructureWrite(CamelModel):
    body_site_code: str = Field(min_length=1, max_length=60)
    laterality: Laterality
    status: StructureStatus
    finding_code: str = Field(min_length=1, max_length=60)
    map_region_code: str = Field(min_length=1, max_length=60)


class WaxRemovalWrite(CamelModel):
    subtype: Literal["wax_removal"]
    method: Literal["microsuction", "curette", "irrigation"]
    completeness: Literal["complete", "partial"]
    canal_condition: Literal["clear", "residual_wax", "inflamed", "traumatized"]


class ForeignBodyWrite(CamelModel):
    subtype: Literal["foreign_body"]
    object_text: str = Field(min_length=1, max_length=80)
    object_locale: ContentLocale
    method: Literal["microsuction", "forceps", "irrigation", "hook"]
    trauma: Literal["none", "canal", "tympanic"]


class WickWrite(CamelModel):
    subtype: Literal["wick"]
    wick_type: Literal["pope", "ribbon", "merocel"]


class TubeInsertionWrite(CamelModel):
    subtype: Literal["tube_insertion"]
    tube_model: Literal["shepard", "armstrong", "t_tube", "bobbin", "paparella"]
    effusion: Literal["none", "serous", "mucoid", "purulent", "bloody"]
    complication: Literal["bleeding", "otorrhea", "vertigo", "perforation"] | None = (
        None
    )


class TubeRemovalWrite(CamelModel):
    subtype: Literal["tube_removal"]
    device_public_id: str = Field(min_length=26, max_length=26)


class IntratympanicInjectionWrite(CamelModel):
    subtype: Literal["intratympanic_injection"]
    drug_code: Literal[
        "DRUG.IT.DEXAMETHASONE",
        "DRUG.IT.METHYLPREDNISOLONE",
        "DRUG.IT.GENTAMICIN",
    ]
    dose_amount: Decimal = Field(gt=0, le=_DOSE_MAX, max_digits=5, decimal_places=2)
    dose_unit: DoseUnit
    indication_text: str | None = Field(default=None, max_length=400)
    indication_locale: ContentLocale | None = None

    @model_validator(mode="after")
    def indication_locale_required(self) -> IntratympanicInjectionWrite:
        has_text = bool(self.indication_text and self.indication_text.strip())
        if has_text and self.indication_locale is None:
            raise ValueError("indication_locale")
        if not has_text:
            self.indication_text = None
            self.indication_locale = None
        return self


class CavityCleaningWrite(CamelModel):
    subtype: Literal["cavity_cleaning"]
    condition: Literal["dry", "moist", "granulation", "debris", "exposed_structures"]


OfficeProcedureWrite = Annotated[
    WaxRemovalWrite
    | ForeignBodyWrite
    | WickWrite
    | TubeInsertionWrite
    | TubeRemovalWrite
    | IntratympanicInjectionWrite
    | CavityCleaningWrite,
    Field(discriminator="subtype"),
]


class _OtologyBody(CamelModel):
    encounter_public_id: str | None = Field(default=None, min_length=26, max_length=26)
    performed_at: datetime
    laterality: Laterality = Laterality.BILATERAL
    anesthesia: AnesthesiaType = "none"
    setting: ProcedureSetting = "office"
    instrument: str | None = Field(default=None, max_length=100)
    indication_text: str | None = Field(default=None, max_length=400)
    tolerance: ToleranceValue | None = None
    method: ExamMethod
    weber: WeberValue | None = None
    rinne_right: RinneValue | None = None
    rinne_left: RinneValue | None = None
    fork_frequency_hz: Literal[256, 512] | None = None
    mobility_right: MobilityValue | None = None
    mobility_left: MobilityValue | None = None
    structures: list[OtologyStructureWrite] = Field(default_factory=list)
    procedure: OfficeProcedureWrite | None = None
    conclusion_text: str | None = Field(default=None, max_length=_NOTE)


class OtologyCreate(_OtologyBody):
    patient_public_id: str = Field(min_length=26, max_length=26)


class OtologyUpdate(_OtologyBody):
    version: int = Field(ge=1)


class EarDeviceStatusUpdate(CamelModel):
    version: int = Field(ge=1)
    status: DeviceStatus
