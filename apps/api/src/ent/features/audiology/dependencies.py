"""Audiology FastAPI dependencies."""

from __future__ import annotations

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.db.session import get_session
from ent.core.i18n.content_locale import content_locale_from_accept_language
from ent.features.audiology.device_service import HearingDeviceService
from ent.features.audiology.evoked_service import AbrResultService, OaeResultService
from ent.features.audiology.service import AudiologyService
from ent.features.audiology.speech_service import SpeechAudiometryService
from ent.features.audiology.tympanometry_service import TympanometryService


def get_audiology_service(
    session: AsyncSession = Depends(get_session),
) -> AudiologyService:
    return AudiologyService(session=session)


def get_speech_audiometry_service(
    session: AsyncSession = Depends(get_session),
) -> SpeechAudiometryService:
    return SpeechAudiometryService(session=session)


def get_tympanometry_service(
    session: AsyncSession = Depends(get_session),
) -> TympanometryService:
    return TympanometryService(session=session)


def get_oae_result_service(
    session: AsyncSession = Depends(get_session),
) -> OaeResultService:
    return OaeResultService(session=session)


def get_abr_result_service(
    session: AsyncSession = Depends(get_session),
) -> AbrResultService:
    return AbrResultService(session=session)


def get_hearing_device_service(
    session: AsyncSession = Depends(get_session),
) -> HearingDeviceService:
    return HearingDeviceService(session=session)


def get_content_locale(
    accept_language: str | None = Header(default=None, alias="Accept-Language"),
) -> str:
    return content_locale_from_accept_language(accept_language)


def idempotency_key(
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> str | None:
    if idempotency_key is None:
        return None
    return idempotency_key[:80]
