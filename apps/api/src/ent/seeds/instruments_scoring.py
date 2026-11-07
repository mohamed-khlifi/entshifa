"""Build engine specs from launch instrument seed definitions (tests and validation)."""

from __future__ import annotations

from decimal import Decimal

from ent.engines.scoring.types import (
    InstrumentItemSpec,
    InstrumentScoringSpec,
    ScoringType,
    SeverityBandSpec,
    SubscaleSpec,
)
from ent.seeds.instruments_launch_specs import (
    LAUNCH_INSTRUMENT_SPECS,
    LaunchInstrumentSpec,
)
from ent.seeds.instruments_option_labels import option_values_for_scale

_LAUNCH_BY_CODE = {spec.code: spec for spec in LAUNCH_INSTRUMENT_SPECS}


def launch_spec_by_code(code: str) -> LaunchInstrumentSpec:
    spec = _LAUNCH_BY_CODE.get(code)
    if spec is None:
        msg = f"unknown launch instrument: {code}"
        raise KeyError(msg)
    return spec


def engine_scoring_spec_from_launch(
    spec: LaunchInstrumentSpec,
) -> InstrumentScoringSpec:
    values = option_values_for_scale(spec.scale_key)
    items = tuple(
        InstrumentItemSpec(
            code=item.code,
            position=item.position,
            allowed_values=values,
            subscale=item.subscale,
            is_reverse_scored=False,
            weight=Decimal("1"),
        )
        for item in spec.items
    )
    bands = tuple(
        SeverityBandSpec(code=b.code, min_score=b.min_score, max_score=b.max_score)
        for b in spec.severity_bands
    )
    subscales = tuple(
        SubscaleSpec(code=s.code, item_codes=s.item_codes) for s in spec.subscales
    )
    st: ScoringType = "weighted_sum" if spec.scoring_type == "weighted_sum" else "sum"
    return InstrumentScoringSpec(
        code=spec.code,
        version=spec.version,
        scoring_type=st,
        min_score=Decimal(str(spec.min_score)),
        max_score=Decimal(str(spec.max_score)),
        reference=spec.reference,
        items=items,
        subscales=subscales,
        severity_bands=bands,
        scale_multiplier=spec.scale_multiplier,
        mcid=spec.mcid,
    )
