"""Map instrument ORM rows to API schemas and scoring specs."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from ent.engines.scoring.types import (
    InstrumentItemSpec,
    InstrumentScoringSpec,
    QuestionnaireScoreOutput,
    ScoringType,
    SeverityBandSpec,
    SubscaleSpec,
)
from ent.features.questionnaires.constants import INSTRUMENT_LOCALES
from ent.features.questionnaires.models import (
    Instrument,
    InstrumentItem,
    InstrumentOption,
    InstrumentVersion,
)
from ent.features.questionnaires.schemas.responses import (
    InstrumentDetailRead,
    InstrumentItemRead,
    InstrumentLocalizedRead,
    InstrumentOptionRead,
    InstrumentScoreRead,
    InstrumentSummaryRead,
    InstrumentVersionRead,
)


def _current_version(instrument: Instrument) -> InstrumentVersion | None:
    versions = [v for v in instrument.versions if v.deleted_at is None]
    if not versions:
        return None
    current = [v for v in versions if v.is_current]
    if current:
        return sorted(current, key=lambda v: v.effective_from, reverse=True)[0]
    return sorted(versions, key=lambda v: v.effective_from, reverse=True)[0]


def _options_for_item(
    version: InstrumentVersion,
    item: InstrumentItem,
) -> list[InstrumentOption]:
    dedicated = [
        opt
        for opt in version.options
        if opt.deleted_at is None and opt.item_id == item.id
    ]
    if dedicated:
        return sorted(dedicated, key=lambda o: o.position)
    shared = [
        opt for opt in version.options if opt.deleted_at is None and opt.item_id is None
    ]
    return sorted(shared, key=lambda o: o.position)


def _translation_map(
    version: InstrumentVersion,
    locale: str,
) -> dict[tuple[int | None, int | None], str]:
    out: dict[tuple[int | None, int | None], str] = {}
    for row in version.translations:
        if row.deleted_at is not None or row.locale != locale:
            continue
        out[(row.item_id, row.option_id)] = row.text
    return out


def locales_complete(version: InstrumentVersion) -> list[str]:
    complete: list[str] = []
    active_items = [i for i in version.items if i.deleted_at is None]
    active_options = [o for o in version.options if o.deleted_at is None]
    for locale in INSTRUMENT_LOCALES:
        if _locale_is_complete(version, locale, active_items, active_options):
            complete.append(locale)
    return complete


def _locale_is_complete(
    version: InstrumentVersion,
    locale: str,
    items: list[InstrumentItem],
    options: list[InstrumentOption],
) -> bool:
    texts = _translation_map(version, locale)
    if not texts.get((None, None), "").strip():
        return False
    for item in items:
        if not texts.get((item.id, None), "").strip():
            return False
    for opt in options:
        if not texts.get((None, opt.id), "").strip():
            return False
    return True


def to_summary(instrument: Instrument) -> InstrumentSummaryRead:
    version = _current_version(instrument)
    locales: list[str] = []
    if version is not None:
        locales = locales_complete(version)
    return InstrumentSummaryRead(
        public_id=instrument.public_id,
        code=instrument.code,
        category=instrument.category,
        respondent=instrument.respondent,
        scoring_type=instrument.scoring_type,
        min_score=int(instrument.min_score),
        max_score=int(instrument.max_score),
        mcid=instrument.mcid,
        license_note=instrument.license_note,
        reference=instrument.reference,
        is_system=bool(instrument.is_system),
        is_active=bool(instrument.is_active),
        locales_available=locales,
    )


def _item_read(
    item: InstrumentItem,
    version: InstrumentVersion,
    locale: str | None,
) -> InstrumentItemRead:
    texts = _translation_map(version, locale) if locale else {}
    options = _options_for_item(version, item)
    return InstrumentItemRead(
        public_id=item.public_id,
        code=item.code,
        position=int(item.position),
        subscale=item.subscale,
        is_reverse_scored=bool(item.is_reverse_scored),
        weight=item.weight,
        text=texts.get((item.id, None)) if locale else None,
        options=[
            InstrumentOptionRead(
                public_id=opt.public_id,
                value=int(opt.value),
                position=int(opt.position),
                text=texts.get((None, opt.id)) if locale else None,
            )
            for opt in options
        ],
    )


def to_detail(
    instrument: Instrument,
    *,
    locale: str | None = None,
) -> InstrumentDetailRead:
    summary = to_summary(instrument)
    version = _current_version(instrument)
    current: InstrumentVersionRead | None = None
    items: list[InstrumentItemRead] = []
    if version is not None:
        current = InstrumentVersionRead(
            public_id=version.public_id,
            version=version.version,
            effective_from=version.effective_from,
            is_current=bool(version.is_current),
            scoring_config=dict(version.scoring_config),
        )
        active_items = sorted(
            [i for i in version.items if i.deleted_at is None],
            key=lambda i: i.position,
        )
        items = [_item_read(item, version, locale) for item in active_items]
    return InstrumentDetailRead(
        **summary.model_dump(),
        current_version=current,
        items=items,
    )


def to_localized(
    instrument: Instrument,
    *,
    locale: str,
    title: str,
) -> InstrumentLocalizedRead:
    detail = to_detail(instrument, locale=locale)
    return InstrumentLocalizedRead(
        **detail.model_dump(),
        locale=locale,
        title=title,
    )


def _decimal_config(value: Any, default: str = "1") -> Decimal:
    if value is None:
        return Decimal(default)
    return Decimal(str(value))


def build_scoring_spec(
    instrument: Instrument,
    version: InstrumentVersion,
) -> InstrumentScoringSpec:
    config = dict(version.scoring_config)
    items_sorted = sorted(
        [i for i in version.items if i.deleted_at is None],
        key=lambda i: i.position,
    )
    specs: list[InstrumentItemSpec] = []
    reverse_set = frozenset(
        config.get("reverseScoredItems") or config.get("reverse_scored_items") or []
    )
    for item in items_sorted:
        opts = _options_for_item(version, item)
        allowed = tuple(sorted({int(o.value) for o in opts}))
        specs.append(
            InstrumentItemSpec(
                code=item.code,
                position=int(item.position),
                allowed_values=allowed,
                subscale=item.subscale,
                is_reverse_scored=bool(item.is_reverse_scored)
                or item.code in reverse_set,
                weight=Decimal(str(item.weight)),
            )
        )
    bands_raw = config.get("severityBands") or config.get("severity_bands") or []
    bands: list[SeverityBandSpec] = []
    for band in bands_raw:
        if isinstance(band, dict):
            bands.append(
                SeverityBandSpec(
                    code=str(band["code"]),
                    min_score=_decimal_config(
                        band.get("minScore", band.get("min_score"))
                    ),
                    max_score=_decimal_config(
                        band.get("maxScore", band.get("max_score"))
                    ),
                )
            )
    subscales_raw = config.get("subscales") or []
    subscales: list[SubscaleSpec] = []
    for sub in subscales_raw:
        if isinstance(sub, dict):
            codes = sub.get("itemCodes") or sub.get("item_codes") or []
            subscales.append(
                SubscaleSpec(
                    code=str(sub["code"]), item_codes=tuple(str(c) for c in codes)
                )
            )
    multiplier = _decimal_config(
        config.get("scaleMultiplier", config.get("scale_multiplier")),
    )
    st: ScoringType = (
        "weighted_sum" if instrument.scoring_type == "weighted_sum" else "sum"
    )
    return InstrumentScoringSpec(
        code=instrument.code,
        version=version.version,
        scoring_type=st,
        min_score=Decimal(str(instrument.min_score)),
        max_score=Decimal(str(instrument.max_score)),
        reference=instrument.reference,
        items=tuple(specs),
        subscales=tuple(subscales),
        severity_bands=tuple(bands),
        scale_multiplier=multiplier,
        mcid=instrument.mcid,
    )


def to_score_read(output: QuestionnaireScoreOutput) -> InstrumentScoreRead:
    subscales = {k: v for k, v in output.subscale_scores.items()}
    return InstrumentScoreRead(
        total_score=output.total_score,
        severity_band=output.severity_band,
        subscale_scores=subscales,
        change_from_previous=output.change_from_previous,
        mcid_reached=output.mcid_reached,
        engine_code=output.calculation.code,
        engine_version=output.calculation.version,
        reference=output.calculation.reference,
    )
