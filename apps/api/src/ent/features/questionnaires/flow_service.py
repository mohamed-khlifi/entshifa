"""Questionnaire invitation and response use cases (P5-03)."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.audit.recorder import AuditRecorder
from ent.core.context import set_clinic_id, set_user_id
from ent.core.errors.exceptions import NotFoundError
from ent.core.schemas.base import PageMeta, PageSchema, PaginationParams
from ent.core.security.principal import CurrentUser
from ent.core.security.tokens import hash_refresh_token, new_refresh_token
from ent.core.utils.ids import new_ulid
from ent.engines.scoring.errors import (
    IncompleteInstrumentResponseError,
    InvalidInstrumentAnswerError,
)
from ent.engines.scoring.registry import score_from_spec
from ent.features.clinics.repository import ClinicRepository
from ent.features.encounters.repository import EncounterRepository
from ent.features.patients.models import Patient
from ent.features.patients.repository import PatientRepository
from ent.features.questionnaires.constants import (
    QUESTIONNAIRE_REMOTE_TTL_MINUTES,
    QUESTIONNAIRE_TABLET_TTL_MINUTES,
)
from ent.features.questionnaires.exceptions import (
    InstrumentIncompleteResponseError,
    InstrumentInvalidAnswerError,
    InstrumentNotFoundError,
    InstrumentTranslationIncompleteError,
    QuestionnaireContactMissingError,
    QuestionnaireIdempotencyMismatchError,
    QuestionnaireInvitationAlreadyCompletedError,
    QuestionnaireInvitationExpiredError,
    QuestionnaireInvitationNotFoundError,
    QuestionnaireResponseNotFoundError,
)
from ent.features.questionnaires.flow_mapping import (
    invitation_created,
    invitation_read,
    public_session_read,
    response_read,
)
from ent.features.questionnaires.flow_repository import (
    QuestionnaireIdempotencyRepository,
    QuestionnaireInvitationGlobalRepository,
    QuestionnaireInvitationRepository,
    QuestionnaireResponseRepository,
)
from ent.features.questionnaires.mapping import build_scoring_spec, locales_complete
from ent.features.questionnaires.models import (
    Instrument,
    InstrumentVersion,
    QuestionnaireAnswer,
    QuestionnaireInvitation,
    QuestionnaireRequestIdempotency,
    QuestionnaireResponse,
)
from ent.features.questionnaires.repository import (
    InstrumentRepository,
    InstrumentVersionRepository,
)
from ent.features.questionnaires.schemas.flow_requests import (
    PublicQuestionnaireSubmit,
    QuestionnaireInvitationCreate,
    QuestionnaireStaffResponseCreate,
)
from ent.features.questionnaires.schemas.flow_responses import (
    PublicQuestionnaireCompletionRead,
    PublicQuestionnaireSessionRead,
    QuestionnaireInvitationCreatedRead,
    QuestionnaireInvitationRead,
    QuestionnaireResponseDetailRead,
    QuestionnaireResponseRead,
)
from ent.features.questionnaires.throttle import assert_public_questionnaire_allowed
from ent.integrations.email import send_transactional
from ent.integrations.messaging import send_patient_message
from ent.settings import get_settings


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _hash_request(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class QuestionnaireFlowService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._audit = AuditRecorder(session)

    async def create_invitation(
        self,
        *,
        user: CurrentUser,
        patient_id: str,
        body: QuestionnaireInvitationCreate,
        idempotency_key: str | None,
    ) -> QuestionnaireInvitationCreatedRead:
        set_clinic_id(user.clinic_id)
        set_user_id(user.user_id)
        payload = body.model_dump(mode="json")
        replay = await self._replay_idempotency(
            user,
            idempotency_key,
            payload,
        )
        if replay is not None:
            existing = await QuestionnaireInvitationRepository(
                self._session,
                user.clinic_id,
            ).get_by_public_id(replay)
            if existing is None:
                raise QuestionnaireIdempotencyMismatchError()
            instrument = await self._require_instrument(user, body.instrument_code)
            public_path = self._public_path(existing.locale, "")
            return invitation_created(
                existing,
                instrument_code=instrument.code,
                raw_token="",
                public_path=public_path,
            )

        patient = await self._require_patient(user, patient_id)
        instrument = await self._require_instrument(user, body.instrument_code)
        version = await self._require_current_version(user, instrument)
        locale = body.locale or patient.preferred_locale
        if locale not in locales_complete(version):
            raise InstrumentTranslationIncompleteError(locale=locale)

        recipient = self._recipient_for_channel(patient, body.channel)
        ttl = body.expires_in_minutes or self._default_ttl(body.channel)
        expires_at = _now() + timedelta(minutes=ttl)
        encounter_internal: int | None = None
        if body.encounter_id is not None:
            enc = await EncounterRepository(
                self._session,
                user.clinic_id,
            ).get_by_public_id(body.encounter_id)
            if enc is None or int(enc.patient_id) != int(patient.id):
                raise NotFoundError(resource="encounter")
            encounter_internal = int(enc.id)

        raw_token = new_refresh_token()
        row = QuestionnaireInvitation(
            public_id=new_ulid(),
            clinic_id=user.clinic_id,
            patient_id=int(patient.id),
            instrument_version_id=int(version.id),
            token_hash=hash_refresh_token(raw_token),
            channel=body.channel,
            sent_at=_now(),
            expires_at=expires_at,
            context=body.context,
            encounter_id=encounter_internal,
            locale=locale,
            recipient_address=recipient,
            created_by_id=user.user_id,
            updated_by_id=user.user_id,
        )
        self._session.add(row)
        await self._session.flush()
        self._dispatch_invitation(
            channel=body.channel,
            locale=locale,
            recipient=recipient,
            raw_token=raw_token,
            instrument_code=instrument.code,
        )
        await self._store_idempotency(
            user,
            idempotency_key,
            payload,
            row.public_id,
        )
        self._audit.record_write(
            action="create",
            entity=row,
            clinic_id=user.clinic_id,
            patient_id=int(patient.id),
        )
        await self._session.commit()
        public_path = self._public_path(locale, raw_token)
        return invitation_created(
            row,
            instrument_code=instrument.code,
            raw_token=raw_token,
            public_path=public_path,
        )

    async def list_invitations(
        self,
        *,
        user: CurrentUser,
        patient_id: str,
        page: PaginationParams | None,
    ) -> PageSchema[QuestionnaireInvitationRead]:
        set_clinic_id(user.clinic_id)
        patient = await self._require_patient(user, patient_id)
        repo = QuestionnaireInvitationRepository(self._session, user.clinic_id)
        result = await repo.list_for_patient(patient_id=int(patient.id), page=page)
        reads: list[QuestionnaireInvitationRead] = []
        version_repo = InstrumentVersionRepository(self._session)
        self._audit.record_access(
            action="list",
            entity_type="questionnaire_invitation",
            clinic_id=user.clinic_id,
            patient_id=int(patient.id),
        )
        for row in result.items:
            code = ""
            version = await version_repo.get_by_id(int(row.instrument_version_id))
            if version is not None:
                instrument = await InstrumentRepository(
                    self._session,
                    user.clinic_id,
                ).get(int(version.instrument_id))
                if instrument is not None:
                    code = instrument.code
            reads.append(invitation_read(row, instrument_code=code))
        await self._session.commit()
        return PageSchema(
            items=reads,
            page=PageMeta(
                total=result.total,
                limit=page.limit if page else 25,
                offset=page.offset if page else 0,
            ),
        )

    async def create_staff_response(
        self,
        *,
        user: CurrentUser,
        patient_id: str,
        body: QuestionnaireStaffResponseCreate,
        idempotency_key: str | None,
    ) -> QuestionnaireResponseRead:
        set_clinic_id(user.clinic_id)
        set_user_id(user.user_id)
        payload = body.model_dump(mode="json")
        replay = await self._replay_idempotency(user, idempotency_key, payload)
        if replay is not None:
            existing = await QuestionnaireResponseRepository(
                self._session,
                user.clinic_id,
            ).get_detail(replay)
            if existing is None:
                raise QuestionnaireIdempotencyMismatchError()
            instrument = await self._require_instrument(user, body.instrument_code)
            version = await self._require_current_version(user, instrument)
            return await self._to_response_read(user, existing, instrument, version)

        patient = await self._require_patient(user, patient_id)
        instrument = await self._require_instrument(user, body.instrument_code)
        version = await self._require_current_version(user, instrument)
        if body.locale not in locales_complete(version):
            raise InstrumentTranslationIncompleteError(locale=body.locale)
        encounter_internal = await self._resolve_encounter(
            user,
            body.encounter_id,
            int(patient.id),
        )
        row = await self._persist_scored_response(
            clinic_id=user.clinic_id,
            patient_id=int(patient.id),
            version=version,
            instrument=instrument,
            locale=body.locale,
            entered_by=body.entered_by,
            answers=body.answers,
            encounter_id=encounter_internal,
            invitation_id=None,
            actor_id=user.user_id,
        )
        await self._store_idempotency(user, idempotency_key, payload, row.public_id)
        await self._session.commit()
        return await self._to_response_read(user, row, instrument, version)

    async def list_responses(
        self,
        *,
        user: CurrentUser,
        patient_id: str,
        instrument_code: str | None,
        encounter_id: str | None,
        page: PaginationParams | None,
    ) -> PageSchema[QuestionnaireResponseRead]:
        set_clinic_id(user.clinic_id)
        patient = await self._require_patient(user, patient_id)
        version_internal: int | None = None
        if instrument_code is not None:
            instrument = await self._require_instrument(user, instrument_code)
            version = await self._require_current_version(user, instrument)
            version_internal = int(version.id)
        encounter_internal: int | None = None
        if encounter_id is not None:
            enc = await EncounterRepository(
                self._session,
                user.clinic_id,
            ).get_by_public_id(encounter_id)
            if enc is None:
                raise NotFoundError(resource="encounter")
            encounter_internal = int(enc.id)
        repo = QuestionnaireResponseRepository(self._session, user.clinic_id)
        result = await repo.list_for_patient(
            patient_id=int(patient.id),
            instrument_version_id=version_internal,
            encounter_id=encounter_internal,
            page=page,
        )
        reads: list[QuestionnaireResponseRead] = []
        self._audit.record_access(
            action="list",
            entity_type="questionnaire_response",
            clinic_id=user.clinic_id,
            patient_id=int(patient.id),
        )
        for row in result.items:
            instrument, version = await self._instrument_for_version(
                user,
                int(row.instrument_version_id),
            )
            reads.append(
                await self._to_response_read(user, row, instrument, version),
            )
        await self._session.commit()
        return PageSchema(
            items=reads,
            page=PageMeta(
                total=result.total,
                limit=page.limit if page else 25,
                offset=page.offset if page else 0,
            ),
        )

    async def get_response(
        self,
        *,
        user: CurrentUser,
        response_id: str,
    ) -> QuestionnaireResponseDetailRead:
        set_clinic_id(user.clinic_id)
        row = await QuestionnaireResponseRepository(
            self._session,
            user.clinic_id,
        ).get_detail(response_id)
        if row is None:
            raise QuestionnaireResponseNotFoundError()
        self._audit.record_access(
            action="read",
            entity_type="questionnaire_response",
            clinic_id=user.clinic_id,
            entity_id=int(row.id),
            entity_public_id=row.public_id,
            patient_id=int(row.patient_id),
        )
        instrument, version = await self._instrument_for_version(
            user,
            int(row.instrument_version_id),
        )
        base = await self._to_response_read(user, row, instrument, version)
        await self._session.commit()
        return QuestionnaireResponseDetailRead(**base.model_dump())

    async def public_get_session(
        self,
        *,
        raw_token: str,
        ip_address: str | None,
    ) -> PublicQuestionnaireSessionRead:
        token_hash = hash_refresh_token(raw_token)
        await assert_public_questionnaire_allowed(
            ip_address=ip_address,
            token_hash=token_hash,
        )
        invitation = await QuestionnaireInvitationGlobalRepository(
            self._session,
        ).get_by_token_hash(token_hash)
        if invitation is None:
            raise QuestionnaireInvitationNotFoundError()
        self._assert_invitation_open(invitation)
        if invitation.opened_at is None:
            invitation.opened_at = _now()
        patient = await PatientRepository(
            self._session,
            invitation.clinic_id,
        ).get(int(invitation.patient_id))
        clinic = await ClinicRepository(self._session).get(invitation.clinic_id)
        instrument, version = await self._instrument_for_version(
            _system_user(invitation.clinic_id),
            int(invitation.instrument_version_id),
        )
        if patient is None or clinic is None:
            raise QuestionnaireInvitationNotFoundError()
        self._audit.record_access(
            action="read",
            entity_type="questionnaire_invitation",
            clinic_id=invitation.clinic_id,
            patient_id=int(patient.id),
        )
        await self._session.commit()
        return public_session_read(
            invitation=invitation,
            patient_first_name=patient.first_name,
            clinic_name=clinic.legal_name or clinic.name,
            instrument=instrument,
            version=version,
        )

    async def public_submit(
        self,
        *,
        raw_token: str,
        body: PublicQuestionnaireSubmit,
        ip_address: str | None,
    ) -> PublicQuestionnaireCompletionRead:
        token_hash = hash_refresh_token(raw_token)
        await assert_public_questionnaire_allowed(
            ip_address=ip_address,
            token_hash=token_hash,
        )
        invitation = await QuestionnaireInvitationGlobalRepository(
            self._session,
        ).get_by_token_hash(token_hash)
        if invitation is None:
            raise QuestionnaireInvitationNotFoundError()
        self._assert_invitation_open(invitation)
        instrument, version = await self._instrument_for_version(
            _system_user(invitation.clinic_id),
            int(invitation.instrument_version_id),
        )
        await self._persist_scored_response(
            clinic_id=invitation.clinic_id,
            patient_id=int(invitation.patient_id),
            version=version,
            instrument=instrument,
            locale=invitation.locale,
            entered_by="patient",
            answers=body.answers,
            encounter_id=invitation.encounter_id,
            invitation_id=int(invitation.id),
            actor_id=invitation.created_by_id,
        )
        invitation.completed_at = _now()
        self._audit.record_write(
            action="complete",
            entity=invitation,
            clinic_id=invitation.clinic_id,
            patient_id=int(invitation.patient_id),
        )
        await self._session.commit()
        return PublicQuestionnaireCompletionRead(
            completed_at=invitation.completed_at,
            locale=invitation.locale,
        )

    async def questionnaire_status_for_patient(
        self,
        *,
        clinic_id: int,
        patient_id: int,
        day_start: datetime,
        day_end: datetime,
        now: datetime,
    ) -> str:
        response_repo = QuestionnaireResponseRepository(self._session, clinic_id)
        if await response_repo.completed_between(
            patient_id=patient_id,
            start=day_start,
            end=day_end,
        ):
            return "completed"
        invite_repo = QuestionnaireInvitationRepository(self._session, clinic_id)
        if await invite_repo.has_active_uncompleted(patient_id=patient_id, now=now):
            return "pending"
        return "not_applicable"

    def _assert_invitation_open(self, invitation: QuestionnaireInvitation) -> None:
        if invitation.completed_at is not None:
            raise QuestionnaireInvitationAlreadyCompletedError()
        if invitation.expires_at <= _now():
            raise QuestionnaireInvitationExpiredError()

    async def _persist_scored_response(
        self,
        *,
        clinic_id: int,
        patient_id: int,
        version: InstrumentVersion,
        instrument: Instrument,
        locale: str,
        entered_by: str,
        answers: dict[str, int],
        encounter_id: int | None,
        invitation_id: int | None,
        actor_id: int | None,
    ) -> QuestionnaireResponse:
        spec = build_scoring_spec(instrument, version)
        prior = await QuestionnaireResponseRepository(
            self._session,
            clinic_id,
        ).latest_for_patient_version(
            patient_id=patient_id,
            instrument_version_id=int(version.id),
        )
        previous_total: Decimal | None = None
        previous_id: int | None = None
        if prior is not None:
            previous_total = prior.total_score
            previous_id = int(prior.id)
        try:
            output = score_from_spec(
                spec,
                dict(answers),
                previous_total_score=previous_total,
            )
        except IncompleteInstrumentResponseError as exc:
            raise InstrumentIncompleteResponseError(
                missing_item_codes=exc.missing_item_codes,
            ) from exc
        except InvalidInstrumentAnswerError as exc:
            raise InstrumentInvalidAnswerError(
                item_code=exc.item_code,
                value=exc.value,
            ) from exc

        row = QuestionnaireResponse(
            public_id=new_ulid(),
            clinic_id=clinic_id,
            patient_id=patient_id,
            instrument_version_id=int(version.id),
            encounter_id=encounter_id,
            invitation_id=invitation_id,
            completed_at=_now(),
            locale=locale,
            entered_by=entered_by,
            total_score=output.total_score,
            subscale_scores={
                key: str(val) for key, val in output.subscale_scores.items()
            },
            severity_band=output.severity_band,
            change_from_previous=output.change_from_previous,
            mcid_reached=output.mcid_reached,
            previous_response_id=previous_id,
            created_by_id=actor_id,
            updated_by_id=actor_id,
        )
        self._session.add(row)
        await self._session.flush()
        items_by_code = {i.code: i for i in version.items if i.deleted_at is None}
        for code, value in answers.items():
            item = items_by_code.get(code)
            if item is None:
                continue
            self._session.add(
                QuestionnaireAnswer(
                    public_id=new_ulid(),
                    questionnaire_response_id=int(row.id),
                    instrument_item_id=int(item.id),
                    value=int(value),
                    created_by_id=actor_id,
                    updated_by_id=actor_id,
                ),
            )
        self._audit.record_write(
            action="create",
            entity=row,
            clinic_id=clinic_id,
            patient_id=patient_id,
        )
        return row

    async def _to_response_read(
        self,
        user: CurrentUser,
        row: QuestionnaireResponse,
        instrument: Instrument,
        version: InstrumentVersion,
    ) -> QuestionnaireResponseRead:
        encounter_public: str | None = None
        if row.encounter_id is not None:
            enc = await EncounterRepository(
                self._session,
                user.clinic_id,
            ).get(int(row.encounter_id))
            if enc is not None:
                encounter_public = enc.public_id
        return response_read(
            row,
            instrument=instrument,
            version=version,
            encounter_public_id=encounter_public,
        )

    async def _instrument_for_version(
        self,
        user: CurrentUser,
        version_id: int,
    ) -> tuple[Instrument, InstrumentVersion]:
        version = await InstrumentVersionRepository(self._session).get_by_id(version_id)
        if version is None:
            raise InstrumentNotFoundError()
        instrument = await InstrumentRepository(
            self._session,
            user.clinic_id,
        ).get(int(version.instrument_id))
        if instrument is None:
            raise InstrumentNotFoundError()
        return instrument, version

    async def _require_patient(self, user: CurrentUser, public_id: str) -> Patient:
        row = await PatientRepository(self._session, user.clinic_id).get_by_public_id(
            public_id,
        )
        if row is None:
            raise NotFoundError(resource="patient")
        return row

    async def _require_instrument(
        self,
        user: CurrentUser,
        code: str,
    ) -> Instrument:
        row = await InstrumentRepository(self._session, user.clinic_id).get_by_code(
            code
        )
        if row is None:
            raise InstrumentNotFoundError()
        return row

    async def _require_current_version(
        self,
        user: CurrentUser,
        instrument: Instrument,
    ) -> InstrumentVersion:
        version = await InstrumentVersionRepository(self._session).get_current(
            int(instrument.id),
        )
        if version is None:
            raise InstrumentNotFoundError()
        return version

    async def _resolve_encounter(
        self,
        user: CurrentUser,
        encounter_public_id: str | None,
        patient_id: int,
    ) -> int | None:
        if encounter_public_id is None:
            return None
        enc = await EncounterRepository(
            self._session,
            user.clinic_id,
        ).get_by_public_id(encounter_public_id)
        if enc is None or int(enc.patient_id) != patient_id:
            raise NotFoundError(resource="encounter")
        return int(enc.id)

    def _recipient_for_channel(self, patient: Patient, channel: str) -> str | None:
        if channel == "email":
            if not patient.email:
                raise QuestionnaireContactMissingError(channel=channel)
            return patient.email
        if channel in {"sms", "whatsapp"}:
            if not patient.phone_primary:
                raise QuestionnaireContactMissingError(channel=channel)
            return patient.phone_primary
        return None

    def _default_ttl(self, channel: str) -> int:
        if channel == "tablet":
            return QUESTIONNAIRE_TABLET_TTL_MINUTES
        return QUESTIONNAIRE_REMOTE_TTL_MINUTES

    def _public_path(self, locale: str, raw_token: str) -> str:
        if not raw_token:
            return f"/{locale}/q"
        return f"/{locale}/q/{raw_token}"

    def _dispatch_invitation(
        self,
        *,
        channel: str,
        locale: str,
        recipient: str | None,
        raw_token: str,
        instrument_code: str,
    ) -> None:
        if channel == "tablet" or recipient is None:
            return
        settings = get_settings()
        link = f"{settings.web_url.rstrip('/')}/{locale}/q/{raw_token}"
        context = {
            "instrumentCode": instrument_code,
            "locale": locale,
            "link": link,
            "token": raw_token,
        }
        if channel == "email":
            send_transactional(
                to=recipient,
                template_code="questionnaires.invitation",
                context=context,
            )
            return
        send_patient_message(
            channel=channel,
            to=recipient,
            locale=locale,
            template_code="questionnaires.invitation",
            context=context,
        )

    async def _replay_idempotency(
        self,
        user: CurrentUser,
        key: str | None,
        payload: dict[str, Any],
    ) -> str | None:
        if not key:
            return None
        existing = await QuestionnaireIdempotencyRepository(
            self._session,
            user.clinic_id,
        ).get_by_key(key)
        if existing is None:
            return None
        if existing.request_hash != _hash_request(payload):
            raise QuestionnaireIdempotencyMismatchError()
        return existing.resource_public_id

    async def _store_idempotency(
        self,
        user: CurrentUser,
        key: str | None,
        payload: dict[str, Any],
        resource_public_id: str,
    ) -> None:
        if not key:
            return
        self._session.add(
            QuestionnaireRequestIdempotency(
                public_id=new_ulid(),
                clinic_id=user.clinic_id,
                idempotency_key=key,
                request_hash=_hash_request(payload),
                resource_public_id=resource_public_id,
            ),
        )


def _system_user(clinic_id: int) -> CurrentUser:
    return CurrentUser(
        user_id=0,
        user_public_id="system",
        session_id=0,
        session_public_id="",
        clinic_id=clinic_id,
        clinic_public_id="",
        permissions=frozenset(),
    )
