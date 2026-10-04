"""Diagnosis use cases: visit rows, promotion, and doctor favourites."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.audit.recorder import AuditRecorder
from ent.core.context import set_clinic_id, set_user_id
from ent.core.errors.exceptions import ValidationError
from ent.core.schemas.base import PageMeta, PageSchema
from ent.core.schemas.common import Laterality
from ent.core.security.principal import CurrentUser
from ent.core.utils.ids import new_ulid
from ent.features.diagnoses.exceptions import (
    DiagnosisInvalidConceptError,
    DiagnosisNotFoundError,
)
from ent.features.diagnoses.mapping import (
    normalize_diagnoses,
    problem_status_for,
    to_diagnosis_read,
    to_favorite_read,
)
from ent.features.diagnoses.models import Diagnosis, UserDiagnosisFavorite
from ent.features.diagnoses.repository import (
    DiagnosisRepository,
    UserDiagnosisFavoriteRepository,
)
from ent.features.diagnoses.schemas.requests import (
    DiagnosisFavoriteReplace,
    DiagnosisWrite,
)
from ent.features.diagnoses.schemas.responses import (
    DiagnosisFavoriteRead,
    DiagnosisRead,
)
from ent.features.encounters.exceptions import EncounterNotFoundError
from ent.features.encounters.models import Encounter
from ent.features.encounters.references import EncounterReferences
from ent.features.encounters.repository import EncounterRepository
from ent.features.patients.models import PatientProblem
from ent.features.patients.repository import PatientProblemRepository
from ent.features.terminology.models import Concept
from ent.features.terminology.repository import TerminologyRepository

_FAVORITE_LIMIT = 40
_PROBLEM_RANK = {"active": 0, "suspected": 1, "resolved": 2, "ruled_out": 3}


class DiagnosisService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._audit = AuditRecorder(session)
        self._refs = EncounterReferences(session)

    async def replace_for_encounter(
        self,
        *,
        user: CurrentUser,
        encounter: Encounter,
        items: list[DiagnosisWrite],
    ) -> None:
        """Replace the draft visit's diagnoses. Matched rows keep their identity."""

        self._bind(user)
        EncounterRepository(self._session, clinic_id=user.clinic_id).assert_draft(
            encounter
        )
        normalized = normalize_diagnoses(list(items))
        concepts = await self._concepts(
            user, {item.concept_public_id for item in normalized}
        )
        self._require_diagnosis_kind(normalized, concepts)
        repo = self._diagnoses(user)
        existing = await repo.list_for_encounter(int(encounter.id))
        by_key = {(int(row.concept_id), row.laterality): row for row in existing}
        seen: set[tuple[int, str]] = set()
        now = datetime.now(UTC).replace(tzinfo=None)
        for item in normalized:
            concept = concepts[item.concept_public_id]
            key = (int(concept.id), item.laterality.value)
            if key in seen:
                raise ValidationError(reason="duplicate_diagnosis")
            seen.add(key)
            current = by_key.get(key)
            if current is None:
                await repo.add(
                    Diagnosis(
                        public_id=new_ulid(),
                        clinic_id=user.clinic_id,
                        patient_id=int(encounter.patient_id),
                        encounter_id=int(encounter.id),
                        concept_id=int(concept.id),
                        laterality=item.laterality.value,
                        status=item.status,
                        is_primary=item.is_primary,
                        onset_date=item.onset_date,
                        note=item.note,
                        source=item.source,
                        recorded_by_id=user.user_id,
                        effective_at=encounter.started_at,
                        sort_order=item.sort_order,
                        created_by_id=user.user_id,
                        updated_by_id=user.user_id,
                    )
                )
                continue
            current.status = item.status
            current.is_primary = item.is_primary
            current.onset_date = item.onset_date
            current.note = item.note
            current.sort_order = item.sort_order
            current.source = item.source
            current.updated_by_id = user.user_id
        for key, row in by_key.items():
            if key in seen:
                continue
            row.deleted_at = now
            row.deleted_by_id = user.user_id
            row.updated_by_id = user.user_id

    async def copy_onto_encounter(
        self,
        *,
        user: CurrentUser,
        source: Encounter,
        target: Encounter,
    ) -> None:
        """Clone visit diagnoses onto a new draft and mark them as copied."""

        self._bind(user)
        repo = self._diagnoses(user)
        for row in source.diagnoses:
            if row.deleted_at is not None:
                continue
            await repo.add(
                Diagnosis(
                    public_id=new_ulid(),
                    clinic_id=user.clinic_id,
                    patient_id=int(target.patient_id),
                    encounter_id=int(target.id),
                    concept_id=int(row.concept_id),
                    laterality=row.laterality,
                    status=row.status,
                    is_primary=bool(row.is_primary),
                    onset_date=row.onset_date,
                    note=row.note,
                    source="copy_forward",
                    recorded_by_id=user.user_id,
                    effective_at=target.started_at,
                    derived_from_diagnosis_id=int(row.id),
                    sort_order=int(row.sort_order),
                    created_by_id=user.user_id,
                    updated_by_id=user.user_id,
                )
            )

    async def promote(
        self,
        *,
        user: CurrentUser,
        encounter_public_id: str,
        diagnosis_public_id: str,
        content_locale: str,
    ) -> DiagnosisRead:
        """Upsert the problem list from a visit diagnosis and link the row."""

        self._bind(user)
        encounter = await self._require_encounter(user, encounter_public_id)
        repo = self._diagnoses(user)
        row = await repo.get_for_encounter(diagnosis_public_id, int(encounter.id))
        if row is None:
            raise DiagnosisNotFoundError(
                resource="diagnosis", publicId=diagnosis_public_id
            )
        problem = await self._upsert_problem(user, encounter, row)
        encounter_pk = int(encounter.id)
        patient_pk = int(encounter.patient_id)
        row.promoted_to_problem_id = int(problem.id)
        row.updated_by_id = user.user_id
        row.version = int(row.version) + 1
        await self._session.flush()
        self._session.expire_all()
        refreshed = await repo.get_for_encounter(diagnosis_public_id, encounter_pk)
        if refreshed is None:
            raise DiagnosisNotFoundError(
                resource="diagnosis", publicId=diagnosis_public_id
            )
        labels = await self._refs.labels(
            user, {int(refreshed.concept_id)}, content_locale
        )
        payload = to_diagnosis_read(refreshed, labels)
        self._audit.record_access(
            action="promote",
            entity_type="diagnosis",
            clinic_id=user.clinic_id,
            entity_id=int(refreshed.id),
            entity_public_id=refreshed.public_id,
            patient_id=patient_pk,
        )
        await self._session.commit()
        return payload

    async def list_favorites(
        self, *, user: CurrentUser, content_locale: str
    ) -> PageSchema[DiagnosisFavoriteRead]:
        self._bind(user)
        rows = await self._favorites(user).list_for_user(user.user_id)
        labels = await self._refs.labels(
            user, {int(row.concept_id) for row in rows}, content_locale
        )
        items = [to_favorite_read(row, labels) for row in rows]
        self._audit.record_access(
            action="list",
            entity_type="user_diagnosis_favorite",
            clinic_id=user.clinic_id,
        )
        await self._session.commit()
        return PageSchema(
            items=items,
            page=PageMeta(
                total=len(items),
                limit=_FAVORITE_LIMIT,
                offset=0,
                next_cursor=None,
            ),
        )

    async def replace_favorites(
        self,
        *,
        user: CurrentUser,
        body: DiagnosisFavoriteReplace,
        content_locale: str,
    ) -> PageSchema[DiagnosisFavoriteRead]:
        self._bind(user)
        ordered = list(dict.fromkeys(body.concept_public_ids))
        concepts = await self._concepts(user, set(ordered))
        writes = [
            DiagnosisWrite(
                concept_public_id=public_id,
                laterality=Laterality.NA,
                status="suspected",
            )
            for public_id in ordered
        ]
        self._require_diagnosis_kind(writes, concepts)
        repo = self._favorites(user)
        existing = {
            int(row.concept_id): row
            for row in await repo.list_for_user_including_deleted(user.user_id)
        }
        kept: set[int] = set()
        now = datetime.now(UTC).replace(tzinfo=None)
        for index, public_id in enumerate(ordered):
            concept = concepts[public_id]
            kept.add(int(concept.id))
            current = existing.get(int(concept.id))
            if current is None:
                await repo.add(
                    UserDiagnosisFavorite(
                        public_id=new_ulid(),
                        clinic_id=user.clinic_id,
                        user_id=user.user_id,
                        concept_id=int(concept.id),
                        sort_order=index,
                        created_by_id=user.user_id,
                        updated_by_id=user.user_id,
                    )
                )
                continue
            current.sort_order = index
            current.deleted_at = None
            current.deleted_by_id = None
            current.updated_by_id = user.user_id
        for concept_id, row in existing.items():
            if concept_id in kept or row.deleted_at is not None:
                continue
            row.deleted_at = now
            row.deleted_by_id = user.user_id
            row.updated_by_id = user.user_id
        await self._session.flush()
        return await self.list_favorites(user=user, content_locale=content_locale)

    def _bind(self, user: CurrentUser) -> None:
        set_clinic_id(user.clinic_id)
        set_user_id(user.user_id)

    def _diagnoses(self, user: CurrentUser) -> DiagnosisRepository:
        return DiagnosisRepository(self._session, clinic_id=user.clinic_id)

    def _favorites(self, user: CurrentUser) -> UserDiagnosisFavoriteRepository:
        return UserDiagnosisFavoriteRepository(self._session, clinic_id=user.clinic_id)

    async def _require_encounter(self, user: CurrentUser, public_id: str) -> Encounter:
        encounter = await EncounterRepository(
            self._session, clinic_id=user.clinic_id
        ).get_detail(public_id)
        if encounter is None:
            raise EncounterNotFoundError(resource="encounter", publicId=public_id)
        await self._refs.assert_patient_visible(user, int(encounter.patient_id))
        return encounter

    async def _concepts(
        self, user: CurrentUser, public_ids: set[str]
    ) -> dict[str, Concept]:
        rows = await TerminologyRepository(
            self._session, clinic_id=user.clinic_id
        ).list_concepts_by_public_ids(public_ids)
        found = {row.public_id: row for row in rows}
        missing = public_ids - set(found)
        if missing:
            raise ValidationError(
                reason="unknown_concept", conceptId=sorted(missing)[0]
            )
        return found

    def _require_diagnosis_kind(
        self, items: list[DiagnosisWrite], concepts: dict[str, Concept]
    ) -> None:
        for item in items:
            concept = concepts[item.concept_public_id]
            if concept.kind != "diagnosis":
                raise DiagnosisInvalidConceptError(
                    conceptId=item.concept_public_id,
                    kind=concept.kind,
                )

    async def _upsert_problem(
        self, user: CurrentUser, encounter: Encounter, row: Diagnosis
    ) -> PatientProblem:
        repo = PatientProblemRepository(self._session, clinic_id=user.clinic_id)
        matches = await repo.matching_concept(
            patient_id=int(encounter.patient_id),
            concept_id=int(row.concept_id),
            laterality=row.laterality,
        )
        status = problem_status_for(row.status)
        today = datetime.now(UTC).date()
        if not matches:
            problem = PatientProblem(
                public_id=new_ulid(),
                clinic_id=user.clinic_id,
                patient_id=int(encounter.patient_id),
                diagnosis_concept_id=int(row.concept_id),
                laterality=row.laterality,
                status=status,
                onset_date=row.onset_date,
                resolved_date=today if status in {"resolved", "ruled_out"} else None,
                first_encounter_id=int(encounter.id),
                last_encounter_id=int(encounter.id),
                note=row.note,
                created_by_id=user.user_id,
                updated_by_id=user.user_id,
            )
            await repo.add(problem)
            return problem
        problem = min(matches, key=lambda item: _PROBLEM_RANK.get(item.status, 9))
        problem.status = status
        problem.last_encounter_id = int(encounter.id)
        if problem.first_encounter_id is None:
            problem.first_encounter_id = int(encounter.id)
        if problem.onset_date is None:
            problem.onset_date = row.onset_date
        if problem.note is None:
            problem.note = row.note
        if status in {"resolved", "ruled_out"}:
            if problem.resolved_date is None:
                problem.resolved_date = today
        else:
            problem.resolved_date = None
        problem.updated_by_id = user.user_id
        problem.version = int(problem.version) + 1
        return problem
