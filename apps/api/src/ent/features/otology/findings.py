"""Turn membrane and canal marks into observations."""

from __future__ import annotations

from datetime import datetime

from ent.core.utils.ids import new_ulid
from ent.features.observations.models import Observation
from ent.features.otology.schemas.requests import OtologyCreate, OtologyUpdate
from ent.features.terminology.models import Concept

Write = OtologyCreate | OtologyUpdate


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
    rows: list[Observation] = []
    for item in body.structures:
        finding = concepts[item.finding_code]
        site = concepts[item.body_site_code]
        rows.append(
            Observation(
                public_id=new_ulid(),
                clinic_id=clinic_id,
                patient_id=patient_id,
                procedure_record_id=procedure_record_id,
                encounter_id=encounter_id,
                encounter_public_id=encounter_public_id,
                concept_id=int(finding.id),
                body_site_concept_id=int(site.id),
                map_region_code=item.map_region_code,
                laterality=item.laterality.value,
                status=item.status,
                value_type="code",
                value_concept_id=int(finding.id),
                effective_at=effective_at,
                source="clinician",
                recorded_by_id=user_id,
                confirmed_by_id=user_id,
                created_by_id=user_id,
                updated_by_id=user_id,
            )
        )
    return rows
