"""Map audiogram ORM rows to API schemas."""

from __future__ import annotations

from decimal import Decimal

from ent.core.schemas.base import PageMeta, PageSchema
from ent.features.audiology.constants import EXTENDED_HIGH_FREQUENCIES_HZ
from ent.features.audiology.models import Audiogram, AudiogramThreshold
from ent.features.audiology.schemas.responses import AudiogramRead, ThresholdRead


def _decimal(value: Decimal | None) -> float | None:
    if value is None:
        return None
    return float(value)


def threshold_read(row: AudiogramThreshold) -> ThresholdRead:
    return ThresholdRead(
        ear=row.ear,  # type: ignore[arg-type]
        conduction=row.conduction,  # type: ignore[arg-type]
        frequency_hz=int(row.frequency_hz),
        level_db=row.level_db,
        is_masked=bool(row.is_masked),
        is_no_response=bool(row.is_no_response),
    )


def audiogram_read(row: Audiogram) -> AudiogramRead:
    thresholds = [threshold_read(item) for item in row.thresholds]
    extended = any(
        item.frequency_hz in EXTENDED_HIGH_FREQUENCIES_HZ for item in row.thresholds
    )
    baseline_public_id = (
        row.baseline_audiogram.public_id if row.baseline_audiogram is not None else None
    )
    return AudiogramRead(
        public_id=row.public_id,
        patient_public_id=row.patient.public_id,
        encounter_public_id=row.encounter.public_id if row.encounter else None,
        performed_at=row.performed_at,
        performed_by_public_id=row.performed_by.public_id,
        equipment=row.equipment,
        calibration_date=row.calibration_date,
        transducer=row.transducer,  # type: ignore[arg-type]
        method=row.method,  # type: ignore[arg-type]
        reliability=row.reliability,  # type: ignore[arg-type]
        is_baseline=bool(row.is_baseline),
        baseline_audiogram_public_id=baseline_public_id,
        pta_formula=row.pta_formula,
        pta_right=_decimal(row.pta_right),
        pta_left=_decimal(row.pta_left),
        abg_right=_decimal(row.abg_right),
        abg_left=_decimal(row.abg_left),
        grade_right=row.grade_right,
        grade_left=row.grade_left,
        loss_type_right=row.loss_type_right,
        loss_type_left=row.loss_type_left,
        configuration_right=row.configuration_right,
        configuration_left=row.configuration_left,
        asymmetry_flag=bool(row.asymmetry_flag),
        shift_flag=bool(row.shift_flag),
        engine_version=row.engine_version,
        interpretation_text=row.interpretation_text,
        status=row.status,
        version=int(row.version),
        has_extended_high_frequencies=extended,
        thresholds=thresholds,
    )


def to_page(
    items: list[AudiogramRead],
    *,
    total: int,
    limit: int,
    offset: int | None,
) -> PageSchema[AudiogramRead]:
    return PageSchema(
        items=items,
        page=PageMeta(total=total, limit=limit, offset=offset, next_cursor=None),
    )
