"""Patient registry use cases (P1-05)."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.audit.recorder import AuditRecorder
from ent.core.context import set_clinic_id, set_user_id
from ent.core.errors.exceptions import NotFoundError, ValidationError
from ent.core.events.bus import get_event_bus
from ent.core.schemas.base import PageMeta, PageSchema, PaginationParams
from ent.core.schemas.common import CodeableConcept
from ent.core.security.principal import CurrentUser
from ent.core.utils.ids import new_ulid
from ent.engines.patients.duplicates import is_likely_duplicate
from ent.engines.patients.name_normalize import build_name_normalized, normalize_phone
from ent.features.clinics.repository import ClinicRepository
from ent.features.patients.events import patient_created_event, patient_merged_event
from ent.features.patients.exceptions import (
    PatientIdempotencyMismatchError,
    PatientMergeInvalidError,
    PatientMrnConflictError,
    PatientPossibleDuplicateError,
    PatientVersionConflictError,
)
from ent.features.patients.models import (
    Patient,
    PatientAllergy,
    PatientFlag,
    PatientHistory,
    PatientIdentifier,
    PatientMedication,
    PatientMergeLog,
    PatientProblem,
    PatientRequestIdempotency,
)
from ent.features.patients.policies import created_by_scope
from ent.features.patients.repository import (
    PatientAllergyRepository,
    PatientFlagRepository,
    PatientHistoryRepository,
    PatientIdempotencyRepository,
    PatientIdentifierRepository,
    PatientMedicationRepository,
    PatientMergeLogRepository,
    PatientProblemRepository,
    PatientRepository,
    count_children,
)
from ent.features.patients.schemas.requests import (
    PatientAllergyCreate,
    PatientCreate,
    PatientFlagCreate,
    PatientFlagUpdate,
    PatientHistoryCreate,
    PatientIdentifierCreate,
    PatientMedicationCreate,
    PatientMergeRequest,
    PatientProblemCreate,
    PatientUpdate,
)
from ent.features.patients.schemas.responses import (
    PatientAllergyRead,
    PatientFlagRead,
    PatientHistoryRead,
    PatientIdentifierRead,
    PatientMedicationRead,
    PatientMergeRead,
    PatientProblemRead,
    PatientRead,
    PatientSummaryRead,
)

_CHART_LIMIT = 100


class PatientService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._audit = AuditRecorder(session)

    async def list_patients(
        self,
        *,
        user: CurrentUser,
        search: str | None,
        birth_date: Any,
        sex: str | None,
        flag_code: str | None,
        sort: str | None,
        page: PaginationParams | None,
    ) -> PageSchema[PatientSummaryRead]:
        self._bind(user)
        repo = self._patients(user)
        result = await repo.search(
            search=search,
            birth_date=birth_date,
            sex=sex,
            flag_code=flag_code,
            created_by_id=created_by_scope(user),
            sort=sort,
            page=page,
        )
        self._audit.record_access(
            action="list",
            entity_type="patient",
            clinic_id=user.clinic_id,
            reason=(search or "")[:255] or None,
        )
        await self._session.commit()
        return PageSchema(
            items=[_summary(row) for row in result.items],
            page=PageMeta(
                total=result.total,
                limit=result.limit,
                offset=result.offset,
                next_cursor=result.next_cursor,
            ),
        )

    async def create_patient(
        self,
        *,
        user: CurrentUser,
        body: PatientCreate,
        idempotency_key: str | None,
        content_locale: str = "fr",
    ) -> PatientRead:
        self._bind(user)
        replay = await self._replay(
            user, idempotency_key, "patient.create", body.model_dump(mode="json")
        )
        if replay is not None:
            return await self.get_patient(
                user=user,
                public_id=replay,
                content_locale=content_locale,
            )

        repo = self._patients(user)
        await self._assert_locale(user, body.preferred_locale)
        name_normalized = _names(body)
        phone_primary = normalize_phone(body.phone_primary)
        phone_secondary = normalize_phone(body.phone_secondary)
        if not body.confirm_duplicate:
            await self._raise_if_duplicate(
                repo,
                name_normalized=name_normalized,
                birth_date=body.birth_date,
                phones=(phone_primary, phone_secondary),
            )

        mrn = body.mrn or await repo.allocate_mrn()
        if await _mrn_taken(repo, mrn):
            raise PatientMrnConflictError(mrn=mrn)

        patient = Patient(
            public_id=new_ulid(),
            clinic_id=user.clinic_id,
            mrn=mrn,
            first_name=body.first_name.strip(),
            last_name=body.last_name.strip(),
            first_name_alt=_blank(body.first_name_alt),
            last_name_alt=_blank(body.last_name_alt),
            name_normalized=name_normalized,
            birth_date=body.birth_date,
            birth_date_is_estimated=body.birth_date_is_estimated,
            sex=body.sex,
            preferred_locale=body.preferred_locale,
            phone_primary=phone_primary,
            phone_secondary=phone_secondary,
            email=_blank(body.email),
            address_line1=body.address_line1,
            address_line2=body.address_line2,
            city=body.city,
            postal_code=body.postal_code,
            country_code=body.country_code,
            occupation=body.occupation,
            noise_exposure=body.noise_exposure,
            smoking_status=body.smoking_status,
            alcohol_status=body.alcohol_status,
            insurance_number=body.insurance_number,
            referring_doctor_name=body.referring_doctor_name,
            referring_doctor_phone=normalize_phone(body.referring_doctor_phone),
            referring_doctor_email=_blank(body.referring_doctor_email),
            referring_doctor_locale=body.referring_doctor_locale,
            guardian_name=body.guardian_name,
            guardian_relation=body.guardian_relation,
            emergency_contact_name=body.emergency_contact_name,
            emergency_contact_phone=normalize_phone(body.emergency_contact_phone),
            consent_sms=body.consent_sms,
            consent_email=body.consent_email,
            consent_teaching=body.consent_teaching,
            is_deceased=body.is_deceased,
            deceased_date=body.deceased_date,
            created_by_id=user.user_id,
            updated_by_id=user.user_id,
        )
        await repo.add(patient)
        for identifier in body.identifiers:
            await self._add_identifier(user, patient, identifier)
        for allergy in body.allergies:
            await self._add_allergy(user, patient, allergy)
        for medication in body.medications:
            await self._add_medication(user, patient, medication)
        for flag in body.flags:
            await self._add_flag(user, patient, flag)
        for problem in body.problems:
            await self._add_problem(user, patient, problem)
        for history_item in body.history:
            await self._add_history(user, patient, history_item)
        await self._store_idempotency(
            user,
            idempotency_key,
            "patient.create",
            body.model_dump(mode="json"),
            patient.public_id,
        )
        await self._session.commit()
        await self._session.refresh(patient)
        await get_event_bus().publish(
            patient_created_event(
                patient_public_id=patient.public_id,
                clinic_id=user.clinic_id,
            )
        )
        return await self._read(user, patient, content_locale=content_locale)

    async def get_patient(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        content_locale: str = "fr",
    ) -> PatientRead:
        self._bind(user)
        patient = await self._visible(user, public_id)
        self._audit.record_access(
            action="read",
            entity_type="patient",
            clinic_id=user.clinic_id,
            entity_id=patient.id,
            entity_public_id=patient.public_id,
            patient_id=patient.id,
        )
        await self._session.commit()
        return await self._read(user, patient, content_locale=content_locale)

    async def update_patient(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        body: PatientUpdate,
        content_locale: str = "fr",
    ) -> PatientRead:
        self._bind(user)
        patient = await self._visible(user, public_id)
        if patient.version != body.version:
            raise PatientVersionConflictError(
                public_id=public_id, version=patient.version
            )
        data = body.model_dump(exclude_unset=True)
        data.pop("version", None)
        if "preferred_locale" in data and data["preferred_locale"] is not None:
            await self._assert_locale(user, str(data["preferred_locale"]))
        for field in (
            "phone_primary",
            "phone_secondary",
            "referring_doctor_phone",
            "emergency_contact_phone",
        ):
            if field in data:
                data[field] = normalize_phone(data[field])
        for field, value in data.items():
            setattr(patient, field, value)
        if {"first_name", "last_name", "first_name_alt", "last_name_alt"} & data.keys():
            patient.name_normalized = build_name_normalized(
                first_name=patient.first_name,
                last_name=patient.last_name,
                first_name_alt=patient.first_name_alt,
                last_name_alt=patient.last_name_alt,
            )
        if patient.deceased_date is not None and not patient.is_deceased:
            raise ValidationError(reason="deceased_date_requires_is_deceased")
        if (
            patient.deceased_date is not None
            and patient.deceased_date < patient.birth_date
        ):
            raise ValidationError(reason="deceased_date_before_birth_date")
        if data:
            patient.version += 1
            patient.updated_by_id = user.user_id
        await self._session.commit()
        return await self._read(user, patient, content_locale=content_locale)

    async def merge_patients(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        body: PatientMergeRequest,
    ) -> PatientMergeRead:
        self._bind(user)
        if public_id == body.merged_patient_id:
            raise PatientMergeInvalidError(reason="same_patient")
        repo = self._patients(user)
        survivor = await repo.get_visible(public_id, created_by_id=None)
        merged = await repo.get_visible(body.merged_patient_id, created_by_id=None)
        if survivor is None:
            raise NotFoundError(resource="patient", public_id=public_id)
        if merged is None:
            raise NotFoundError(resource="patient", public_id=body.merged_patient_id)
        moved = await repo.reassign_chart(
            from_patient_id=merged.id,
            to_patient_id=survivor.id,
            actor_id=user.user_id,
        )
        merged.deleted_at = datetime.now(UTC).replace(tzinfo=None)
        merged.deleted_by_id = user.user_id
        merged.updated_by_id = user.user_id
        log = PatientMergeLog(
            public_id=new_ulid(),
            clinic_id=user.clinic_id,
            surviving_patient_id=survivor.id,
            merged_patient_id=merged.id,
            merged_by_id=user.user_id,
            reason=body.reason,
            payload={
                "moved_public_ids": moved,
                "surviving_mrn": survivor.mrn,
                "merged_mrn": merged.mrn,
            },
            created_by_id=user.user_id,
            updated_by_id=user.user_id,
        )
        await PatientMergeLogRepository(self._session, clinic_id=user.clinic_id).add(
            log
        )
        self._audit.record_write(
            action="merge",
            entity=log,
            clinic_id=user.clinic_id,
            patient_id=survivor.id,
            reason=body.reason,
        )
        await self._session.commit()
        await get_event_bus().publish(
            patient_merged_event(
                surviving_public_id=survivor.public_id,
                merged_public_id=merged.public_id,
                clinic_id=user.clinic_id,
            )
        )
        return PatientMergeRead(
            surviving_patient_id=survivor.public_id,
            merged_patient_id=merged.public_id,
            merge_log_public_id=log.public_id,
        )

    async def timeline(
        self, *, user: CurrentUser, public_id: str
    ) -> PageSchema[PatientSummaryRead]:
        """Empty until encounters exist. Confirms the patient is visible."""

        self._bind(user)
        await self._visible(user, public_id)
        return PageSchema(
            items=[],
            page=PageMeta(total=0, limit=25, offset=0, next_cursor=None),
        )

    async def list_identifiers(
        self, *, user: CurrentUser, public_id: str, page: PaginationParams
    ) -> PageSchema[PatientIdentifierRead]:
        patient = await self._visible(user, public_id)
        repo = PatientIdentifierRepository(self._session, clinic_id=user.clinic_id)
        items = await repo.list_for_patient(
            patient.id, limit=page.limit, offset=page.offset or 0
        )
        total = await count_children(repo, patient.id)
        return _page([_identifier(row) for row in items], total, page)

    async def add_identifier(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        body: PatientIdentifierCreate,
        idempotency_key: str | None,
    ) -> PatientIdentifierRead:
        self._bind(user)
        replay = await self._replay(
            user,
            idempotency_key,
            "patient.identifier.create",
            body.model_dump(mode="json"),
        )
        patient = await self._visible(user, public_id)
        if replay is not None:
            return await self._identifier_by_public_id(user, patient.id, replay)
        row = await self._add_identifier(user, patient, body)
        await self._store_idempotency(
            user,
            idempotency_key,
            "patient.identifier.create",
            body.model_dump(mode="json"),
            row.public_id,
        )
        await self._session.commit()
        return _identifier(row)

    async def list_allergies(
        self, *, user: CurrentUser, public_id: str, page: PaginationParams
    ) -> PageSchema[PatientAllergyRead]:
        patient = await self._visible(user, public_id)
        repo = PatientAllergyRepository(self._session, clinic_id=user.clinic_id)
        items = await repo.list_for_patient(
            patient.id, limit=page.limit, offset=page.offset or 0
        )
        total = await count_children(repo, patient.id)
        labels = await self._concept_labels(user,
            _concept_ids(items, "substance_concept_id", "reaction_concept_id")
        )
        return _page([_allergy(row, labels) for row in items], total, page)

    async def add_allergy(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        body: PatientAllergyCreate,
        idempotency_key: str | None,
    ) -> PatientAllergyRead:
        self._bind(user)
        patient = await self._visible(user, public_id)
        replay = await self._replay(
            user,
            idempotency_key,
            "patient.allergy.create",
            body.model_dump(mode="json"),
        )
        if replay is not None:
            return await self._allergy_by_public_id(user, patient.id, replay)
        row = await self._add_allergy(user, patient, body)
        await self._store_idempotency(
            user,
            idempotency_key,
            "patient.allergy.create",
            body.model_dump(mode="json"),
            row.public_id,
        )
        await self._session.commit()
        labels = await self._concept_labels(user,
            _concept_ids([row], "substance_concept_id", "reaction_concept_id")
        )
        return _allergy(row, labels)

    async def list_medications(
        self, *, user: CurrentUser, public_id: str, page: PaginationParams
    ) -> PageSchema[PatientMedicationRead]:
        patient = await self._visible(user, public_id)
        repo = PatientMedicationRepository(self._session, clinic_id=user.clinic_id)
        items = await repo.list_for_patient(
            patient.id, limit=page.limit, offset=page.offset or 0
        )
        total = await count_children(repo, patient.id)
        return _page([_medication(row) for row in items], total, page)

    async def add_medication(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        body: PatientMedicationCreate,
        idempotency_key: str | None,
    ) -> PatientMedicationRead:
        self._bind(user)
        patient = await self._visible(user, public_id)
        replay = await self._replay(
            user,
            idempotency_key,
            "patient.medication.create",
            body.model_dump(mode="json"),
        )
        if replay is not None:
            return await self._medication_by_public_id(user, patient.id, replay)
        row = await self._add_medication(user, patient, body)
        await self._store_idempotency(
            user,
            idempotency_key,
            "patient.medication.create",
            body.model_dump(mode="json"),
            row.public_id,
        )
        await self._session.commit()
        return _medication(row)

    async def list_flags(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        flag_code: str | None,
        active_only: bool,
        page: PaginationParams,
    ) -> PageSchema[PatientFlagRead]:
        patient = await self._visible(user, public_id)
        repo = PatientFlagRepository(self._session, clinic_id=user.clinic_id)
        if active_only or flag_code is not None:
            items = await repo.list_active(
                flag_code=flag_code,
                patient_id=patient.id,
                limit=page.limit,
            )
            if not active_only and flag_code is not None:
                items = [
                    row
                    for row in await repo.list_for_patient(patient.id, limit=page.limit)
                    if row.flag_code == flag_code
                ]
        else:
            items = await repo.list_for_patient(
                patient.id, limit=page.limit, offset=page.offset or 0
            )
        users = await self._patients(user).user_public_ids(
            {row.created_by_id for row in items if row.created_by_id is not None}
        )
        return _page([_flag(row, users) for row in items], len(items), page)

    async def add_flag(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        body: PatientFlagCreate,
        idempotency_key: str | None,
    ) -> PatientFlagRead:
        self._bind(user)
        patient = await self._visible(user, public_id)
        replay = await self._replay(
            user, idempotency_key, "patient.flag.create", body.model_dump(mode="json")
        )
        if replay is not None:
            return await self._flag_by_public_id(user, patient.id, replay)
        row = await self._add_flag(user, patient, body)
        await self._store_idempotency(
            user,
            idempotency_key,
            "patient.flag.create",
            body.model_dump(mode="json"),
            row.public_id,
        )
        await self._session.commit()
        users = await self._patients(user).user_public_ids({user.user_id})
        return _flag(row, users)

    async def update_flag(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        flag_id: str,
        body: PatientFlagUpdate,
    ) -> PatientFlagRead:
        self._bind(user)
        patient = await self._visible(user, public_id)
        repo = PatientFlagRepository(self._session, clinic_id=user.clinic_id)
        row = await repo.get_by_public_id(flag_id)
        if row is None or row.patient_id != patient.id:
            raise NotFoundError(resource="patient_flag", public_id=flag_id)
        if row.version != body.version:
            raise PatientVersionConflictError(public_id=flag_id, version=row.version)
        data = body.model_dump(exclude_unset=True)
        data.pop("version", None)
        for field, value in data.items():
            if field == "laterality" and value is not None:
                value = value.value if hasattr(value, "value") else value
            setattr(row, field, value)
        if row.ended_on is not None and row.ended_on < row.started_on:
            raise ValidationError(reason="ended_on_before_started_on")
        if data:
            row.version += 1
            row.updated_by_id = user.user_id
        await self._session.commit()
        users = await self._patients(user).user_public_ids(
            {row.created_by_id} if row.created_by_id is not None else set()
        )
        return _flag(row, users)

    async def list_problems(
        self, *, user: CurrentUser, public_id: str, page: PaginationParams
    ) -> PageSchema[PatientProblemRead]:
        patient = await self._visible(user, public_id)
        repo = PatientProblemRepository(self._session, clinic_id=user.clinic_id)
        items = await repo.list_for_patient(
            patient.id, limit=page.limit, offset=page.offset or 0
        )
        total = await count_children(repo, patient.id)
        labels = await self._concept_labels(user,
            _concept_ids(items, "diagnosis_concept_id")
        )
        return _page([_problem(row, labels) for row in items], total, page)

    async def add_problem(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        body: PatientProblemCreate,
        idempotency_key: str | None,
    ) -> PatientProblemRead:
        self._bind(user)
        patient = await self._visible(user, public_id)
        replay = await self._replay(
            user,
            idempotency_key,
            "patient.problem.create",
            body.model_dump(mode="json"),
        )
        if replay is not None:
            return await self._problem_by_public_id(user, patient.id, replay)
        row = await self._add_problem(user, patient, body)
        await self._store_idempotency(
            user,
            idempotency_key,
            "patient.problem.create",
            body.model_dump(mode="json"),
            row.public_id,
        )
        await self._session.commit()
        labels = await self._concept_labels(user,{row.diagnosis_concept_id})
        return _problem(row, labels)

    async def list_history(
        self, *, user: CurrentUser, public_id: str, page: PaginationParams
    ) -> PageSchema[PatientHistoryRead]:
        patient = await self._visible(user, public_id)
        repo = PatientHistoryRepository(self._session, clinic_id=user.clinic_id)
        items = await repo.list_for_patient(
            patient.id, limit=page.limit, offset=page.offset or 0
        )
        total = await count_children(repo, patient.id)
        labels = await self._concept_labels(user,
            {row.concept_id for row in items if row.concept_id is not None}
        )
        return _page([_history(row, labels) for row in items], total, page)

    async def add_history(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        body: PatientHistoryCreate,
        idempotency_key: str | None,
    ) -> PatientHistoryRead:
        self._bind(user)
        patient = await self._visible(user, public_id)
        replay = await self._replay(
            user,
            idempotency_key,
            "patient.history.create",
            body.model_dump(mode="json"),
        )
        if replay is not None:
            return await self._history_by_public_id(user, patient.id, replay)
        row = await self._add_history(user, patient, body)
        await self._store_idempotency(
            user,
            idempotency_key,
            "patient.history.create",
            body.model_dump(mode="json"),
            row.public_id,
        )
        await self._session.commit()
        labels = await self._concept_labels(user,
            {row.concept_id} if row.concept_id is not None else set()
        )
        return _history(row, labels)

    async def delete_identifier(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        identifier_id: str,
    ) -> None:
        self._bind(user)
        patient = await self._visible(user, public_id)
        repo = PatientIdentifierRepository(self._session, clinic_id=user.clinic_id)
        row = await repo.get_by_public_id(identifier_id)
        if row is None or row.patient_id != patient.id:
            raise NotFoundError(resource="patient_identifier", public_id=identifier_id)
        await repo.soft_delete(row.id, user.user_id)
        await self._session.commit()

    async def delete_allergy(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        allergy_id: str,
    ) -> None:
        self._bind(user)
        patient = await self._visible(user, public_id)
        repo = PatientAllergyRepository(self._session, clinic_id=user.clinic_id)
        row = await repo.get_by_public_id(allergy_id)
        if row is None or row.patient_id != patient.id:
            raise NotFoundError(resource="patient_allergy", public_id=allergy_id)
        await repo.soft_delete(row.id, user.user_id)
        await self._session.commit()

    async def delete_medication(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        medication_id: str,
    ) -> None:
        self._bind(user)
        patient = await self._visible(user, public_id)
        repo = PatientMedicationRepository(self._session, clinic_id=user.clinic_id)
        row = await repo.get_by_public_id(medication_id)
        if row is None or row.patient_id != patient.id:
            raise NotFoundError(resource="patient_medication", public_id=medication_id)
        await repo.soft_delete(row.id, user.user_id)
        await self._session.commit()

    async def delete_problem(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        problem_id: str,
    ) -> None:
        self._bind(user)
        patient = await self._visible(user, public_id)
        repo = PatientProblemRepository(self._session, clinic_id=user.clinic_id)
        row = await repo.get_by_public_id(problem_id)
        if row is None or row.patient_id != patient.id:
            raise NotFoundError(resource="patient_problem", public_id=problem_id)
        await repo.soft_delete(row.id, user.user_id)
        await self._session.commit()

    async def delete_history(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        history_id: str,
    ) -> None:
        self._bind(user)
        patient = await self._visible(user, public_id)
        repo = PatientHistoryRepository(self._session, clinic_id=user.clinic_id)
        row = await repo.get_by_public_id(history_id)
        if row is None or row.patient_id != patient.id:
            raise NotFoundError(resource="patient_history", public_id=history_id)
        await repo.soft_delete(row.id, user.user_id)
        await self._session.commit()

    def _bind(self, user: CurrentUser) -> None:
        set_user_id(user.user_id)
        set_clinic_id(user.clinic_id)

    def _patients(self, user: CurrentUser) -> PatientRepository:
        return PatientRepository(self._session, clinic_id=user.clinic_id)

    async def _concept_labels(
        self,
        user: CurrentUser,
        concept_ids: set[int],
        *,
        content_locale: str = "fr",
    ) -> dict[int, tuple[str, str, str | None]]:
        clinic = await ClinicRepository(self._session).get(user.clinic_id)
        default = clinic.default_locale if clinic else "fr"
        return await self._patients(user).concept_labels(
            concept_ids,
            locale=content_locale,
            clinic_default_locale=default,
        )

    async def _visible(self, user: CurrentUser, public_id: str) -> Patient:
        self._bind(user)
        patient = await self._patients(user).get_visible(
            public_id, created_by_id=created_by_scope(user)
        )
        if patient is None:
            raise NotFoundError(resource="patient", public_id=public_id)
        return patient

    async def _assert_locale(self, user: CurrentUser, locale: str) -> None:
        clinic = await ClinicRepository(self._session).get(user.clinic_id)
        if clinic is None:
            raise NotFoundError(resource="clinic", public_id=user.clinic_public_id)
        supported = clinic.supported_locales
        if not isinstance(supported, list) or locale not in supported:
            raise ValidationError(
                reason="preferred_locale_not_supported", locale=locale
            )

    async def _raise_if_duplicate(
        self,
        repo: PatientRepository,
        *,
        name_normalized: str,
        birth_date: Any,
        phones: tuple[str | None, ...],
    ) -> None:
        candidates = await repo.find_duplicate_candidates(
            name_normalized=name_normalized,
            birth_date=birth_date,
            phones=phones,
        )
        matches = [
            row.public_id
            for row in candidates
            if is_likely_duplicate(
                left_name_normalized=name_normalized,
                left_birth_date=birth_date,
                left_phones=phones,
                right_name_normalized=row.name_normalized,
                right_birth_date=row.birth_date,
                right_phones=(row.phone_primary, row.phone_secondary),
            )
        ]
        if matches:
            raise PatientPossibleDuplicateError(candidates=matches)

    async def _replay(
        self,
        user: CurrentUser,
        key: str | None,
        operation: str,
        payload: dict[str, Any],
    ) -> str | None:
        if not key:
            return None
        existing = await PatientIdempotencyRepository(
            self._session, clinic_id=user.clinic_id
        ).get_by_key(key)
        if existing is None:
            return None
        digest = _request_hash(operation, payload)
        if existing.request_hash != digest or existing.resource_type != operation:
            raise PatientIdempotencyMismatchError()
        return existing.resource_public_id

    async def _store_idempotency(
        self,
        user: CurrentUser,
        key: str | None,
        operation: str,
        payload: dict[str, Any],
        resource_public_id: str,
    ) -> None:
        if not key:
            return
        row = PatientRequestIdempotency(
            public_id=new_ulid(),
            clinic_id=user.clinic_id,
            idempotency_key=key,
            request_hash=_request_hash(operation, payload),
            resource_type=operation,
            resource_public_id=resource_public_id,
        )
        await PatientIdempotencyRepository(self._session, clinic_id=user.clinic_id).add(
            row
        )

    async def _concept_id(self, user: CurrentUser, public_id: str) -> int:
        concept = await self._patients(user).concept_by_public_id(public_id)
        if concept is None:
            raise NotFoundError(resource="concept", public_id=public_id)
        return concept.id

    async def _add_identifier(
        self, user: CurrentUser, patient: Patient, body: PatientIdentifierCreate
    ) -> PatientIdentifier:
        row = PatientIdentifier(
            public_id=new_ulid(),
            clinic_id=user.clinic_id,
            patient_id=patient.id,
            type=body.type,
            value=body.value.strip(),
            issuing_country=body.issuing_country,
            created_by_id=user.user_id,
            updated_by_id=user.user_id,
        )
        await PatientIdentifierRepository(self._session, clinic_id=user.clinic_id).add(
            row
        )
        return row

    async def _add_allergy(
        self, user: CurrentUser, patient: Patient, body: PatientAllergyCreate
    ) -> PatientAllergy:
        reaction_id = None
        if body.reaction_concept_id is not None:
            reaction_id = await self._concept_id(user, body.reaction_concept_id)
        row = PatientAllergy(
            public_id=new_ulid(),
            clinic_id=user.clinic_id,
            patient_id=patient.id,
            substance_concept_id=await self._concept_id(
                user, body.substance_concept_id
            ),
            category=body.category,
            reaction_concept_id=reaction_id,
            severity=body.severity,
            onset_date=body.onset_date,
            is_active=body.is_active,
            note=body.note,
            created_by_id=user.user_id,
            updated_by_id=user.user_id,
        )
        await PatientAllergyRepository(self._session, clinic_id=user.clinic_id).add(row)
        return row

    async def _add_medication(
        self, user: CurrentUser, patient: Patient, body: PatientMedicationCreate
    ) -> PatientMedication:
        row = PatientMedication(
            public_id=new_ulid(),
            clinic_id=user.clinic_id,
            patient_id=patient.id,
            free_text_name=body.free_text_name.strip(),
            dose=body.dose,
            frequency=body.frequency,
            route=body.route,
            started_on=body.started_on,
            stopped_on=body.stopped_on,
            is_active=body.is_active,
            is_anticoagulant=body.is_anticoagulant,
            is_ototoxic=body.is_ototoxic,
            source=body.source,
            created_by_id=user.user_id,
            updated_by_id=user.user_id,
        )
        await PatientMedicationRepository(self._session, clinic_id=user.clinic_id).add(
            row
        )
        return row

    async def _add_flag(
        self, user: CurrentUser, patient: Patient, body: PatientFlagCreate
    ) -> PatientFlag:
        laterality = body.laterality.value if body.laterality is not None else None
        row = PatientFlag(
            public_id=new_ulid(),
            clinic_id=user.clinic_id,
            patient_id=patient.id,
            flag_code=body.flag_code,
            laterality=laterality,
            severity=body.severity,
            detail=body.detail,
            started_on=body.started_on,
            ended_on=body.ended_on,
            is_auto=body.is_auto,
            created_by_id=user.user_id,
            updated_by_id=user.user_id,
        )
        await PatientFlagRepository(self._session, clinic_id=user.clinic_id).add(row)
        return row

    async def _add_problem(
        self, user: CurrentUser, patient: Patient, body: PatientProblemCreate
    ) -> PatientProblem:
        row = PatientProblem(
            public_id=new_ulid(),
            clinic_id=user.clinic_id,
            patient_id=patient.id,
            diagnosis_concept_id=await self._concept_id(
                user, body.diagnosis_concept_id
            ),
            laterality=body.laterality.value,
            status=body.status,
            onset_date=body.onset_date,
            resolved_date=body.resolved_date,
            note=body.note,
            created_by_id=user.user_id,
            updated_by_id=user.user_id,
        )
        await PatientProblemRepository(self._session, clinic_id=user.clinic_id).add(row)
        return row

    async def _add_history(
        self, user: CurrentUser, patient: Patient, body: PatientHistoryCreate
    ) -> PatientHistory:
        concept_id = None
        if body.concept_id is not None:
            concept_id = await self._concept_id(user, body.concept_id)
        laterality = body.laterality.value if body.laterality is not None else None
        row = PatientHistory(
            public_id=new_ulid(),
            clinic_id=user.clinic_id,
            patient_id=patient.id,
            category=body.category,
            concept_id=concept_id,
            free_text=body.free_text,
            laterality=laterality,
            occurred_year=body.occurred_year,
            occurred_date=body.occurred_date,
            detail=body.detail,
            created_by_id=user.user_id,
            updated_by_id=user.user_id,
        )
        await PatientHistoryRepository(self._session, clinic_id=user.clinic_id).add(row)
        return row

    async def _read(
        self,
        user: CurrentUser,
        patient: Patient,
        *,
        content_locale: str = "fr",
    ) -> PatientRead:
        repo = self._patients(user)
        identifiers = await PatientIdentifierRepository(
            self._session, clinic_id=user.clinic_id
        ).list_for_patient(patient.id, limit=_CHART_LIMIT)
        allergies = await PatientAllergyRepository(
            self._session, clinic_id=user.clinic_id
        ).list_for_patient(patient.id, limit=_CHART_LIMIT)
        medications = await PatientMedicationRepository(
            self._session, clinic_id=user.clinic_id
        ).list_for_patient(patient.id, limit=_CHART_LIMIT)
        flags = await PatientFlagRepository(
            self._session, clinic_id=user.clinic_id
        ).list_for_patient(patient.id, limit=_CHART_LIMIT)
        problems = await PatientProblemRepository(
            self._session, clinic_id=user.clinic_id
        ).list_for_patient(patient.id, limit=_CHART_LIMIT)
        history = await PatientHistoryRepository(
            self._session, clinic_id=user.clinic_id
        ).list_for_patient(patient.id, limit=_CHART_LIMIT)
        concept_ids: set[int] = set()
        concept_ids.update(
            _concept_ids(allergies, "substance_concept_id", "reaction_concept_id")
        )
        concept_ids.update(_concept_ids(problems, "diagnosis_concept_id"))
        concept_ids.update(
            {row.concept_id for row in history if row.concept_id is not None}
        )
        labels = await self._concept_labels(
            user,
            concept_ids,
            content_locale=content_locale,
        )
        users = await repo.user_public_ids(
            {row.created_by_id for row in flags if row.created_by_id is not None}
        )
        summary = _summary(patient)
        return PatientRead(
            **summary.model_dump(),
            phone_secondary=patient.phone_secondary,
            email=patient.email,
            address_line1=patient.address_line1,
            address_line2=patient.address_line2,
            city=patient.city,
            postal_code=patient.postal_code,
            country_code=patient.country_code,
            occupation=patient.occupation,
            noise_exposure=patient.noise_exposure,
            smoking_status=patient.smoking_status,
            alcohol_status=patient.alcohol_status,
            insurance_number=patient.insurance_number,
            referring_doctor_name=patient.referring_doctor_name,
            referring_doctor_phone=patient.referring_doctor_phone,
            referring_doctor_email=patient.referring_doctor_email,
            referring_doctor_locale=patient.referring_doctor_locale,
            guardian_name=patient.guardian_name,
            guardian_relation=patient.guardian_relation,
            emergency_contact_name=patient.emergency_contact_name,
            emergency_contact_phone=patient.emergency_contact_phone,
            consent_sms=patient.consent_sms,
            consent_email=patient.consent_email,
            consent_teaching=patient.consent_teaching,
            is_deceased=patient.is_deceased,
            deceased_date=patient.deceased_date,
            created_at=patient.created_at,
            updated_at=patient.updated_at,
            identifiers=[_identifier(row) for row in identifiers],
            allergies=[_allergy(row, labels) for row in allergies],
            medications=[_medication(row) for row in medications],
            flags=[_flag(row, users) for row in flags],
            problems=[_problem(row, labels) for row in problems],
            history=[_history(row, labels) for row in history],
        )

    async def _identifier_by_public_id(
        self, user: CurrentUser, patient_id: int, public_id: str
    ) -> PatientIdentifierRead:
        row = await PatientIdentifierRepository(
            self._session, clinic_id=user.clinic_id
        ).get_by_public_id(public_id)
        if row is None or row.patient_id != patient_id:
            raise NotFoundError(resource="patient_identifier", public_id=public_id)
        return _identifier(row)

    async def _allergy_by_public_id(
        self, user: CurrentUser, patient_id: int, public_id: str
    ) -> PatientAllergyRead:
        row = await PatientAllergyRepository(
            self._session, clinic_id=user.clinic_id
        ).get_by_public_id(public_id)
        if row is None or row.patient_id != patient_id:
            raise NotFoundError(resource="patient_allergy", public_id=public_id)
        labels = await self._concept_labels(user,
            _concept_ids([row], "substance_concept_id", "reaction_concept_id")
        )
        return _allergy(row, labels)

    async def _medication_by_public_id(
        self, user: CurrentUser, patient_id: int, public_id: str
    ) -> PatientMedicationRead:
        row = await PatientMedicationRepository(
            self._session, clinic_id=user.clinic_id
        ).get_by_public_id(public_id)
        if row is None or row.patient_id != patient_id:
            raise NotFoundError(resource="patient_medication", public_id=public_id)
        return _medication(row)

    async def _flag_by_public_id(
        self, user: CurrentUser, patient_id: int, public_id: str
    ) -> PatientFlagRead:
        row = await PatientFlagRepository(
            self._session, clinic_id=user.clinic_id
        ).get_by_public_id(public_id)
        if row is None or row.patient_id != patient_id:
            raise NotFoundError(resource="patient_flag", public_id=public_id)
        users = await self._patients(user).user_public_ids(
            {row.created_by_id} if row.created_by_id is not None else set()
        )
        return _flag(row, users)

    async def _problem_by_public_id(
        self, user: CurrentUser, patient_id: int, public_id: str
    ) -> PatientProblemRead:
        row = await PatientProblemRepository(
            self._session, clinic_id=user.clinic_id
        ).get_by_public_id(public_id)
        if row is None or row.patient_id != patient_id:
            raise NotFoundError(resource="patient_problem", public_id=public_id)
        labels = await self._concept_labels(user,{row.diagnosis_concept_id})
        return _problem(row, labels)

    async def _history_by_public_id(
        self, user: CurrentUser, patient_id: int, public_id: str
    ) -> PatientHistoryRead:
        row = await PatientHistoryRepository(
            self._session, clinic_id=user.clinic_id
        ).get_by_public_id(public_id)
        if row is None or row.patient_id != patient_id:
            raise NotFoundError(resource="patient_history", public_id=public_id)
        labels = await self._concept_labels(user,
            {row.concept_id} if row.concept_id is not None else set()
        )
        return _history(row, labels)


def _names(body: PatientCreate) -> str:
    return build_name_normalized(
        first_name=body.first_name,
        last_name=body.last_name,
        first_name_alt=body.first_name_alt,
        last_name_alt=body.last_name_alt,
    )


def _blank(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _request_hash(operation: str, payload: dict[str, Any]) -> str:
    raw = json.dumps(
        {"operation": operation, "body": payload},
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


async def _mrn_taken(repo: PatientRepository, mrn: str) -> bool:
    found = await repo.session.execute(
        repo._base_query().where(Patient.mrn == mrn).where(Patient.deleted_at.is_(None))
    )
    # Soft-deleted MRNs must stay reserved. Query without the deleted filter.
    if found.scalar_one_or_none() is not None:
        return True
    from sqlalchemy import select

    reserved = await repo.session.execute(
        select(Patient.id).where(
            Patient.clinic_id == repo.clinic_id,
            Patient.mrn == mrn,
        )
    )
    return reserved.scalar_one_or_none() is not None


def _summary(patient: Patient) -> PatientSummaryRead:
    return PatientSummaryRead(
        public_id=patient.public_id,
        mrn=patient.mrn,
        first_name=patient.first_name,
        last_name=patient.last_name,
        first_name_alt=patient.first_name_alt,
        last_name_alt=patient.last_name_alt,
        birth_date=patient.birth_date,
        birth_date_is_estimated=patient.birth_date_is_estimated,
        sex=patient.sex,
        preferred_locale=patient.preferred_locale,
        phone_primary=patient.phone_primary,
        version=patient.version,
    )


def _page(items: list[Any], total: int, page: PaginationParams) -> PageSchema[Any]:
    return PageSchema(
        items=items,
        page=PageMeta(
            total=total,
            limit=page.limit,
            offset=page.offset or 0,
            next_cursor=None,
        ),
    )


def _concept_ids(rows: list[Any], *fields: str) -> set[int]:
    found: set[int] = set()
    for row in rows:
        for field in fields:
            value = getattr(row, field)
            if value is not None:
                found.add(int(value))
    return found


def _concept(
    labels: dict[int, tuple[str, str, str | None]],
    concept_id: int,
) -> CodeableConcept:
    public_id, code, display = labels[concept_id]
    return CodeableConcept(concept_id=public_id, code=code, display=display)


def _identifier(row: PatientIdentifier) -> PatientIdentifierRead:
    return PatientIdentifierRead(
        public_id=row.public_id,
        type=row.type,
        value=row.value,
        issuing_country=row.issuing_country,
        version=row.version,
    )


def _allergy(
    row: PatientAllergy,
    labels: dict[int, tuple[str, str, str | None]],
) -> PatientAllergyRead:
    reaction = None
    if row.reaction_concept_id is not None:
        reaction = _concept(labels, row.reaction_concept_id)
    return PatientAllergyRead(
        public_id=row.public_id,
        substance=_concept(labels, row.substance_concept_id),
        category=row.category,
        reaction=reaction,
        severity=row.severity,
        onset_date=row.onset_date,
        is_active=row.is_active,
        note=row.note,
        version=row.version,
    )


def _medication(row: PatientMedication) -> PatientMedicationRead:
    return PatientMedicationRead(
        public_id=row.public_id,
        free_text_name=row.free_text_name,
        dose=row.dose,
        frequency=row.frequency,
        route=row.route,
        started_on=row.started_on,
        stopped_on=row.stopped_on,
        is_active=row.is_active,
        is_anticoagulant=row.is_anticoagulant,
        is_ototoxic=row.is_ototoxic,
        source=row.source,
        version=row.version,
    )


def _flag(row: PatientFlag, users: dict[int, str]) -> PatientFlagRead:
    recorded = users.get(row.created_by_id) if row.created_by_id is not None else None
    return PatientFlagRead(
        public_id=row.public_id,
        flag_code=row.flag_code,
        laterality=row.laterality,
        severity=row.severity,
        detail=row.detail,
        started_on=row.started_on,
        ended_on=row.ended_on,
        is_auto=row.is_auto,
        recorded_by_public_id=recorded,
        version=row.version,
    )


def _problem(
    row: PatientProblem,
    labels: dict[int, tuple[str, str, str | None]],
) -> PatientProblemRead:
    return PatientProblemRead(
        public_id=row.public_id,
        diagnosis=_concept(labels, row.diagnosis_concept_id),
        laterality=row.laterality,
        status=row.status,
        onset_date=row.onset_date,
        resolved_date=row.resolved_date,
        note=row.note,
        version=row.version,
    )


def _history(
    row: PatientHistory,
    labels: dict[int, tuple[str, str, str | None]],
) -> PatientHistoryRead:
    concept = _concept(labels, row.concept_id) if row.concept_id is not None else None
    return PatientHistoryRead(
        public_id=row.public_id,
        category=row.category,
        concept=concept,
        free_text=row.free_text,
        laterality=row.laterality,
        occurred_year=row.occurred_year,
        occurred_date=row.occurred_date,
        detail=row.detail,
        version=row.version,
    )
