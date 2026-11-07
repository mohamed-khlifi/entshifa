"""Map questionnaire flow ORM rows to API schemas."""

from __future__ import annotations

from decimal import Decimal

from ent.features.questionnaires.mapping import (
    _options_for_item,
    _translation_map,
)
from ent.features.questionnaires.models import (
    Instrument,
    InstrumentVersion,
    QuestionnaireAnswer,
    QuestionnaireInvitation,
    QuestionnaireResponse,
)
from ent.features.questionnaires.schemas.flow_responses import (
    PublicInstrumentItemRead,
    PublicInstrumentRead,
    PublicQuestionnaireSessionRead,
    QuestionnaireAnswerRead,
    QuestionnaireInvitationCreatedRead,
    QuestionnaireInvitationRead,
    QuestionnaireResponseRead,
)


def invitation_read(
    invitation: QuestionnaireInvitation,
    *,
    instrument_code: str,
) -> QuestionnaireInvitationRead:
    return QuestionnaireInvitationRead(
        public_id=invitation.public_id,
        instrument_code=instrument_code,
        channel=invitation.channel,
        context=invitation.context,
        locale=invitation.locale,
        sent_at=invitation.sent_at,
        expires_at=invitation.expires_at,
        opened_at=invitation.opened_at,
        completed_at=invitation.completed_at,
    )


def invitation_created(
    invitation: QuestionnaireInvitation,
    *,
    instrument_code: str,
    raw_token: str,
    public_path: str,
) -> QuestionnaireInvitationCreatedRead:
    return QuestionnaireInvitationCreatedRead(
        public_id=invitation.public_id,
        instrument_code=instrument_code,
        channel=invitation.channel,
        context=invitation.context,
        locale=invitation.locale,
        sent_at=invitation.sent_at,
        expires_at=invitation.expires_at,
        token=raw_token,
        public_path=public_path,
    )


def _answers_by_code(
    version: InstrumentVersion,
    answers: list[QuestionnaireAnswer],
) -> list[QuestionnaireAnswerRead]:
    items_by_id = {int(i.id): i for i in version.items if i.deleted_at is None}
    out: list[QuestionnaireAnswerRead] = []
    for row in answers:
        if row.deleted_at is not None:
            continue
        item = items_by_id.get(int(row.instrument_item_id))
        if item is None:
            continue
        out.append(QuestionnaireAnswerRead(item_code=item.code, value=int(row.value)))
    return sorted(out, key=lambda a: a.item_code)


def response_read(
    response: QuestionnaireResponse,
    *,
    instrument: Instrument,
    version: InstrumentVersion,
    encounter_public_id: str | None,
) -> QuestionnaireResponseRead:
    texts = _translation_map(version, response.locale)
    title = texts.get((None, None), "")
    subscales = {
        key: Decimal(str(value))
        for key, value in dict(response.subscale_scores).items()
    }
    return QuestionnaireResponseRead(
        public_id=response.public_id,
        instrument_code=instrument.code,
        instrument_title=title or None,
        locale=response.locale,
        entered_by=response.entered_by,
        completed_at=response.completed_at,
        total_score=response.total_score,
        subscale_scores=subscales,
        severity_band=response.severity_band,
        change_from_previous=response.change_from_previous,
        mcid_reached=response.mcid_reached,
        encounter_id=encounter_public_id,
        answers=_answers_by_code(version, list(response.answers)),
    )


def public_instrument_read(
    instrument: Instrument,
    version: InstrumentVersion,
    locale: str,
) -> PublicInstrumentRead:
    texts = _translation_map(version, locale)
    title = texts.get((None, None), "")
    items: list[PublicInstrumentItemRead] = []
    active_items = sorted(
        [i for i in version.items if i.deleted_at is None],
        key=lambda i: i.position,
    )
    for item in active_items:
        options = _options_for_item(version, item)
        option_reads: list[dict[str, object]] = []
        for opt in options:
            option_reads.append(
                {
                    "value": int(opt.value),
                    "position": int(opt.position),
                    "text": texts.get((None, opt.id), ""),
                },
            )
        items.append(
            PublicInstrumentItemRead(
                code=item.code,
                position=int(item.position),
                text=texts.get((item.id, None), ""),
                options=option_reads,
            ),
        )
    return PublicInstrumentRead(
        code=instrument.code,
        title=title,
        category=instrument.category,
        respondent=instrument.respondent,
        items=items,
    )


def public_session_read(
    *,
    invitation: QuestionnaireInvitation,
    patient_first_name: str,
    clinic_name: str,
    instrument: Instrument,
    version: InstrumentVersion,
) -> PublicQuestionnaireSessionRead:
    return PublicQuestionnaireSessionRead(
        patient_first_name=patient_first_name,
        clinic_name=clinic_name,
        locale=invitation.locale,
        channel=invitation.channel,
        expires_at=invitation.expires_at,
        instrument=public_instrument_read(instrument, version, invitation.locale),
    )
