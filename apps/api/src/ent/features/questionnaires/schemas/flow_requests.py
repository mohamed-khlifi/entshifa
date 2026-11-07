"""Questionnaire patient-flow request schemas (P5-03)."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, field_validator

from ent.core.schemas.base import CamelModel
from ent.features.questionnaires.constants import (
    INSTRUMENT_LOCALES,
    QUESTIONNAIRE_CHANNELS,
    QUESTIONNAIRE_CONTEXTS,
    QUESTIONNAIRE_ENTERED_BY,
    QUESTIONNAIRE_EXPIRES_MAX_BOUND,
    QUESTIONNAIRE_EXPIRES_MIN_BOUND,
)

QuestionnaireChannel = Literal["sms", "whatsapp", "email", "tablet"]
QuestionnaireContext = Literal[
    "pre_visit",
    "waiting_room",
    "post_op_3m",
    "post_op_6m",
    "post_op_12m",
    "follow_up",
]
QuestionnaireEnteredBy = Literal["staff", "clinician"]


class QuestionnaireInvitationCreate(CamelModel):
    instrument_code: str = Field(min_length=1, max_length=40)
    channel: QuestionnaireChannel
    context: QuestionnaireContext = "pre_visit"
    locale: str | None = Field(default=None, max_length=10)
    encounter_id: str | None = Field(default=None, max_length=26)
    expires_in_minutes: int | None = Field(default=None, ge=15, le=10080)

    @field_validator("locale")
    @classmethod
    def _locale(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if value not in INSTRUMENT_LOCALES:
            msg = "unsupported_locale"
            raise ValueError(msg)
        return value

    @field_validator("channel")
    @classmethod
    def _channel(cls, value: str) -> str:
        if value not in QUESTIONNAIRE_CHANNELS:
            msg = "unsupported_channel"
            raise ValueError(msg)
        return value

    @field_validator("context")
    @classmethod
    def _context(cls, value: str) -> str:
        if value not in QUESTIONNAIRE_CONTEXTS:
            msg = "unsupported_context"
            raise ValueError(msg)
        return value

    @field_validator("expires_in_minutes")
    @classmethod
    def _expires(cls, value: int | None) -> int | None:
        if value is None:
            return None
        if (
            value < QUESTIONNAIRE_EXPIRES_MIN_BOUND
            or value > QUESTIONNAIRE_EXPIRES_MAX_BOUND
        ):
            msg = "expires_out_of_bounds"
            raise ValueError(msg)
        return value


class QuestionnaireStaffResponseCreate(CamelModel):
    instrument_code: str = Field(min_length=1, max_length=40)
    locale: str = Field(max_length=10)
    entered_by: QuestionnaireEnteredBy = "staff"
    encounter_id: str | None = Field(default=None, max_length=26)
    answers: dict[str, int] = Field(min_length=1)

    @field_validator("locale")
    @classmethod
    def _locale(cls, value: str) -> str:
        if value not in INSTRUMENT_LOCALES:
            msg = "unsupported_locale"
            raise ValueError(msg)
        return value

    @field_validator("entered_by")
    @classmethod
    def _entered_by(cls, value: str) -> str:
        if value not in QUESTIONNAIRE_ENTERED_BY:
            msg = "unsupported_entered_by"
            raise ValueError(msg)
        return value


class PublicQuestionnaireSubmit(CamelModel):
    answers: dict[str, int] = Field(min_length=1)
