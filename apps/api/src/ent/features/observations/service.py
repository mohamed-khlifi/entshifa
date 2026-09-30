"""Observation use cases. Findings stay typed and tenant-scoped."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.audit.recorder import AuditRecorder
from ent.core.context import set_clinic_id, set_user_id
from ent.core.errors.exceptions import NotFoundError, ValidationError
from ent.core.schemas.base import PageSchema, PaginationParams
from ent.core.security.principal import CurrentUser
from ent.core.utils.ids import new_ulid
from ent.engines.observations.bilateral import expand_bilateral_observations
from ent.features.attachments.repository import AttachmentRepository
from ent.features.clinics.repository import ClinicRepository
from ent.features.observations.exceptions import (
    ObservationNotFoundError,
    ObservationVersionConflictError,
)
from ent.features.observations.mapping import (
    _apply_value,
    _check,
    _codes,
    _component,
    _concept_ids,
    _diff_read,
    _draft,
    _observation,
    _observation_read,
    _page,
    _snapshot_read,
    _to_utc_naive,
    _user_ids,
    _value_codes,
    _value_draft,
)
from ent.features.observations.models import (
    ExaminationSnapshot,
    Observation,
    ObservationComponent,
)
from ent.features.observations.repository import (
    ExaminationSnapshotRepository,
    ObservationRepository,
)
from ent.features.observations.schemas.requests import (
    ExaminationSnapshotCreate,
    ObservationBatchCreate,
    ObservationUpdate,
)
from ent.features.observations.schemas.responses import (
    ExaminationSnapshotRead,
    ObservationDiffRead,
    ObservationRead,
)
from ent.features.patients.models import Patient
from ent.features.patients.policies import created_by_scope
from ent.features.patients.repository import PatientRepository
from ent.features.terminology.models import Concept
from ent.features.terminology.repository import TerminologyRepository


class ObservationService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._audit = AuditRecorder(session)

    async def record_batch(
        self,
        *,
        user: CurrentUser,
        patient_public_id: str,
        body: ObservationBatchCreate,
        content_locale: str,
    ) -> list[ObservationRead]:
        self._bind(user)
        patient = await self._patient(user, patient_public_id)
        drafts = expand_bilateral_observations(
            tuple(_draft(item) for item in body.observations)
        )
        for draft in drafts:
            _check(draft.value)
            for component in draft.components:
                _check(component.value)
        concepts = await self._concepts(user, _codes(drafts))
        repo = self._observations(user)
        rows: list[tuple[Observation, list[ObservationComponent]]] = []
        for draft in drafts:
            observation = _observation(
                user=user,
                patient=patient,
                encounter_public_id=body.encounter_public_id,
                draft=draft,
                concepts=concepts,
            )
            components = [
                _component(user, observation, component, concepts)
                for component in draft.components
            ]
            rows.append((observation, components))
        stored = await repo.create_batch(rows)
        loaded = await repo.list_by_public_ids([row.public_id for row in stored])
        payload = await self._reads(user, patient, loaded, content_locale)
        await self._session.commit()
        return payload

    async def list_by_encounter(
        self,
        *,
        user: CurrentUser,
        encounter_public_id: str,
        page: PaginationParams | None,
        content_locale: str,
    ) -> PageSchema[ObservationRead]:
        self._bind(user)
        repo = self._observations(user)
        result = await repo.list_by_encounter(encounter_public_id, page=page)
        self._audit.record_access(
            action="list",
            entity_type="observation",
            clinic_id=user.clinic_id,
            entity_public_id=encounter_public_id,
            reason="encounter",
        )
        if result.total == 0:
            await self._session.commit()
            raise ObservationNotFoundError(
                resource="encounter",
                publicId=encounter_public_id,
            )
        patient_ids = {int(row.patient_id) for row in result.items}
        patients = await self._patients(user).public_ids_by_id(patient_ids)
        items = await self._reads_for_ids(user, result.items, patients, content_locale)
        await self._session.commit()
        return _page(items, result.total, result.limit, result.offset)

    async def get_encounter_diff(
        self,
        *,
        user: CurrentUser,
        patient_public_id: str,
        encounter_public_id_a: str | None,
        encounter_public_id_b: str | None,
        content_locale: str,
    ) -> list[ObservationDiffRead]:
        self._bind(user)
        patient = await self._patient(user, patient_public_id)
        if not encounter_public_id_a or not encounter_public_id_b:
            raise ValidationError(reason="encounter")
        if encounter_public_id_a == encounter_public_id_b:
            raise ValidationError(reason="same_encounter")
        rows = await self._observations(user).diff_encounters_by_body_site(
            patient_id=int(patient.id),
            encounter_public_id_a=encounter_public_id_a,
            encounter_public_id_b=encounter_public_id_b,
        )
        concept_ids: set[int] = set()
        for row in rows:
            concept_ids.add(row.concept_id)
            if row.body_site_concept_id is not None:
                concept_ids.add(row.body_site_concept_id)
            if row.value_concept_id_a is not None:
                concept_ids.add(row.value_concept_id_a)
            if row.value_concept_id_b is not None:
                concept_ids.add(row.value_concept_id_b)
        labels = await self._labels(user, concept_ids, content_locale)
        self._audit.record_access(
            action="diff",
            entity_type="observation",
            clinic_id=user.clinic_id,
            patient_id=int(patient.id),
            reason="encounter_diff",
        )
        await self._session.commit()
        return [_diff_read(row, labels) for row in rows]

    async def list_timeline(
        self,
        *,
        user: CurrentUser,
        patient_public_id: str,
        concept_code: str,
        page: PaginationParams | None,
        content_locale: str,
    ) -> PageSchema[ObservationRead]:
        self._bind(user)
        patient = await self._patient(user, patient_public_id)
        concept = await self._concept(user, concept_code)
        if concept is None:
            raise ValidationError(reason="unknown_concept", conceptCode=concept_code)
        result = await self._observations(user).list_timeline(
            patient_id=int(patient.id),
            concept_id=int(concept.id),
            page=page,
        )
        self._audit.record_access(
            action="timeline",
            entity_type="observation",
            clinic_id=user.clinic_id,
            patient_id=int(patient.id),
            entity_public_id=concept.public_id,
            reason=concept_code,
        )
        items = await self._reads(user, patient, result.items, content_locale)
        await self._session.commit()
        return _page(items, result.total, result.limit, result.offset)

    async def list_cohort(
        self,
        *,
        user: CurrentUser,
        concept_code: str,
        ordinal_value: int,
        effective_from: datetime,
        effective_to: datetime,
        page: PaginationParams | None,
        content_locale: str,
    ) -> PageSchema[ObservationRead]:
        self._bind(user)
        if effective_to <= effective_from:
            raise ValidationError(reason="effective_range")
        concept = await self._concept(user, concept_code)
        if concept is None:
            resolved = page or PaginationParams()
            return _page([], 0, resolved.limit, resolved.offset or 0)
        result = await self._observations(user).list_cohort(
            concept_id=int(concept.id),
            ordinal_value=ordinal_value,
            effective_from=_to_utc_naive(effective_from),
            effective_to=_to_utc_naive(effective_to),
            page=page,
        )
        self._audit.record_access(
            action="list",
            entity_type="observation",
            clinic_id=user.clinic_id,
            entity_public_id=concept.public_id,
            reason="cohort",
        )
        patients = await self._patients(user).public_ids_by_id(
            {int(row.patient_id) for row in result.items}
        )
        items = await self._reads_for_ids(user, result.items, patients, content_locale)
        await self._session.commit()
        return _page(items, result.total, result.limit, result.offset)

    async def update_observation(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        body: ObservationUpdate,
        content_locale: str,
    ) -> ObservationRead:
        self._bind(user)
        repo = self._observations(user)
        row = await repo.get_by_public_id(public_id)
        if row is None:
            raise ObservationNotFoundError(resource="observation", publicId=public_id)
        if int(row.version) != body.version:
            raise ObservationVersionConflictError(
                currentVersion=int(row.version),
                submittedVersion=body.version,
            )
        value = _value_draft(body)
        _check(value)
        concepts = await self._concepts(user, _value_codes(value))
        _apply_value(row, value, concepts)
        row.status = body.status
        row.map_region_code = body.map_region_code
        row.version = int(row.version) + 1
        row.updated_by_id = user.user_id
        await self._session.flush()
        patient = await self._patients(user).get(int(row.patient_id))
        if patient is None:
            raise NotFoundError(resource="patient")
        payload = await self._reads(user, patient, [row], content_locale)
        await self._session.commit()
        return payload[0]

    async def delete_observation(
        self,
        *,
        user: CurrentUser,
        public_id: str,
    ) -> None:
        self._bind(user)
        repo = self._observations(user)
        row = await repo.get_by_public_id(public_id)
        if row is None:
            raise ObservationNotFoundError(resource="observation", publicId=public_id)
        await repo.mark_deleted(row, user.user_id)
        await self._session.commit()

    async def record_snapshot(
        self,
        *,
        user: CurrentUser,
        patient_public_id: str,
        body: ExaminationSnapshotCreate,
    ) -> ExaminationSnapshotRead:
        self._bind(user)
        patient = await self._patient(user, patient_public_id)
        rendered_id = await self._attachment_id(
            user, body.rendered_svg_public_id, int(patient.id)
        )
        snapshot = ExaminationSnapshot(
            public_id=new_ulid(),
            clinic_id=user.clinic_id,
            patient_id=int(patient.id),
            encounter_public_id=body.encounter_public_id,
            map_id=body.map_id,
            laterality=body.laterality.value if body.laterality is not None else None,
            payload=body.payload,
            rendered_svg_id=rendered_id,
            created_by_id=user.user_id,
            updated_by_id=user.user_id,
        )
        await self._snapshots(user).add(snapshot)
        await self._session.commit()
        return _snapshot_read(
            snapshot,
            patient.public_id,
            body.rendered_svg_public_id,
        )

    async def list_snapshots(
        self,
        *,
        user: CurrentUser,
        patient_public_id: str,
        map_id: str | None,
        page: PaginationParams | None,
    ) -> PageSchema[ExaminationSnapshotRead]:
        self._bind(user)
        patient = await self._patient(user, patient_public_id)
        result = await self._snapshots(user).list_for_patient(
            int(patient.id),
            map_id=map_id,
            page=page,
        )
        svg_ids = {
            int(row.rendered_svg_id)
            for row in result.items
            if row.rendered_svg_id is not None
        }
        svg_public_ids = await AttachmentRepository(
            self._session, clinic_id=user.clinic_id
        ).public_ids_by_id(svg_ids)
        self._audit.record_access(
            action="list",
            entity_type="examination_snapshot",
            clinic_id=user.clinic_id,
            patient_id=int(patient.id),
            reason=map_id,
        )
        await self._session.commit()
        items = [
            _snapshot_read(
                row,
                patient.public_id,
                (
                    svg_public_ids.get(int(row.rendered_svg_id))
                    if row.rendered_svg_id is not None
                    else None
                ),
            )
            for row in result.items
        ]
        return _page(items, result.total, result.limit, result.offset)

    def _bind(self, user: CurrentUser) -> None:
        set_user_id(user.user_id)
        set_clinic_id(user.clinic_id)

    def _observations(self, user: CurrentUser) -> ObservationRepository:
        return ObservationRepository(self._session, clinic_id=user.clinic_id)

    def _snapshots(self, user: CurrentUser) -> ExaminationSnapshotRepository:
        return ExaminationSnapshotRepository(self._session, clinic_id=user.clinic_id)

    def _patients(self, user: CurrentUser) -> PatientRepository:
        return PatientRepository(self._session, clinic_id=user.clinic_id)

    async def _patient(self, user: CurrentUser, public_id: str) -> Patient:
        patient = await self._patients(user).get_visible(
            public_id,
            created_by_id=created_by_scope(user),
        )
        if patient is None:
            raise NotFoundError(resource="patient", publicId=public_id)
        return patient

    async def _concept(self, user: CurrentUser, code: str) -> Concept | None:
        return await TerminologyRepository(
            self._session, user.clinic_id
        ).get_concept_by_code(code)

    async def _concepts(self, user: CurrentUser, codes: set[str]) -> dict[str, Concept]:
        found: dict[str, Concept] = {}
        for code in codes:
            concept = await self._concept(user, code)
            if concept is None:
                raise ValidationError(reason="unknown_concept", conceptCode=code)
            found[code] = concept
        return found

    async def _labels(
        self,
        user: CurrentUser,
        concept_ids: set[int],
        content_locale: str,
    ) -> dict[int, tuple[str, str, str | None]]:
        clinic = await ClinicRepository(self._session).get(user.clinic_id)
        default_locale = clinic.default_locale if clinic is not None else content_locale
        return await self._patients(user).concept_labels(
            concept_ids,
            locale=content_locale,
            clinic_default_locale=default_locale,
        )

    async def _attachment_id(
        self,
        user: CurrentUser,
        public_id: str | None,
        patient_id: int,
    ) -> int | None:
        if public_id is None:
            return None
        attachment = await AttachmentRepository(
            self._session, clinic_id=user.clinic_id
        ).get_by_public_id(public_id)
        if attachment is None or attachment.patient_id != patient_id:
            raise NotFoundError(resource="attachment", publicId=public_id)
        return int(attachment.id)

    async def _reads(
        self,
        user: CurrentUser,
        patient: Patient,
        rows: list[Observation],
        content_locale: str,
    ) -> list[ObservationRead]:
        patients = {int(patient.id): patient.public_id}
        return await self._reads_for_ids(user, rows, patients, content_locale)

    async def _reads_for_ids(
        self,
        user: CurrentUser,
        rows: list[Observation],
        patients: dict[int, str],
        content_locale: str,
    ) -> list[ObservationRead]:
        labels = await self._labels(user, _concept_ids(rows), content_locale)
        users = await self._patients(user).user_public_ids(_user_ids(rows))
        return [
            _observation_read(row, patients[int(row.patient_id)], labels, users)
            for row in rows
        ]
