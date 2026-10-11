"""Procedure record use cases. Signing freezes the parent; corrections are addenda."""

from __future__ import annotations

import ipaddress
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.audit.recorder import AuditRecorder
from ent.core.context import get_ip_address, set_clinic_id, set_user_id
from ent.core.events.bus import get_event_bus
from ent.core.schemas.base import PageSchema, PaginationParams
from ent.core.security.principal import CurrentUser
from ent.engines.procedures.signing import locked_hash
from ent.features.procedures.draft import (
    apply_draft_changes,
    load_procedure_concepts,
    reject_null_required,
)
from ent.features.procedures.events import procedure_performed_event
from ent.features.procedures.exceptions import (
    ProcedureRecordNotFoundError,
    ProcedureVersionConflictError,
)
from ent.features.procedures.mapping import (
    blank_to_none,
    content_from_record,
    to_page,
    to_procedure_read,
    to_utc_naive,
)
from ent.features.procedures.models import ProcedureRecord, ProcedureRecordAddendum
from ent.features.procedures.references import ProcedureReferences
from ent.features.procedures.repository import (
    ProcedureRecordAddendumRepository,
    ProcedureRecordRepository,
)
from ent.features.procedures.schemas.requests import (
    ProcedureAddendumCreate,
    ProcedureRecordCreate,
    ProcedureRecordUpdate,
    ProcedureSign,
)
from ent.features.procedures.schemas.responses import ProcedureRecordRead


class ProcedureRecordService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._audit = AuditRecorder(session)
        self._refs = ProcedureReferences(session)

    async def create_procedure(
        self,
        *,
        user: CurrentUser,
        body: ProcedureRecordCreate,
        content_locale: str,
    ) -> ProcedureRecordRead:
        self._bind(user)
        patient = await self._refs.patient(user, body.patient_public_id)
        concepts = await load_procedure_concepts(
            self._refs,
            user,
            body.procedure_concept_public_id,
            body.complication_concept_public_id,
        )
        performer_public_id = body.performed_by_public_id or user.user_public_id
        row = ProcedureRecord(
            clinic_id=user.clinic_id,
            patient_id=int(patient.id),
            encounter_id=await self._refs.encounter_id(
                user,
                body.encounter_public_id,
                patient_id=int(patient.id),
            ),
            procedure_concept_id=int(concepts[body.procedure_concept_public_id].id),
            performed_at=to_utc_naive(body.performed_at),
            performed_by_id=await self._refs.member_id(user, performer_public_id),
            laterality=str(body.laterality),
            anesthesia=body.anesthesia,
            setting=body.setting,
            instrument=blank_to_none(body.instrument),
            indication_text=blank_to_none(body.indication_text),
            tolerance=body.tolerance,
            complication_concept_id=(
                int(concepts[body.complication_concept_public_id].id)
                if body.complication_concept_public_id is not None
                else None
            ),
            complication_note=blank_to_none(body.complication_note),
            status="draft",
            created_by_id=user.user_id,
            updated_by_id=user.user_id,
        )
        await self._records(user).add(row)
        return await self._reload(user, row.public_id, content_locale)

    async def get_procedure(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        content_locale: str,
    ) -> ProcedureRecordRead:
        self._bind(user)
        row = await self._require(user, public_id)
        payload = await self._read(user, row, content_locale)
        self._audit.record_access(
            action="get",
            entity_type="procedure_record",
            clinic_id=user.clinic_id,
            entity_id=int(row.id),
            entity_public_id=row.public_id,
            patient_id=int(row.patient_id),
        )
        await self._session.commit()
        return payload

    async def list_procedures(
        self,
        *,
        user: CurrentUser,
        page: PaginationParams,
        content_locale: str,
        patient_public_id: str | None = None,
    ) -> PageSchema[ProcedureRecordRead]:
        self._bind(user)
        patient_id = None
        if patient_public_id is not None:
            patient_id = int((await self._refs.patient(user, patient_public_id)).id)
        result = await self._records(user).list_procedures(page, patient_id=patient_id)
        items = [await self._read(user, row, content_locale) for row in result.items]
        self._audit.record_access(
            action="list",
            entity_type="procedure_record",
            clinic_id=user.clinic_id,
            patient_id=patient_id,
        )
        await self._session.commit()
        return to_page(
            items,
            total=result.total,
            limit=result.limit,
            offset=result.offset,
        )

    async def update_procedure(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        body: ProcedureRecordUpdate,
        content_locale: str,
    ) -> ProcedureRecordRead:
        self._bind(user)
        row = await self._require(user, public_id)
        self._check_version(row, body.version)
        self._records(user).assert_draft(row)
        data = body.model_dump(exclude_unset=True)
        data.pop("version", None)
        reject_null_required(data)
        await apply_draft_changes(self._refs, user, row, data)
        row.updated_by_id = user.user_id
        row.version = int(row.version) + 1
        return await self._reload(user, row.public_id, content_locale)

    async def sign_procedure(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        body: ProcedureSign,
        content_locale: str,
    ) -> ProcedureRecordRead:
        self._bind(user)
        row = await self._require(user, public_id)
        signed_at = datetime.now(UTC).replace(tzinfo=None)
        digest = locked_hash(content_from_record(row))
        self._records(user).mark_signed(
            row,
            locked_hash=digest,
            signed_at=signed_at,
            signed_by_id=user.user_id,
            signed_role=body.role,
            signed_ip=_encode_ip(get_ip_address()),
        )
        await self._session.commit()
        await get_event_bus().publish(
            procedure_performed_event(
                clinic_id=user.clinic_id,
                procedure_public_id=row.public_id,
                patient_public_id=row.patient.public_id,
                encounter_public_id=(
                    row.encounter.public_id if row.encounter is not None else None
                ),
                procedure_concept_code=row.procedure_concept.code,
                performed_at=row.performed_at,
                performed_by_public_id=row.performed_by.public_id,
                laterality=row.laterality,
                setting=row.setting,
                anesthesia=row.anesthesia,
                has_complications=bool(
                    row.complication_concept_id or row.complication_note
                ),
            )
        )
        return await self._reload(user, public_id, content_locale)

    async def add_addendum(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        body: ProcedureAddendumCreate,
        content_locale: str,
    ) -> ProcedureRecordRead:
        self._bind(user)
        row = await self._require(user, public_id)
        self._records(user).mark_amended(row, updated_by_id=user.user_id)
        await self._session.flush()
        await ProcedureRecordAddendumRepository(self._session, user.clinic_id).add(
            ProcedureRecordAddendum(
                clinic_id=user.clinic_id,
                procedure_record_id=int(row.id),
                author_id=user.user_id,
                body=body.body.strip(),
                created_by_id=user.user_id,
                updated_by_id=user.user_id,
            )
        )
        return await self._reload(user, row.public_id, content_locale)

    def _bind(self, user: CurrentUser) -> None:
        set_clinic_id(user.clinic_id)
        set_user_id(user.user_id)

    def _records(self, user: CurrentUser) -> ProcedureRecordRepository:
        return ProcedureRecordRepository(self._session, clinic_id=user.clinic_id)

    async def _require(self, user: CurrentUser, public_id: str) -> ProcedureRecord:
        row = await self._records(user).get_detail(public_id)
        if row is None:
            raise ProcedureRecordNotFoundError(public_id=public_id)
        await self._refs.assert_patient_visible(user, int(row.patient_id))
        return row

    async def _reload(
        self,
        user: CurrentUser,
        public_id: str,
        content_locale: str,
    ) -> ProcedureRecordRead:
        await self._session.flush()
        self._session.expire_all()
        row = await self._require(user, public_id)
        return await self._read(user, row, content_locale)

    async def _read(
        self,
        user: CurrentUser,
        row: ProcedureRecord,
        content_locale: str,
    ) -> ProcedureRecordRead:
        concept_ids = {int(row.procedure_concept_id)}
        if row.complication_concept_id is not None:
            concept_ids.add(int(row.complication_concept_id))
        labels = await self._refs.labels(user, concept_ids, content_locale)
        return to_procedure_read(row, labels)

    def _check_version(self, row: ProcedureRecord, version: int) -> None:
        if int(row.version) != version:
            raise ProcedureVersionConflictError(
                server_version=int(row.version),
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
