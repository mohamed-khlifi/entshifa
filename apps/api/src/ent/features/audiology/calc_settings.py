"""Resolve clinic audiology calculation settings."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.errors.exceptions import ValidationError
from ent.core.security.principal import CurrentUser
from ent.engines.audiology.types import AsymmetryRule, PtaFormula, ShiftRule
from ent.features.clinics.resolver import SettingResolver
from ent.features.clinics.setting_keys import (
    AbrInterauralThresholdValue,
    AsymmetryRuleValue,
    ClinicalSettingKey,
    ShiftRuleValue,
)


async def resolve_calc_settings(
    session: AsyncSession,
    user: CurrentUser,
) -> tuple[PtaFormula, AsymmetryRule, ShiftRule]:
    resolver = SettingResolver(session)
    pta_resolved = await resolver.resolve(
        key=ClinicalSettingKey.PTA_FORMULA.value,
        clinic_id=user.clinic_id,
        user_id=user.user_id,
    )
    asym_resolved = await resolver.resolve(
        key=ClinicalSettingKey.ASYMMETRY_RULE.value,
        clinic_id=user.clinic_id,
        user_id=user.user_id,
    )
    shift_resolved = await resolver.resolve(
        key=ClinicalSettingKey.SHIFT_RULE.value,
        clinic_id=user.clinic_id,
        user_id=user.user_id,
    )
    pta = pta_resolved.value
    if not isinstance(pta, str):
        raise ValidationError(reason="invalid_pta_formula")
    asym = AsymmetryRuleValue.model_validate(asym_resolved.value)
    shift = ShiftRuleValue.model_validate(shift_resolved.value)
    return (
        pta,  # type: ignore[return-value]
        AsymmetryRule(
            adjacent_db=asym.adjacent_db,
            adjacent_count=asym.adjacent_count,
            single_db=asym.single_db,
            wrs_percent=asym.wrs_percent,
        ),
        shift.rule,
    )


async def resolve_abr_interaural_threshold_ms(
    session: AsyncSession,
    user: CurrentUser,
) -> Decimal:
    resolver = SettingResolver(session)
    resolved = await resolver.resolve(
        key=ClinicalSettingKey.ABR_INTERAURAL_V_THRESHOLD_MS.value,
        clinic_id=user.clinic_id,
        user_id=user.user_id,
    )
    parsed = AbrInterauralThresholdValue.model_validate(resolved.value)
    return parsed.threshold_ms
