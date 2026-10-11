"""Turn an endoscopy payload into observations. The engines read these rows back."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from ent.core.utils.ids import new_ulid
from ent.features.endoscopy.constants import (
    ADENOID_CODE,
    LK_CONCEPT_CODES,
    POLYP_GRADE_CODE,
)
from ent.features.endoscopy.schemas.requests import (
    EndoscopyCreate,
    EndoscopyStructureWrite,
    EndoscopyUpdate,
    LundKennedySideWrite,
)
from ent.features.observations.models import Observation
from ent.features.terminology.models import Concept

EndoscopyWrite = EndoscopyCreate | EndoscopyUpdate


def build_observations(
    *,
    clinic_id: int,
    patient_id: int,
    procedure_record_id: int,
    encounter_id: int | None,
    encounter_public_id: str | None,
    user_id: int,
    effective_at: datetime,
    body: EndoscopyWrite,
    concepts: dict[str, Concept],
    polyp_scale: str,
) -> list[Observation]:
    """One row per structure, Lund-Kennedy item, polyp grade and adenoid percent."""

    rows: list[Observation] = []
    for item in body.structures:
        rows.append(
            _structure(
                clinic_id=clinic_id,
                patient_id=patient_id,
                procedure_record_id=procedure_record_id,
                encounter_id=encounter_id,
                encounter_public_id=encounter_public_id,
                user_id=user_id,
                effective_at=effective_at,
                item=item,
                concepts=concepts,
            )
        )
    for side, grades in (
        ("right", body.lund_kennedy_right),
        ("left", body.lund_kennedy_left),
    ):
        rows.extend(
            _lk_side(
                clinic_id=clinic_id,
                patient_id=patient_id,
                procedure_record_id=procedure_record_id,
                encounter_id=encounter_id,
                encounter_public_id=encounter_public_id,
                user_id=user_id,
                effective_at=effective_at,
                side=side,
                grades=grades,
                concepts=concepts,
            )
        )
    rows.extend(
        _optional_scores(
            clinic_id=clinic_id,
            patient_id=patient_id,
            procedure_record_id=procedure_record_id,
            encounter_id=encounter_id,
            encounter_public_id=encounter_public_id,
            user_id=user_id,
            effective_at=effective_at,
            body=body,
            concepts=concepts,
            polyp_scale=polyp_scale,
        )
    )
    return rows


def _structure(
    *,
    clinic_id: int,
    patient_id: int,
    procedure_record_id: int,
    encounter_id: int | None,
    encounter_public_id: str | None,
    user_id: int,
    effective_at: datetime,
    item: EndoscopyStructureWrite,
    concepts: dict[str, Concept],
) -> Observation:
    finding = concepts[item.finding_code]
    site = concepts[item.body_site_code]
    return _row(
        clinic_id=clinic_id,
        patient_id=patient_id,
        procedure_record_id=procedure_record_id,
        encounter_id=encounter_id,
        encounter_public_id=encounter_public_id,
        user_id=user_id,
        effective_at=effective_at,
        concept=finding,
        body_site=site,
        laterality=item.laterality.value,
        status=item.status,
        value_type="code",
        value_concept=finding,
        map_region_code=site.code,
    )


def _lk_side(
    *,
    clinic_id: int,
    patient_id: int,
    procedure_record_id: int,
    encounter_id: int | None,
    encounter_public_id: str | None,
    user_id: int,
    effective_at: datetime,
    side: str,
    grades: LundKennedySideWrite,
    concepts: dict[str, Concept],
) -> list[Observation]:
    values = {
        "polyps": grades.polyps,
        "edema": grades.edema,
        "discharge": grades.discharge,
        "scarring": grades.scarring,
        "crusting": grades.crusting,
    }
    rows: list[Observation] = []
    for item, grade in values.items():
        concept = concepts[LK_CONCEPT_CODES[item]]
        rows.append(
            _row(
                clinic_id=clinic_id,
                patient_id=patient_id,
                procedure_record_id=procedure_record_id,
                encounter_id=encounter_id,
                encounter_public_id=encounter_public_id,
                user_id=user_id,
                effective_at=effective_at,
                concept=concept,
                body_site=None,
                laterality=side,
                status="abnormal" if grade > 0 else "normal",
                value_type="ordinal",
                ordinal_value=grade,
            )
        )
    return rows


def _optional_scores(
    *,
    clinic_id: int,
    patient_id: int,
    procedure_record_id: int,
    encounter_id: int | None,
    encounter_public_id: str | None,
    user_id: int,
    effective_at: datetime,
    body: EndoscopyWrite,
    concepts: dict[str, Concept],
    polyp_scale: str,
) -> list[Observation]:
    rows: list[Observation] = []
    concept = concepts[POLYP_GRADE_CODE]
    for side, grade in (
        ("right", body.polyp_grade_right),
        ("left", body.polyp_grade_left),
    ):
        if grade is None:
            continue
        rows.append(
            _row(
                clinic_id=clinic_id,
                patient_id=patient_id,
                procedure_record_id=procedure_record_id,
                encounter_id=encounter_id,
                encounter_public_id=encounter_public_id,
                user_id=user_id,
                effective_at=effective_at,
                concept=concept,
                body_site=None,
                laterality=side,
                status="abnormal" if grade > 0 else "normal",
                value_type="ordinal",
                ordinal_value=grade,
                qualifiers={"scale": polyp_scale},
            )
        )
    if body.adenoid_obstruction_pct is not None:
        percent = body.adenoid_obstruction_pct
        rows.append(
            _row(
                clinic_id=clinic_id,
                patient_id=patient_id,
                procedure_record_id=procedure_record_id,
                encounter_id=encounter_id,
                encounter_public_id=encounter_public_id,
                user_id=user_id,
                effective_at=effective_at,
                concept=concepts[ADENOID_CODE],
                body_site=None,
                laterality="midline",
                status="abnormal" if percent > 0 else "normal",
                value_type="numeric",
                value_numeric=Decimal(percent),
                value_unit="%",
            )
        )
    return rows


def _row(
    *,
    clinic_id: int,
    patient_id: int,
    procedure_record_id: int,
    encounter_id: int | None,
    encounter_public_id: str | None,
    user_id: int,
    effective_at: datetime,
    concept: Concept,
    body_site: Concept | None,
    laterality: str,
    status: str,
    value_type: str,
    value_concept: Concept | None = None,
    ordinal_value: int | None = None,
    value_numeric: Decimal | None = None,
    value_unit: str | None = None,
    map_region_code: str | None = None,
    qualifiers: dict[str, str] | None = None,
) -> Observation:
    return Observation(
        public_id=new_ulid(),
        clinic_id=clinic_id,
        patient_id=patient_id,
        procedure_record_id=procedure_record_id,
        encounter_id=encounter_id,
        encounter_public_id=encounter_public_id,
        concept_id=int(concept.id),
        body_site_concept_id=int(body_site.id) if body_site is not None else None,
        map_region_code=map_region_code,
        laterality=laterality,
        status=status,
        value_type=value_type,
        value_concept_id=int(value_concept.id) if value_concept is not None else None,
        ordinal_value=ordinal_value,
        value_numeric=value_numeric,
        value_unit=value_unit,
        qualifiers=qualifiers,
        effective_at=effective_at,
        source="clinician",
        recorded_by_id=user_id,
        confirmed_by_id=user_id,
        created_by_id=user_id,
        updated_by_id=user_id,
    )
