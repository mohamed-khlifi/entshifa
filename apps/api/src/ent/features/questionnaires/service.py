"""Questionnaire instrument use cases (P5-01)."""

from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.audit.recorder import AuditRecorder
from ent.core.context import set_clinic_id, set_user_id
from ent.core.schemas.base import PageMeta, PageSchema, PaginationParams
from ent.core.security.principal import CurrentUser
from ent.core.utils.ids import new_ulid
from ent.engines.scoring.errors import (
    IncompleteInstrumentResponseError,
    InstrumentScoreOutOfRangeError,
    InvalidInstrumentAnswerError,
    InvalidInstrumentDefinitionError,
)
from ent.engines.scoring.registry import score_from_spec
from ent.engines.scoring.sum_scorer import validate_spec
from ent.features.questionnaires.exceptions import (
    InstrumentCodeConflictError,
    InstrumentIncompleteResponseError,
    InstrumentInvalidAnswerError,
    InstrumentInvalidDefinitionError,
    InstrumentNotFoundError,
    InstrumentSystemImmutableError,
    InstrumentTranslationIncompleteError,
    InstrumentVersionConflictError,
)
from ent.features.questionnaires.mapping import (
    _current_version,
    _translation_map,
    build_scoring_spec,
    locales_complete,
    to_detail,
    to_localized,
    to_score_read,
    to_summary,
)
from ent.features.questionnaires.models import (
    Instrument,
    InstrumentItem,
    InstrumentOption,
    InstrumentTranslation,
    InstrumentVersion,
)
from ent.features.questionnaires.repository import (
    InstrumentRepository,
    InstrumentVersionRepository,
)
from ent.features.questionnaires.schemas.requests import (
    InstrumentCreate,
    InstrumentItemInput,
    InstrumentLocaleTranslationInput,
    InstrumentOptionInput,
    InstrumentScoreRequest,
    InstrumentTranslationUpsert,
    InstrumentVersionCreate,
)
from ent.features.questionnaires.schemas.responses import (
    InstrumentDetailRead,
    InstrumentLocalizedRead,
    InstrumentScoreRead,
    InstrumentSummaryRead,
)


class QuestionnaireService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._audit = AuditRecorder(session)

    async def list_instruments(
        self,
        *,
        user: CurrentUser,
        page: PaginationParams,
        category: str | None,
        respondent: str | None,
        locale: str | None,
    ) -> PageSchema[InstrumentSummaryRead]:
        self._bind(user)
        result = await self._repo(user).list_effective(
            category=category,
            respondent=respondent,
            page=page,
        )
        items = [to_summary(row) for row in result.items]
        if locale is not None:
            items = [row for row in items if locale in row.locales_available]
        self._audit.record_access(
            action="list",
            entity_type="instrument",
            clinic_id=user.clinic_id,
        )
        await self._session.commit()
        return PageSchema(
            items=items,
            page=PageMeta(
                total=result.total if locale is None else len(items),
                limit=result.limit,
                offset=result.offset,
                next_cursor=None,
            ),
        )

    async def get_instrument(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        locale: str | None,
    ) -> InstrumentDetailRead | InstrumentLocalizedRead:
        self._bind(user)
        row = await self._require(user, public_id)
        read: InstrumentDetailRead | InstrumentLocalizedRead
        if locale is not None:
            version = _current_version(row)
            if version is None or locale not in locales_complete(version):
                raise InstrumentTranslationIncompleteError(locale=locale)
            title = _translation_map(version, locale).get((None, None), "")
            read = to_localized(row, locale=locale, title=title)
        else:
            read = to_detail(row, locale=None)
        self._audit.record_access(
            action="get",
            entity_type="instrument",
            clinic_id=user.clinic_id,
            entity_id=int(row.id),
            entity_public_id=row.public_id,
        )
        await self._session.commit()
        return read

    async def get_instrument_by_code(
        self,
        *,
        user: CurrentUser,
        code: str,
        locale: str | None,
    ) -> InstrumentDetailRead | InstrumentLocalizedRead:
        self._bind(user)
        row = await self._repo(user).get_by_code(code)
        if row is None:
            raise InstrumentNotFoundError(code=code)
        loaded = await self._repo(user).get_for_read(row.public_id)
        if loaded is None:
            raise InstrumentNotFoundError(code=code)
        read: InstrumentDetailRead | InstrumentLocalizedRead
        if locale is not None:
            version = _current_version(loaded)
            if version is None or locale not in locales_complete(version):
                raise InstrumentTranslationIncompleteError(locale=locale)
            title = _translation_map(version, locale).get((None, None), "")
            read = to_localized(loaded, locale=locale, title=title)
        else:
            read = to_detail(loaded, locale=None)
        await self._session.commit()
        return read

    async def create_instrument(
        self, *, user: CurrentUser, body: InstrumentCreate
    ) -> InstrumentDetailRead:
        self._bind(user)
        repo = self._repo(user)
        if await repo.get_clinic_owned_by_code(body.code) is not None:
            raise InstrumentCodeConflictError(code=body.code)
        if body.scoring_type == "custom":
            raise InstrumentInvalidDefinitionError(reason="custom_not_supported")
        row = Instrument(
            public_id=new_ulid(),
            clinic_id=user.clinic_id,
            code=body.code,
            category=body.category,
            respondent=body.respondent,
            scoring_type=body.scoring_type,
            min_score=body.min_score,
            max_score=body.max_score,
            mcid=body.mcid,
            license_note=body.license_note,
            reference=body.reference,
            is_system=False,
            is_active=True,
            created_by_id=user.user_id,
            updated_by_id=user.user_id,
        )
        await repo.add(row)
        await self._session.flush()
        await self._add_version(
            user,
            instrument=row,
            version_label=body.version,
            effective_from=body.effective_from,
            is_current=True,
            scoring_config=body.scoring_config.model_dump(by_alias=True, mode="json"),
            shared_options=body.shared_options.options if body.shared_options else None,
            items=body.items,
            translations=body.translations,
        )
        self._audit.record_write(
            action="create",
            entity=row,
            clinic_id=user.clinic_id,
            after={"code": row.code},
        )
        await self._session.commit()
        loaded = await self._require(user, row.public_id)
        return to_detail(loaded)

    async def create_instrument_version(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        body: InstrumentVersionCreate,
    ) -> InstrumentDetailRead:
        self._bind(user)
        instrument = await self._require(user, public_id)
        if instrument.clinic_id != user.clinic_id:
            raise InstrumentSystemImmutableError()
        if body.is_current:
            await InstrumentVersionRepository(self._session).clear_current(
                int(instrument.id)
            )
        await self._add_version(
            user,
            instrument=instrument,
            version_label=body.version,
            effective_from=body.effective_from,
            is_current=body.is_current,
            scoring_config=body.scoring_config.model_dump(by_alias=True, mode="json"),
            shared_options=body.shared_options.options if body.shared_options else None,
            items=body.items,
            translations=body.translations,
        )
        await self._session.commit()
        loaded = await self._require(user, public_id)
        return to_detail(loaded)

    async def upsert_translations(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        locale: str,
        body: InstrumentTranslationUpsert,
    ) -> InstrumentLocalizedRead:
        self._bind(user)
        instrument = await self._require(user, public_id)
        if instrument.clinic_id != user.clinic_id:
            raise InstrumentSystemImmutableError()
        version = _current_version(instrument)
        if version is None:
            raise InstrumentVersionConflictError()
        await self._upsert_locale_rows(
            user,
            version=version,
            locale=locale,
            title=body.title,
            item_texts=body.items,
            option_texts=body.options,
            items=version.items,
            options=version.options,
        )
        await self._session.commit()
        loaded = await self._require(user, public_id)
        if locale not in locales_complete(_current_version(loaded) or version):
            raise InstrumentTranslationIncompleteError(locale=locale)
        title = _translation_map(_current_version(loaded) or version, locale).get(
            (None, None),
            body.title,
        )
        return to_localized(loaded, locale=locale, title=title)

    async def score_instrument(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        body: InstrumentScoreRequest,
    ) -> InstrumentScoreRead:
        self._bind(user)
        instrument = await self._require(user, public_id)
        version = _current_version(instrument)
        if version is None:
            raise InstrumentNotFoundError(public_id=public_id)
        if body.locale is not None and body.locale not in locales_complete(version):
            raise InstrumentTranslationIncompleteError(locale=body.locale)
        spec = build_scoring_spec(instrument, version)
        try:
            validate_spec(spec)
        except InvalidInstrumentDefinitionError as exc:
            raise InstrumentInvalidDefinitionError(reason=str(exc)) from exc
        try:
            output = score_from_spec(
                spec,
                dict(body.answers),
                previous_total_score=body.previous_total_score,
            )
        except IncompleteInstrumentResponseError as exc:
            raise InstrumentIncompleteResponseError(
                missing_item_codes=exc.missing_item_codes
            ) from exc
        except InvalidInstrumentAnswerError as exc:
            raise InstrumentInvalidAnswerError(
                item_code=exc.item_code,
                value=exc.value,
            ) from exc
        except InstrumentScoreOutOfRangeError as exc:
            raise InstrumentInvalidDefinitionError(
                reason="score_out_of_range",
                total=exc.total,
            ) from exc
        self._audit.record_access(
            action="score",
            entity_type="instrument",
            clinic_id=user.clinic_id,
            entity_id=int(instrument.id),
            entity_public_id=instrument.public_id,
        )
        await self._session.commit()
        return to_score_read(output)

    async def _add_version(
        self,
        user: CurrentUser,
        *,
        instrument: Instrument,
        version_label: str,
        effective_from: date,
        is_current: bool,
        scoring_config: dict[str, Any],
        shared_options: list[InstrumentOptionInput] | None,
        items: list[InstrumentItemInput],
        translations: list[InstrumentLocaleTranslationInput],
    ) -> None:
        version = InstrumentVersion(
            public_id=new_ulid(),
            clinic_id=user.clinic_id,
            instrument_id=int(instrument.id),
            version=version_label,
            effective_from=effective_from,
            is_current=is_current,
            scoring_config=scoring_config,
            created_by_id=user.user_id,
            updated_by_id=user.user_id,
        )
        self._session.add(version)
        await self._session.flush()
        item_rows: list[InstrumentItem] = []
        for item in sorted(items, key=lambda i: i.position):
            item_model = InstrumentItem(
                public_id=new_ulid(),
                instrument_version_id=int(version.id),
                position=item.position,
                code=item.code,
                subscale=item.subscale,
                is_reverse_scored=item.is_reverse_scored,
                weight=item.weight,
                created_by_id=user.user_id,
                updated_by_id=user.user_id,
            )
            self._session.add(item_model)
            item_rows.append(item_model)
        await self._session.flush()
        option_by_value: dict[str, InstrumentOption] = {}
        if shared_options:
            for opt in sorted(shared_options, key=lambda o: o.position):
                option_row = InstrumentOption(
                    public_id=new_ulid(),
                    instrument_version_id=int(version.id),
                    item_id=None,
                    value=opt.value,
                    position=opt.position,
                    created_by_id=user.user_id,
                    updated_by_id=user.user_id,
                )
                self._session.add(option_row)
                await self._session.flush()
                option_by_value[str(opt.value)] = option_row
        for item_row, item_in in zip(
            item_rows, sorted(items, key=lambda i: i.position)
        ):
            if item_in.options:
                for opt in sorted(item_in.options, key=lambda o: o.position):
                    option_row = InstrumentOption(
                        public_id=new_ulid(),
                        instrument_version_id=int(version.id),
                        item_id=int(item_row.id),
                        value=opt.value,
                        position=opt.position,
                        created_by_id=user.user_id,
                        updated_by_id=user.user_id,
                    )
                    self._session.add(option_row)
                    await self._session.flush()
                    option_by_value[f"{item_in.code}:{opt.value}"] = option_row
        all_options = list(option_by_value.values())
        for tr in translations:
            await self._upsert_locale_rows(
                user,
                version=version,
                locale=tr.locale,
                title=tr.title,
                item_texts=tr.items,
                option_texts=tr.options,
                items=item_rows,
                options=all_options,
            )
        await self._session.refresh(
            version,
            attribute_names=["items", "options", "translations"],
        )
        probe = build_scoring_spec(instrument, version)
        try:
            validate_spec(probe)
        except InvalidInstrumentDefinitionError as exc:
            raise InstrumentInvalidDefinitionError(reason=str(exc)) from exc

    async def _upsert_locale_rows(
        self,
        user: CurrentUser,
        *,
        version: InstrumentVersion,
        locale: str,
        title: str,
        item_texts: dict[str, str],
        option_texts: dict[str, str],
        items: list[InstrumentItem],
        options: list[InstrumentOption],
    ) -> None:
        await self._replace_translation(
            version=version,
            locale=locale,
            item_id=None,
            option_id=None,
            text=title,
            user_id=user.user_id,
        )
        code_by_id = {row.code: row for row in items}
        for code, text in item_texts.items():
            item = code_by_id.get(code)
            if item is None:
                continue
            await self._replace_translation(
                version=version,
                locale=locale,
                item_id=int(item.id),
                option_id=None,
                text=text,
                user_id=user.user_id,
            )
        for key, text in option_texts.items():
            opt = _resolve_option_key(key, options, code_by_id)
            if opt is None:
                continue
            await self._replace_translation(
                version=version,
                locale=locale,
                item_id=None,
                option_id=int(opt.id),
                text=text,
                user_id=user.user_id,
            )

    async def _replace_translation(
        self,
        *,
        version: InstrumentVersion,
        locale: str,
        item_id: int | None,
        option_id: int | None,
        text: str,
        user_id: int,
    ) -> None:
        existing = await self._session.scalar(
            select(InstrumentTranslation).where(
                InstrumentTranslation.instrument_version_id == int(version.id),
                InstrumentTranslation.locale == locale,
                InstrumentTranslation.item_id == item_id,
                InstrumentTranslation.option_id == option_id,
                InstrumentTranslation.deleted_at.is_(None),
            )
        )
        if existing is not None:
            existing.text = text
            existing.updated_by_id = user_id
            return
        self._session.add(
            InstrumentTranslation(
                public_id=new_ulid(),
                instrument_version_id=int(version.id),
                item_id=item_id,
                option_id=option_id,
                locale=locale,
                text=text,
                created_by_id=user_id,
                updated_by_id=user_id,
            )
        )

    async def _require(self, user: CurrentUser, public_id: str) -> Instrument:
        row = await self._repo(user).get_for_read(public_id)
        if row is None:
            raise InstrumentNotFoundError(public_id=public_id)
        return row

    def _repo(self, user: CurrentUser) -> InstrumentRepository:
        return InstrumentRepository(self._session, clinic_id=user.clinic_id)

    def _bind(self, user: CurrentUser) -> None:
        set_user_id(user.user_id)
        set_clinic_id(user.clinic_id)


def _resolve_option_key(
    key: str,
    options: list[InstrumentOption],
    code_by_id: dict[str, InstrumentItem],
) -> InstrumentOption | None:
    if ":" in key:
        item_code, value_str = key.split(":", 1)
        try:
            value = int(value_str)
        except ValueError:
            return None
        for opt in options:
            if opt.value != value:
                continue
            if opt.item_id is None:
                return opt
            item = code_by_id.get(item_code)
            if item is not None and opt.item_id == item.id:
                return opt
        return None
    try:
        value = int(key)
    except ValueError:
        return None
    for opt in options:
        if opt.item_id is None and int(opt.value) == value:
            return opt
    return None
