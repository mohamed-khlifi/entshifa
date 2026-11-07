"""Seed system questionnaire instruments (P5-02 / architecture §28)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ent.core.utils.ids import new_ulid
from ent.engines.scoring.sum_scorer import validate_spec
from ent.features.questionnaires.mapping import (
    build_scoring_spec,
    locales_complete,
)
from ent.features.questionnaires.models import (
    Instrument,
    InstrumentItem,
    InstrumentOption,
    InstrumentTranslation,
    InstrumentVersion,
)
from ent.seeds.instruments_launch_specs import (
    LAUNCH_INSTRUMENT_SPECS,
    LaunchInstrumentSpec,
    locale_translations_for_spec,
    scoring_config_for_spec,
    shared_options_for_spec,
)

_VERSION_LABEL = "1.0.0"
_EFFECTIVE_FROM = date(2026, 1, 1)


async def seed_instruments(session: AsyncSession) -> int:
    """Idempotently seed the ten launch patient-reported instruments."""

    created_count = 0
    for launch in LAUNCH_INSTRUMENT_SPECS:
        if await _upsert_launch_instrument(session, launch):
            created_count += 1
    await session.flush()
    return created_count


async def _upsert_launch_instrument(
    session: AsyncSession,
    launch: LaunchInstrumentSpec,
) -> bool:
    created = False
    instrument = await session.scalar(
        select(Instrument).where(
            Instrument.code == launch.code,
            Instrument.clinic_id.is_(None),
            Instrument.deleted_at.is_(None),
        )
    )
    if instrument is None:
        instrument = Instrument(
            public_id=new_ulid(),
            clinic_id=None,
            code=launch.code,
            category=launch.category,
            respondent=launch.respondent,
            scoring_type=launch.scoring_type,
            min_score=launch.min_score,
            max_score=launch.max_score,
            mcid=launch.mcid,
            license_note=launch.license_note,
            reference=launch.reference,
            is_system=True,
            is_active=True,
        )
        session.add(instrument)
        await session.flush()
        created = True
    else:
        instrument.category = launch.category
        instrument.respondent = launch.respondent
        instrument.scoring_type = launch.scoring_type
        instrument.min_score = launch.min_score
        instrument.max_score = launch.max_score
        instrument.mcid = launch.mcid
        instrument.license_note = launch.license_note
        instrument.reference = launch.reference
        instrument.is_system = True
        instrument.is_active = True

    version = await session.scalar(
        select(InstrumentVersion).where(
            InstrumentVersion.instrument_id == instrument.id,
            InstrumentVersion.version == _VERSION_LABEL,
            InstrumentVersion.deleted_at.is_(None),
        )
    )
    scoring_config = scoring_config_for_spec(launch)
    if version is None:
        version = InstrumentVersion(
            public_id=new_ulid(),
            clinic_id=None,
            instrument_id=int(instrument.id),
            version=_VERSION_LABEL,
            effective_from=_EFFECTIVE_FROM,
            is_current=True,
            scoring_config=scoring_config,
        )
        session.add(version)
        await session.flush()
    else:
        version.effective_from = _EFFECTIVE_FROM
        version.is_current = True
        version.scoring_config = scoring_config

    await _sync_items_and_options(session, version, launch)
    await _sync_translations(session, version, launch)

    loaded = await session.scalar(
        select(Instrument)
        .where(Instrument.id == instrument.id)
        .options(
            selectinload(Instrument.versions).selectinload(InstrumentVersion.items),
            selectinload(Instrument.versions).selectinload(InstrumentVersion.options),
            selectinload(Instrument.versions).selectinload(
                InstrumentVersion.translations
            ),
        )
    )
    if loaded is None:
        msg = "instrument load failed after seed"
        raise RuntimeError(msg)
    current = next(
        v
        for v in loaded.versions
        if v.version == _VERSION_LABEL and v.deleted_at is None
    )
    complete = locales_complete(current)
    if set(complete) != {"en", "fr", "ar"}:
        msg = f"incomplete locales for {launch.code}: {complete}"
        raise RuntimeError(msg)
    engine_spec = build_scoring_spec(loaded, current)
    validate_spec(engine_spec)
    return created


async def _sync_items_and_options(
    session: AsyncSession,
    version: InstrumentVersion,
    launch: LaunchInstrumentSpec,
) -> None:
    existing_items = (
        await session.scalars(
            select(InstrumentItem).where(
                InstrumentItem.instrument_version_id == version.id,
                InstrumentItem.deleted_at.is_(None),
            )
        )
    ).all()
    by_code = {row.code: row for row in existing_items}
    for item in launch.items:
        row = by_code.get(item.code)
        if row is None:
            row = InstrumentItem(
                public_id=new_ulid(),
                instrument_version_id=int(version.id),
                position=item.position,
                code=item.code,
                subscale=item.subscale,
                is_reverse_scored=False,
                weight=Decimal("1"),
            )
            session.add(row)
        else:
            row.position = item.position
            row.subscale = item.subscale
            row.is_reverse_scored = False
            row.weight = Decimal("1")
    await session.flush()

    values = [opt["value"] for opt in shared_options_for_spec(launch)]
    existing_options = (
        await session.scalars(
            select(InstrumentOption).where(
                InstrumentOption.instrument_version_id == version.id,
                InstrumentOption.item_id.is_(None),
                InstrumentOption.deleted_at.is_(None),
            )
        )
    ).all()
    by_value = {int(opt.value): opt for opt in existing_options}
    for position, value in enumerate(values, start=1):
        opt = by_value.get(value)
        if opt is None:
            session.add(
                InstrumentOption(
                    public_id=new_ulid(),
                    instrument_version_id=int(version.id),
                    item_id=None,
                    value=value,
                    position=position,
                )
            )
        else:
            opt.position = position


async def _sync_translations(
    session: AsyncSession,
    version: InstrumentVersion,
    launch: LaunchInstrumentSpec,
) -> None:
    items = (
        await session.scalars(
            select(InstrumentItem).where(
                InstrumentItem.instrument_version_id == version.id,
                InstrumentItem.deleted_at.is_(None),
            )
        )
    ).all()
    code_to_item = {row.code: row for row in items}
    options = (
        await session.scalars(
            select(InstrumentOption).where(
                InstrumentOption.instrument_version_id == version.id,
                InstrumentOption.item_id.is_(None),
                InstrumentOption.deleted_at.is_(None),
            )
        )
    ).all()
    value_to_option = {int(opt.value): opt for opt in options}

    for block in locale_translations_for_spec(launch):
        locale = block["locale"]
        await _upsert_translation(
            session,
            version_id=int(version.id),
            locale=locale,
            item_id=None,
            option_id=None,
            text=str(block["title"]),
        )
        item_texts: dict[str, str] = block["items"]
        for code, text in item_texts.items():
            item = code_to_item.get(code)
            if item is None:
                continue
            await _upsert_translation(
                session,
                version_id=int(version.id),
                locale=locale,
                item_id=int(item.id),
                option_id=None,
                text=text,
            )
        option_texts: dict[str, str] = block["options"]
        for value_str, text in option_texts.items():
            opt = value_to_option.get(int(value_str))
            if opt is None:
                continue
            await _upsert_translation(
                session,
                version_id=int(version.id),
                locale=locale,
                item_id=None,
                option_id=int(opt.id),
                text=text,
            )


async def _upsert_translation(
    session: AsyncSession,
    *,
    version_id: int,
    locale: str,
    item_id: int | None,
    option_id: int | None,
    text: str,
) -> None:
    existing = await session.scalar(
        select(InstrumentTranslation).where(
            InstrumentTranslation.instrument_version_id == version_id,
            InstrumentTranslation.locale == locale,
            InstrumentTranslation.item_id == item_id,
            InstrumentTranslation.option_id == option_id,
            InstrumentTranslation.deleted_at.is_(None),
        )
    )
    if existing is not None:
        existing.text = text
        return
    session.add(
        InstrumentTranslation(
            public_id=new_ulid(),
            instrument_version_id=version_id,
            item_id=item_id,
            option_id=option_id,
            locale=locale,
            text=text,
        )
    )
