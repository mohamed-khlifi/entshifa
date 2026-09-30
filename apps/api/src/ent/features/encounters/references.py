"""Resolve patients, sites, appointments, templates and concepts for a visit."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.errors.exceptions import NotFoundError, ValidationError
from ent.core.security.principal import CurrentUser
from ent.features.clinics.models import Site
from ent.features.clinics.repository import ClinicRepository, SiteRepository
from ent.features.encounters.repository import EncounterTemplateRepository
from ent.features.patients.models import Patient
from ent.features.patients.policies import created_by_scope
from ent.features.patients.repository import PatientRepository
from ent.features.scheduling.repository import AppointmentRepository
from ent.features.terminology.models import Concept
from ent.features.terminology.repository import TerminologyRepository


class EncounterReferences:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def patients(self, user: CurrentUser) -> PatientRepository:
        return PatientRepository(self._session, clinic_id=user.clinic_id)

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

    async def site(self, user: CurrentUser, public_id: str) -> Site:
        row = await SiteRepository(self._session, user.clinic_id).get_by_public_id(
            public_id
        )
        if row is None:
            raise NotFoundError(resource="site", publicId=public_id)
        return row

    async def appointment_id(
        self,
        user: CurrentUser,
        public_id: str | None,
        patient_id: int,
    ) -> int | None:
        if public_id is None:
            return None
        row = await AppointmentRepository(
            self._session, user.clinic_id
        ).get_by_public_id(public_id)
        if row is None:
            raise NotFoundError(resource="appointment", publicId=public_id)
        if int(row.patient_id) != patient_id:
            raise ValidationError(reason="appointment_patient")
        return int(row.id)

    async def template_id(self, user: CurrentUser, public_id: str | None) -> int | None:
        if public_id is None:
            return None
        row = await EncounterTemplateRepository(
            self._session, user.clinic_id
        ).get_active_for_user(public_id, user_id=user.user_id)
        if row is None:
            raise NotFoundError(resource="template", publicId=public_id)
        return int(row.id)

    async def concepts(self, user: CurrentUser, codes: set[str]) -> dict[str, Concept]:
        found: dict[str, Concept] = {}
        terminology = TerminologyRepository(self._session, user.clinic_id)
        for code in codes:
            concept = await terminology.get_concept_by_code(code)
            if concept is None:
                raise ValidationError(reason="unknown_concept", conceptCode=code)
            found[code] = concept
        return found

    async def labels(
        self,
        user: CurrentUser,
        concept_ids: set[int],
        content_locale: str,
    ) -> dict[int, tuple[str, str, str | None]]:
        clinic = await ClinicRepository(self._session).get(user.clinic_id)
        default_locale = clinic.default_locale if clinic is not None else content_locale
        return await self.patients(user).concept_labels(
            concept_ids,
            locale=content_locale,
            clinic_default_locale=default_locale,
        )
