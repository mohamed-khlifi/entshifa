"""Turn a laryngoscopy payload into observations. The engines read these rows back."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ent.core.utils.ids import new_ulid
from ent.features.laryngoscopy.constants import (
    GRBAS_CONCEPT_CODES,
    GRBAS_ITEMS,
    PAS_CODE,
    RFS_CONCEPT_CODES,
    RFS_ITEMS,
    VOCAL_FOLD_CODE,
)
from ent.features.laryngoscopy.schemas.requests import (
    GrbasWrite,
    LaryngoscopyCreate,
    LaryngoscopyStructureWrite,
    LaryngoscopyUpdate,
    RefluxFindingScoreWrite,
    VocalFoldLesionWrite,
)
from ent.features.observations.models import Observation
from ent.features.terminology.models import Concept

Write = LaryngoscopyCreate | LaryngoscopyUpdate


@dataclass(frozen=True, slots=True)
class _Context:
    clinic_id: int
    patient_id: int
    procedure_record_id: int
    encounter_id: int | None
    encounter_public_id: str | None
    user_id: int
    effective_at: datetime


def build_observations(
    *,
    clinic_id: int,
    patient_id: int,
    procedure_record_id: int,
    encounter_id: int | None,
    encounter_public_id: str | None,
    user_id: int,
    effective_at: datetime,
    body: Write,
    concepts: dict[str, Concept],
) -> list[Observation]:
    """One row per structure, lesion, score item, consistency and residue site."""

    context = _Context(
        clinic_id=clinic_id,
        patient_id=patient_id,
        procedure_record_id=procedure_record_id,
        encounter_id=encounter_id,
        encounter_public_id=encounter_public_id,
        user_id=user_id,
        effective_at=effective_at,
    )
    rows: list[Observation] = [
        _structure(item=item, concepts=concepts, context=context)
        for item in body.structures
    ]
    rows.extend(
        _lesion(lesion=lesion, concepts=concepts, context=context)
        for lesion in body.lesions
    )
    if body.reflux_finding_score is not None:
        rows.extend(
            _ordinals(
                grades=_rfs(body.reflux_finding_score),
                codes=RFS_CONCEPT_CODES,
                concepts=concepts,
                laterality="na",
                context=context,
            )
        )
    if body.grbas is not None:
        rows.extend(
            _ordinals(
                grades=_grbas(body.grbas),
                codes=GRBAS_CONCEPT_CODES,
                concepts=concepts,
                laterality="na",
                context=context,
            )
        )
    if body.fees is not None:
        rows.append(
            _row(
                context=context,
                concept=concepts[PAS_CODE],
                body_site=None,
                laterality="na",
                status="abnormal" if body.fees.pas_score > 1 else "normal",
                value_type="ordinal",
                ordinal_value=body.fees.pas_score,
            )
        )
        for code in body.fees.consistencies:
            rows.append(
                _row(
                    context=context,
                    concept=concepts[code],
                    body_site=None,
                    laterality="na",
                    status="normal",
                    value_type="code",
                    value_concept=concepts[code],
                )
            )
        for code in body.fees.residue_site_codes:
            rows.append(
                _row(
                    context=context,
                    concept=concepts["FIND.LARYNX.POOLING"],
                    body_site=concepts[code],
                    laterality="na",
                    status="abnormal",
                    value_type="code",
                    value_concept=concepts["FIND.LARYNX.POOLING"],
                    map_region_code=code,
                    qualifiers={"role": "residue"},
                )
            )
    return rows


def _structure(
    *,
    item: LaryngoscopyStructureWrite,
    concepts: dict[str, Concept],
    context: _Context,
) -> Observation:
    finding = concepts[item.finding_code]
    site = concepts[item.body_site_code]
    return _row(
        context=context,
        concept=finding,
        body_site=site,
        laterality=item.laterality.value,
        status=item.status,
        value_type="code",
        value_concept=finding,
        map_region_code=site.code,
    )


def _lesion(
    *,
    lesion: VocalFoldLesionWrite,
    concepts: dict[str, Concept],
    context: _Context,
) -> Observation:
    finding = concepts[lesion.finding_code]
    qualifiers = {
        "third": lesion.third_code,
        "surface": lesion.surface_code,
    }
    if lesion.size_mm is not None:
        qualifiers["sizeMm"] = str(lesion.size_mm)
    if lesion.reinke_grade is not None:
        qualifiers["reinkeGrade"] = str(lesion.reinke_grade)
    return _row(
        context=context,
        concept=finding,
        body_site=concepts[VOCAL_FOLD_CODE],
        laterality=lesion.laterality,
        status="abnormal",
        value_type="code",
        value_concept=finding,
        map_region_code=VOCAL_FOLD_CODE,
        qualifiers=qualifiers,
    )


def _ordinals(
    *,
    grades: dict[str, int],
    codes: dict[str, str],
    concepts: dict[str, Concept],
    laterality: str,
    context: _Context,
) -> list[Observation]:
    return [
        _row(
            context=context,
            concept=concepts[codes[item]],
            body_site=None,
            laterality=laterality,
            status="abnormal" if grade > 0 else "normal",
            value_type="ordinal",
            ordinal_value=grade,
        )
        for item, grade in grades.items()
    ]


def _rfs(grades: RefluxFindingScoreWrite) -> dict[str, int]:
    return {item: int(getattr(grades, item)) for item in RFS_ITEMS}


def _grbas(grades: GrbasWrite) -> dict[str, int]:
    return {item: int(getattr(grades, item)) for item in GRBAS_ITEMS}


def _row(
    *,
    context: _Context,
    concept: Concept,
    body_site: Concept | None,
    laterality: str,
    status: str,
    value_type: str,
    value_concept: Concept | None = None,
    ordinal_value: int | None = None,
    map_region_code: str | None = None,
    qualifiers: dict[str, str] | None = None,
) -> Observation:
    return Observation(
        public_id=new_ulid(),
        clinic_id=context.clinic_id,
        patient_id=context.patient_id,
        procedure_record_id=context.procedure_record_id,
        encounter_id=context.encounter_id,
        encounter_public_id=context.encounter_public_id,
        concept_id=int(concept.id),
        body_site_concept_id=int(body_site.id) if body_site is not None else None,
        map_region_code=map_region_code,
        laterality=laterality,
        status=status,
        value_type=value_type,
        value_concept_id=int(value_concept.id) if value_concept is not None else None,
        ordinal_value=ordinal_value,
        qualifiers=qualifiers,
        effective_at=context.effective_at,
        source="clinician",
        recorded_by_id=context.user_id,
        confirmed_by_id=context.user_id,
        created_by_id=context.user_id,
        updated_by_id=context.user_id,
    )
