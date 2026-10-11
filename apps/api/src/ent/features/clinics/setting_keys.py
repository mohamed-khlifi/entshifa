"""Clinical setting keys and value validation (P1-01).

Allowed shapes live here so writes are typed. Runtime defaults live only as
``setting`` table rows (system scope), never as fallback literals in resolvers.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field
from pydantic import ValidationError as PydanticValidationError

from ent.core.errors.exceptions import ValidationError


class ClinicalSettingKey(StrEnum):
    PTA_FORMULA = "pta_formula"
    ASYMMETRY_RULE = "asymmetry_rule"
    POLYP_SCALE = "polyp_scale"
    TUBE_RECALL_INTERVAL_MONTHS = "tube_recall_interval_months"
    OTOLOGY_FOLLOW_UP = "otology_follow_up"
    FOLLOW_UP_DEFAULTS = "follow_up_defaults"


# VERIFY: labels match feature-spec §8.5 PTA formula options.
_PTA_FORMULAS = frozenset({"3freq", "4freq_who", "high_freq", "fletcher"})
# Overall polyp grade. Lund-Kennedy polyp item stays 0-2 and is not this setting.
# VERIFY: Meltzer 0-4 and Lildholdt 0-3 grade prose (feature-spec appendix A).
_POLYP_SCALES = frozenset({"meltzer", "lildholdt"})


class AsymmetryRuleValue(BaseModel):
    adjacent_db: int = Field(ge=1, le=100)
    adjacent_count: int = Field(ge=1, le=10)
    single_db: int = Field(ge=1, le=100)
    wrs_percent: int = Field(ge=1, le=100)


class FollowUpDefaultsValue(BaseModel):
    routine_months: int = Field(ge=1, le=120)
    post_op_days: int = Field(ge=1, le=365)


class OtologyFollowUpValue(BaseModel):
    """Editable office-ear intervals. Appendix C is the source of the seed row."""

    tube_first_check_days: int = Field(ge=1, le=90)
    tube_first_window_days: int = Field(ge=0, le=30)
    tube_interval_window_days: int = Field(ge=0, le=90)
    wick_removal_days: int = Field(ge=1, le=14)
    wick_window_days: int = Field(ge=0, le=7)
    cavity_cleaning_months: int = Field(ge=1, le=24)
    cavity_window_days: int = Field(ge=0, le=90)
    canal_injury_window_days: int = Field(ge=0, le=30)


def validate_setting_value(key: str, value: Any) -> Any:
    """Return a JSON-serialisable value or raise ``ValidationError``."""

    try:
        clinical_key = ClinicalSettingKey(key)
    except ValueError as exc:
        raise ValidationError(reason="unknown_setting_key", key=key) from exc

    if clinical_key is ClinicalSettingKey.PTA_FORMULA:
        if not isinstance(value, str) or value not in _PTA_FORMULAS:
            raise ValidationError(reason="invalid_pta_formula", key=key)
        return value

    if clinical_key is ClinicalSettingKey.POLYP_SCALE:
        if not isinstance(value, str) or value not in _POLYP_SCALES:
            raise ValidationError(reason="invalid_polyp_scale", key=key)
        return value

    if clinical_key is ClinicalSettingKey.TUBE_RECALL_INTERVAL_MONTHS:
        if (
            not isinstance(value, int)
            or isinstance(value, bool)
            or not 1 <= value <= 60
        ):
            raise ValidationError(reason="invalid_tube_recall_interval", key=key)
        return value

    if clinical_key is ClinicalSettingKey.ASYMMETRY_RULE:
        try:
            return AsymmetryRuleValue.model_validate(value).model_dump()
        except PydanticValidationError as exc:
            raise ValidationError(reason="invalid_asymmetry_rule", key=key) from exc

    if clinical_key is ClinicalSettingKey.FOLLOW_UP_DEFAULTS:
        try:
            return FollowUpDefaultsValue.model_validate(value).model_dump()
        except PydanticValidationError as exc:
            raise ValidationError(reason="invalid_follow_up_defaults", key=key) from exc

    if clinical_key is ClinicalSettingKey.OTOLOGY_FOLLOW_UP:
        try:
            return OtologyFollowUpValue.model_validate(value).model_dump()
        except PydanticValidationError as exc:
            raise ValidationError(reason="invalid_otology_follow_up", key=key) from exc

    raise ValidationError(reason="unknown_setting_key", key=key)


def all_clinical_setting_keys() -> frozenset[str]:
    return frozenset(key.value for key in ClinicalSettingKey)
