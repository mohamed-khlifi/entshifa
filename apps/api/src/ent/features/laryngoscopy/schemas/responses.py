"""Laryngoscopy read models. Concept displays are resolved for the request locale."""

from __future__ import annotations

from datetime import datetime

from ent.core.schemas.base import CamelModel
from ent.core.schemas.common import CodeableConcept


class VocalFoldRead(CamelModel):
    mobility: str
    position: str | None


class GrbasRead(CamelModel):
    grade: int
    roughness: int
    breathiness: int
    asthenia: int
    strain: int
    total: int


class RefluxFindingScoreRead(CamelModel):
    subglottic_edema: int
    ventricular_obliteration: int
    erythema: int
    vocal_fold_edema: int
    diffuse_laryngeal_edema: int
    posterior_commissure_hypertrophy: int
    granuloma: int
    thick_endolaryngeal_mucus: int


class LaryngoscopyStructureRead(CamelModel):
    body_site: CodeableConcept
    laterality: str
    status: str
    finding: CodeableConcept


class VocalFoldLesionRead(CamelModel):
    laterality: str
    third: CodeableConcept
    surface: CodeableConcept
    finding: CodeableConcept
    size_mm: int | None
    reinke_grade: int | None


class ScoreStampRead(CamelModel):
    code: str
    version: str
    value: str
    unit: str | None
    reference: str
    formula: str


class LaryngoscopyExamRead(CamelModel):
    public_id: str
    version: int
    procedure_id: str
    procedure_status: str
    patient_id: str
    encounter_id: str | None
    performed_at: datetime
    laterality: str
    anesthesia: str
    setting: str
    instrument: str | None
    indication_text: str | None
    tolerance: str | None
    scope_type: str
    vocal_fold_right: VocalFoldRead
    vocal_fold_left: VocalFoldRead
    glottic_closure: str
    supraglottic_pattern: str | None
    stroboscopy_performed: bool
    symmetry: str | None
    periodicity: str | None
    amplitude_right: str | None
    amplitude_left: str | None
    mucosal_wave_right: str | None
    mucosal_wave_left: str | None
    phase_closure: str | None
    phase_symmetry: str | None
    vertical_level: str | None
    non_vibrating_segment: str | None
    fees_performed: bool
    rfs_score: int | None
    reflux_finding_score: RefluxFindingScoreRead | None
    grbas: GrbasRead | None
    pas_score: int | None
    consistencies: list[CodeableConcept]
    residue_sites: list[CodeableConcept]
    structures: list[LaryngoscopyStructureRead]
    lesions: list[VocalFoldLesionRead]
    scores: list[ScoreStampRead]
    conclusion_text: str | None
    created_at: datetime
    updated_at: datetime
