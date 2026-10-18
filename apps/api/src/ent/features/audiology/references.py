"""Resolve patients, encounters and staff for audiology."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.errors.exceptions import NotFoundError, ValidationError
from ent.core.security.principal import CurrentUser
from ent.features.audiology.models import Audiogram
from ent.features.audiology.repository import AudiogramRepository
from ent.features.encounters.models import Encounter
from ent.features.encounters.repository import EncounterRepository
from ent.features.patients.models import Patient
from ent.features.patients.policies import created_by_scope
from ent.features.patients.repository import PatientRepository
from ent.features.users.repository import UserAdminRepository


class AudiologyReferences:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def patients(self, user: CurrentUser) -> PatientRepository:
        return PatientRepository(self._session, clinic_id=user.clinic_id)

    def audiograms(self, user: CurrentUser) -> AudiogramRepository:
        return AudiogramRepository(self._session, clinic_id=user.clinic_id)

    async def patient(self, user: CurrentUser, public_id: str) -> Patient:
        row = await self.patients(user).get_visible(
            public_id,
            created_by_id=created_by_scope(user),
        )
        if row is None:
            raise NotFoundError(resource="patient", publicId=public_id)
        return row

    async def assert_patient_visible(self, user: CurrentUser, patient_id: int) -> None:
        row = await self.patients(user).get(patient_id)
        if row is None:
            raise NotFoundError(resource="patient")
        scope = created_by_scope(user)
        if scope is not None and row.created_by_id != scope:
            raise NotFoundError(resource="patient")

    async def encounter_id(
        self,
        user: CurrentUser,
        public_id: str | None,
        *,
        patient_id: int,
    ) -> int | None:
        if public_id is None:
            return None
        row = await self._encounter(user, public_id)
        if int(row.patient_id) != patient_id:
            raise ValidationError(reason="encounter_patient", encounterId=public_id)
        return int(row.id)

    async def member_id(self, user: CurrentUser, public_id: str) -> int:
        member = await UserAdminRepository(self._session).get_member(
            clinic_id=user.clinic_id,
            public_id=public_id,
        )
        if member is None:
            raise NotFoundError(resource="user", publicId=public_id)
        return int(member.id)

    async def baseline_audiogram(
        self,
        user: CurrentUser,
        public_id: str | None,
        *,
        patient_id: int,
    ) -> Audiogram | None:
        if public_id is None:
            return None
        row = await self.audiograms(user).get_detail(public_id)
        if row is None:
            raise NotFoundError(resource="audiogram", publicId=public_id)
        if int(row.patient_id) != patient_id:
            raise ValidationError(reason="baseline_patient", audiogramId=public_id)
        return row

    async def _encounter(self, user: CurrentUser, public_id: str) -> Encounter:
        row = await EncounterRepository(
            self._session, clinic_id=user.clinic_id
        ).get_by_public_id(public_id)
        if row is None:
            raise NotFoundError(resource="encounter", publicId=public_id)
        return row
