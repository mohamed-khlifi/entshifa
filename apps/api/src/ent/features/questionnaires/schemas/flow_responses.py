"""Questionnaire patient-flow response schemas (P5-03)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import Field

from ent.core.schemas.base import CamelModel


class QuestionnaireInvitationCreatedRead(CamelModel):
    public_id: str
    instrument_code: str
    channel: str
    context: str
    locale: str
    sent_at: datetime
    expires_at: datetime
    token: str
    public_path: str


class QuestionnaireInvitationRead(CamelModel):
    public_id: str
    instrument_code: str
    channel: str
    context: str
    locale: str
    sent_at: datetime
    expires_at: datetime
    opened_at: datetime | None
    completed_at: datetime | None


class QuestionnaireAnswerRead(CamelModel):
    item_code: str
    value: int


class QuestionnaireResponseItemDetailRead(CamelModel):
    code: str
    position: int
    text: str
    subscale: str | None
    value: int
    option_text: str
    min_value: int
    max_value: int


class QuestionnaireResponseRead(CamelModel):
    public_id: str
    instrument_code: str
    instrument_title: str | None
    locale: str
    entered_by: str
    completed_at: datetime
    total_score: Decimal
    subscale_scores: dict[str, Decimal]
    severity_band: str | None
    change_from_previous: Decimal | None
    mcid_reached: bool | None
    min_score: int
    max_score: int
    mcid: Decimal | None
    encounter_id: str | None
    answers: list[QuestionnaireAnswerRead] = Field(default_factory=list)


class QuestionnaireResponseDetailRead(QuestionnaireResponseRead):
    items: list[QuestionnaireResponseItemDetailRead] = Field(default_factory=list)


class PublicInstrumentOptionRead(CamelModel):
    value: int
    position: int
    text: str


class PublicInstrumentItemRead(CamelModel):
    code: str
    position: int
    text: str
    options: list[PublicInstrumentOptionRead]


class PublicInstrumentRead(CamelModel):
    code: str
    title: str
    category: str
    respondent: str
    items: list[PublicInstrumentItemRead]


class PublicQuestionnaireSessionRead(CamelModel):
    patient_first_name: str
    clinic_name: str
    locale: str
    channel: str
    expires_at: datetime
    instrument: PublicInstrumentRead


class PublicQuestionnaireCompletionRead(CamelModel):
    completed_at: datetime
    locale: str
