"""Encounter use cases. Signing freezes the visit; corrections are addenda."""

from __future__ import annotations

import ipaddress
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.audit.recorder import AuditRecorder
from ent.core.context import get_ip_address, set_clinic_id, set_user_id
from ent.core.schemas.base import PageSchema, PaginationParams
from ent.core.security.principal import CurrentUser
from ent.engines.encounters.signing import locked_hash
from ent.features.diagnoses.schemas.requests import DiagnosisWrite
from ent.features.diagnoses.service import DiagnosisService
from ent.features.encounters.exceptions import (
    EncounterNotFoundError,
    EncounterVersionConflictError,
)
from ent.features.encounters.mapping import (
    assert_time_range,
    content_from_encounter,
    normalize_complaints,
    to_encounter_read,
    to_page,
    to_utc_naive,
)
from ent.features.encounters.models import (
    Encounter,
    EncounterAddendum,
    EncounterComplaint,
    EncounterSignature,
)
from ent.features.encounters.references import EncounterReferences
from ent.features.encounters.repository import (
    EncounterAddendumRepository,
    EncounterRepository,
    EncounterSignatureRepository,
)
from ent.features.encounters.schemas.requests import (
    EncounterAddendumCreate,
    EncounterComplaintWrite,
    EncounterCopyForward,
    EncounterCreate,
    EncounterPatch,
    EncounterSign,
)
from ent.features.encounters.schemas.responses import EncounterRead
from ent.features.terminology.models import Concept


class EncounterService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._audit = AuditRecorder(session)
        self._refs = EncounterReferences(session)
        self._diagnoses = DiagnosisService(session)

    async def create_encounter(
        self,
        *,
        user: CurrentUser,
        body: EncounterCreate,
        content_locale: str,
    ) -> EncounterRead:
        self._bind(user)
        patient = await self._refs.patient(user, body.patient_public_id)
        site = await self._refs.site(user, body.site_public_id)
        appointment_id = await self._refs.appointment_id(
            user, body.appointment_public_id, int(patient.id)
        )
        template_id = await self._refs.template_id(user, body.template_public_id)
        started = to_utc_naive(body.started_at)
        ended = to_utc_naive(body.ended_at) if body.ended_at is not None else None
        assert_time_range(started, ended)
        complaints = normalize_complaints(list(body.complaints))
        concepts = await self._refs.concepts(
            user, {item.concept_code for item in complaints}
        )
        encounter = Encounter(
            clinic_id=user.clinic_id,
            site_id=int(site.id),
            patient_id=int(patient.id),
            user_id=user.user_id,
            appointment_id=appointment_id,
            template_id=template_id,
            encounter_type=body.encounter_type,
            started_at=started,
            ended_at=ended,
            chief_complaint_summary=body.chief_complaint_summary,
            history_text=body.history_text,
            assessment_text=body.assessment_text,
            plan_text=body.plan_text,
            status="draft",
            created_by_id=user.user_id,
            updated_by_id=user.user_id,
        )
        repo = self._encounters(user)
        await repo.add(encounter)
        await self._write_complaints(user, encounter, complaints, concepts)
        if body.diagnoses:
            await self._diagnoses.replace_for_encounter(
                user=user, encounter=encounter, items=list(body.diagnoses)
            )
        return await self._reload(user, encounter.public_id, content_locale)

    async def get_encounter(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        content_locale: str,
    ) -> EncounterRead:
        self._bind(user)
        encounter = await self._require(user, public_id)
        payload = await self._read(user, encounter, content_locale)
        self._audit.record_access(
            action="read",
            entity_type="encounter",
            clinic_id=user.clinic_id,
            entity_id=int(encounter.id),
            entity_public_id=encounter.public_id,
            patient_id=int(encounter.patient_id),
        )
        await self._session.commit()
        return payload

    async def list_for_patient(
        self,
        *,
        user: CurrentUser,
        patient_public_id: str,
        page: PaginationParams | None,
        content_locale: str,
    ) -> PageSchema[EncounterRead]:
        self._bind(user)
        patient = await self._refs.patient(user, patient_public_id)
        result = await self._encounters(user).list_for_patient(int(patient.id), page)
        items = [await self._read(user, row, content_locale) for row in result.items]
        self._audit.record_access(
            action="list",
            entity_type="encounter",
            clinic_id=user.clinic_id,
            patient_id=int(patient.id),
        )
        await self._session.commit()
        return to_page(
            items,
            total=result.total,
            limit=result.limit,
            offset=result.offset,
        )

    async def patch_encounter(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        body: EncounterPatch,
        content_locale: str,
    ) -> EncounterRead:
        self._bind(user)
        encounter = await self._require(user, public_id)
        self._check_version(encounter, body.version)
        data = body.model_dump(exclude_unset=True)
        data.pop("version", None)
        raw_complaints = data.pop("complaints", None)
        raw_diagnoses = data.pop("diagnoses", None)
        changes = {
            key: (
                to_utc_naive(value)
                if key == "ended_at" and isinstance(value, datetime)
                else value
            )
            for key, value in data.items()
        }
        ended = encounter.ended_at
        if "ended_at" in changes:
            candidate = changes["ended_at"]
            ended = (
                candidate
                if isinstance(candidate, datetime) or candidate is None
                else ended
            )
        assert_time_range(encounter.started_at, ended)
        repo = self._encounters(user)
        if changes:
            repo.apply_draft_changes(encounter, changes)
        wrote_complaints = False
        if raw_complaints is not None:
            parsed = [
                EncounterComplaintWrite.model_validate(item) for item in raw_complaints
            ]
            normalized = normalize_complaints(parsed)
            concepts = await self._refs.concepts(
                user, {item.concept_code for item in normalized}
            )
            await self._write_complaints(user, encounter, normalized, concepts)
            wrote_complaints = True
        wrote_diagnoses = False
        if raw_diagnoses is not None:
            parsed_diagnoses = [
                DiagnosisWrite.model_validate(item) for item in raw_diagnoses
            ]
            await self._diagnoses.replace_for_encounter(
                user=user, encounter=encounter, items=parsed_diagnoses
            )
            wrote_diagnoses = True
        if changes or wrote_complaints or wrote_diagnoses:
            encounter.updated_by_id = user.user_id
            encounter.version = int(encounter.version) + 1
        return await self._reload(user, encounter.public_id, content_locale)

    async def sign_encounter(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        body: EncounterSign,
        content_locale: str,
    ) -> EncounterRead:
        self._bind(user)
        encounter = await self._require(user, public_id)
        signed_at = datetime.now(UTC).replace(tzinfo=None)
        digest = locked_hash(content_from_encounter(encounter))
        self._encounters(user).mark_signed(
            encounter,
            locked_hash=digest,
            signed_at=signed_at,
            signed_by_id=user.user_id,
        )
        await EncounterSignatureRepository(self._session, user.clinic_id).add(
            EncounterSignature(
                clinic_id=user.clinic_id,
                encounter_id=int(encounter.id),
                user_id=user.user_id,
                role=body.role,
                signed_at=signed_at,
                ip_address=_encode_ip(get_ip_address()),
                content_hash=digest,
                created_by_id=user.user_id,
                updated_by_id=user.user_id,
            )
        )
        return await self._reload(user, encounter.public_id, content_locale)

    async def add_addendum(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        body: EncounterAddendumCreate,
        content_locale: str,
    ) -> EncounterRead:
        self._bind(user)
        encounter = await self._require(user, public_id)
        self._encounters(user).mark_amended(encounter, updated_by_id=user.user_id)
        await EncounterAddendumRepository(self._session, user.clinic_id).add(
            EncounterAddendum(
                clinic_id=user.clinic_id,
                encounter_id=int(encounter.id),
                author_id=user.user_id,
                body=body.body,
                created_by_id=user.user_id,
                updated_by_id=user.user_id,
            )
        )
        return await self._reload(user, encounter.public_id, content_locale)

    async def copy_forward(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        body: EncounterCopyForward,
        content_locale: str,
    ) -> EncounterRead:
        self._bind(user)
        source = await self._require(user, public_id)
        if body.site_public_id is None:
            site_id = int(source.site_id)
        else:
            site = await self._refs.site(user, body.site_public_id)
            site_id = int(site.id)
        started = to_utc_naive(body.started_at)
        encounter = Encounter(
            clinic_id=user.clinic_id,
            site_id=site_id,
            patient_id=int(source.patient_id),
            user_id=user.user_id,
            template_id=source.template_id,
            encounter_type=source.encounter_type,
            started_at=started,
            chief_complaint_summary=source.chief_complaint_summary,
            history_text=source.history_text,
            assessment_text=source.assessment_text,
            plan_text=source.plan_text,
            status="draft",
            previous_encounter_id=int(source.id),
            created_by_id=user.user_id,
            updated_by_id=user.user_id,
        )
        repo = self._encounters(user)
        await repo.add(encounter)
        copied = [
            EncounterComplaint(
                clinic_id=user.clinic_id,
                encounter_id=int(encounter.id),
                concept_id=int(row.concept_id),
                is_primary=bool(row.is_primary),
                laterality=row.laterality,
                duration_text=row.duration_text,
                sort_order=int(row.sort_order),
                created_by_id=user.user_id,
                updated_by_id=user.user_id,
            )
            for row in source.complaints
            if row.deleted_at is None
        ]
        if copied:
            await repo.replace_complaints(encounter, copied, deleted_by_id=user.user_id)
        await self._diagnoses.copy_onto_encounter(
            user=user, source=source, target=encounter
        )
        return await self._reload(user, encounter.public_id, content_locale)

    def _bind(self, user: CurrentUser) -> None:
        set_clinic_id(user.clinic_id)
        set_user_id(user.user_id)

    def _encounters(self, user: CurrentUser) -> EncounterRepository:
        return EncounterRepository(self._session, clinic_id=user.clinic_id)

    async def _require(self, user: CurrentUser, public_id: str) -> Encounter:
        encounter = await self._encounters(user).get_detail(public_id)
        if encounter is None:
            raise EncounterNotFoundError(resource="encounter", publicId=public_id)
        await self._refs.assert_patient_visible(user, int(encounter.patient_id))
        return encounter

    async def _reload(
        self,
        user: CurrentUser,
        public_id: str,
        content_locale: str,
    ) -> EncounterRead:
        await self._session.flush()
        # Collections already loaded on this identity are not refreshed by
        # selectinload. Expire so the read sees signatures, addenda, and
        # replaced complaints written in this request.
        self._session.expire_all()
        encounter = await self._encounters(user).get_detail(public_id)
        if encounter is None:
            raise EncounterNotFoundError(resource="encounter", publicId=public_id)
        payload = await self._read(user, encounter, content_locale)
        await self._session.commit()
        return payload

    async def _read(
        self,
        user: CurrentUser,
        encounter: Encounter,
        content_locale: str,
    ) -> EncounterRead:
        concept_ids = {
            int(row.concept_id)
            for row in encounter.complaints
            if row.deleted_at is None
        }
        concept_ids.update(
            int(row.concept_id) for row in encounter.diagnoses if row.deleted_at is None
        )
        labels = await self._refs.labels(user, concept_ids, content_locale)
        return to_encounter_read(encounter, labels)

    async def _write_complaints(
        self,
        user: CurrentUser,
        encounter: Encounter,
        complaints: list[EncounterComplaintWrite],
        concepts: dict[str, Concept],
    ) -> None:
        rows = [
            EncounterComplaint(
                clinic_id=user.clinic_id,
                encounter_id=int(encounter.id),
                concept_id=int(concepts[item.concept_code].id),
                is_primary=item.is_primary,
                laterality=(
                    item.laterality.value if item.laterality is not None else None
                ),
                duration_text=item.duration_text,
                sort_order=item.sort_order,
                created_by_id=user.user_id,
                updated_by_id=user.user_id,
            )
            for item in complaints
        ]
        await self._encounters(user).replace_complaints(
            encounter,
            rows,
            deleted_by_id=user.user_id,
        )

    def _check_version(self, encounter: Encounter, version: int) -> None:
        if int(encounter.version) != version:
            raise EncounterVersionConflictError(
                server_version=int(encounter.version),
                client_version=version,
            )


def _encode_ip(ip_address: str | None) -> bytes | None:
    if not ip_address:
        return None
    try:
        if ":" in ip_address:
            return ipaddress.IPv6Address(ip_address).packed
        return ipaddress.IPv4Address(ip_address).packed
    except ValueError:
        return None
