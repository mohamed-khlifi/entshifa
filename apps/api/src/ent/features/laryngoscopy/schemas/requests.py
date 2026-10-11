"""Laryngoscopy write payloads. Scores are computed; the client does not send totals."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from ent.core.schemas.base import CamelModel
from ent.core.schemas.common import Laterality
from ent.features.laryngoscopy.constants import (
    AmplitudeValue,
    FoldSide,
    GlotticClosure,
    MobilityValue,
    MucosalWave,
    NonVibratingSegment,
    PeriodicityValue,
    PhaseClosure,
    PhaseSymmetry,
    PositionValue,
    ScopeType,
    StructureStatus,
    SupraglotticPattern,
    SymmetryValue,
    VerticalLevel,
)
from ent.features.procedures.constants import (
    AnesthesiaType,
    ProcedureSetting,
    ToleranceValue,
)

_NOTE = 10_000


class VocalFoldWrite(CamelModel):
    mobility: MobilityValue
    position: PositionValue | None = None


class LaryngoscopyStructureWrite(CamelModel):
    body_site_code: str = Field(min_length=1, max_length=60)
    laterality: Laterality
    status: StructureStatus
    finding_code: str = Field(min_length=1, max_length=60)


class VocalFoldLesionWrite(CamelModel):
    laterality: FoldSide
    third_code: str = Field(min_length=1, max_length=60)
    surface_code: str = Field(min_length=1, max_length=60)
    finding_code: str = Field(min_length=1, max_length=60)
    size_mm: int | None = Field(default=None, ge=0, le=50)
    reinke_grade: int | None = Field(default=None, ge=1, le=3)


class RefluxFindingScoreWrite(CamelModel):
    subglottic_edema: int
    ventricular_obliteration: int
    erythema: int
    vocal_fold_edema: int
    diffuse_laryngeal_edema: int
    posterior_commissure_hypertrophy: int
    granuloma: int
    thick_endolaryngeal_mucus: int


class GrbasWrite(CamelModel):
    grade: int
    roughness: int
    breathiness: int
    asthenia: int
    strain: int


class StroboscopyWrite(CamelModel):
    symmetry: SymmetryValue
    periodicity: PeriodicityValue
    amplitude_right: AmplitudeValue
    amplitude_left: AmplitudeValue
    mucosal_wave_right: MucosalWave
    mucosal_wave_left: MucosalWave
    phase_closure: PhaseClosure | None = None
    phase_symmetry: PhaseSymmetry | None = None
    vertical_level: VerticalLevel | None = None
    non_vibrating_segment: NonVibratingSegment | None = None


class FeesWrite(CamelModel):
    pas_score: int
    consistencies: list[str] = Field(min_length=1)
    residue_site_codes: list[str] = Field(default_factory=list)


class _LaryngoscopyBody(CamelModel):
    encounter_public_id: str | None = Field(default=None, min_length=26, max_length=26)
    performed_at: datetime
    laterality: Laterality = Laterality.BILATERAL
    anesthesia: AnesthesiaType = "topical_spray"
    setting: ProcedureSetting = "office"
    instrument: str | None = Field(default=None, max_length=100)
    indication_text: str | None = Field(default=None, max_length=400)
    tolerance: ToleranceValue | None = None
    scope_type: ScopeType
    vocal_fold_right: VocalFoldWrite
    vocal_fold_left: VocalFoldWrite
    glottic_closure: GlotticClosure
    supraglottic_pattern: SupraglotticPattern | None = None
    structures: list[LaryngoscopyStructureWrite] = Field(default_factory=list)
    lesions: list[VocalFoldLesionWrite] = Field(default_factory=list)
    stroboscopy: StroboscopyWrite | None = None
    reflux_finding_score: RefluxFindingScoreWrite | None = None
    grbas: GrbasWrite | None = None
    fees: FeesWrite | None = None
    conclusion_text: str | None = Field(default=None, max_length=_NOTE)


class LaryngoscopyCreate(_LaryngoscopyBody):
    patient_public_id: str = Field(min_length=26, max_length=26)


class LaryngoscopyUpdate(_LaryngoscopyBody):
    version: int = Field(ge=1)
