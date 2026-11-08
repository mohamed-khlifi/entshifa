"""Interactive calculator catalog, input metadata, and pure runners (P5-05)."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Literal

from ent.engines.airway.ett_size import CODE as ETT_CODE
from ent.engines.airway.ett_size import FORMULA as ETT_FORMULA
from ent.engines.airway.ett_size import REFERENCE as ETT_REFERENCE
from ent.engines.airway.ett_size import VERSION as ETT_VERSION
from ent.engines.airway.ett_size import score as ett_score
from ent.engines.airway.myer_cotton import CODE as MYER_COTTON_CODE
from ent.engines.airway.myer_cotton import FORMULA as MYER_COTTON_FORMULA
from ent.engines.airway.myer_cotton import REFERENCE as MYER_COTTON_REFERENCE
from ent.engines.airway.myer_cotton import VERSION as MYER_COTTON_VERSION
from ent.engines.airway.myer_cotton import score as myer_cotton_score
from ent.engines.audiology.abr import CODE as ABR_CODE
from ent.engines.audiology.abr import FORMULA as ABR_FORMULA
from ent.engines.audiology.abr import REFERENCE as ABR_REFERENCE
from ent.engines.audiology.abr import VERSION as ABR_VERSION
from ent.engines.audiology.abr import AbrWaveInput
from ent.engines.audiology.abr import score as abr_score
from ent.engines.audiology.air_bone_gap import CODE as ABG_CODE
from ent.engines.audiology.air_bone_gap import FORMULA as ABG_FORMULA
from ent.engines.audiology.air_bone_gap import REFERENCE as ABG_REFERENCE
from ent.engines.audiology.air_bone_gap import VERSION as ABG_VERSION
from ent.engines.audiology.air_bone_gap import score as abg_score
from ent.engines.audiology.asymmetry import CODE as ASYMMETRY_CODE
from ent.engines.audiology.asymmetry import FORMULA as ASYMMETRY_FORMULA
from ent.engines.audiology.asymmetry import REFERENCE as ASYMMETRY_REFERENCE
from ent.engines.audiology.asymmetry import VERSION as ASYMMETRY_VERSION
from ent.engines.audiology.asymmetry import score as asymmetry_score
from ent.engines.audiology.audiogram_svg import CODE as AUDIOGRAM_SVG_CODE
from ent.engines.audiology.audiogram_svg import FORMULA as AUDIOGRAM_SVG_FORMULA
from ent.engines.audiology.audiogram_svg import REFERENCE as AUDIOGRAM_SVG_REFERENCE
from ent.engines.audiology.audiogram_svg import VERSION as AUDIOGRAM_SVG_VERSION
from ent.engines.audiology.candidacy import CODE as CANDIDACY_CODE
from ent.engines.audiology.candidacy import FORMULA as CANDIDACY_FORMULA
from ent.engines.audiology.candidacy import REFERENCE as CANDIDACY_REFERENCE
from ent.engines.audiology.candidacy import VERSION as CANDIDACY_VERSION
from ent.engines.audiology.candidacy import CandidacyInput, device_candidacy_calculation
from ent.engines.audiology.configuration import CODE as CONFIG_CODE
from ent.engines.audiology.configuration import FORMULA as CONFIG_FORMULA
from ent.engines.audiology.configuration import REFERENCE as CONFIG_REFERENCE
from ent.engines.audiology.configuration import VERSION as CONFIG_VERSION
from ent.engines.audiology.configuration import score as configuration_score
from ent.engines.audiology.ehdi_136 import CODE as EHDI_CODE
from ent.engines.audiology.ehdi_136 import FORMULA as EHDI_FORMULA
from ent.engines.audiology.ehdi_136 import REFERENCE as EHDI_REFERENCE
from ent.engines.audiology.ehdi_136 import VERSION as EHDI_VERSION
from ent.engines.audiology.ehdi_136 import Ehdi136Input, ehdi_136_calculation
from ent.engines.audiology.impairment import CODE as IMPAIRMENT_CODE
from ent.engines.audiology.impairment import FORMULA as IMPAIRMENT_FORMULA
from ent.engines.audiology.impairment import REFERENCE as IMPAIRMENT_REFERENCE
from ent.engines.audiology.impairment import VERSION as IMPAIRMENT_VERSION
from ent.engines.audiology.impairment import score_binaural as impairment_score
from ent.engines.audiology.interaural import CODE as INTERAURAL_CODE
from ent.engines.audiology.interaural import FORMULA as INTERAURAL_FORMULA
from ent.engines.audiology.interaural import REFERENCE as INTERAURAL_REFERENCE
from ent.engines.audiology.interaural import VERSION as INTERAURAL_VERSION
from ent.engines.audiology.interaural import score as interaural_score
from ent.engines.audiology.loss_type import CODE as LOSS_TYPE_CODE
from ent.engines.audiology.loss_type import FORMULA as LOSS_TYPE_FORMULA
from ent.engines.audiology.loss_type import REFERENCE as LOSS_TYPE_REFERENCE
from ent.engines.audiology.loss_type import VERSION as LOSS_TYPE_VERSION
from ent.engines.audiology.loss_type import score as loss_type_score
from ent.engines.audiology.pta import CODE as PTA_CODE
from ent.engines.audiology.pta import FORMULA as PTA_FORMULA
from ent.engines.audiology.pta import REFERENCE as PTA_REFERENCE
from ent.engines.audiology.pta import VERSION as PTA_VERSION
from ent.engines.audiology.pta import score as pta_score
from ent.engines.audiology.speech_agreement import CODE as SPEECH_CODE
from ent.engines.audiology.speech_agreement import FORMULA as SPEECH_FORMULA
from ent.engines.audiology.speech_agreement import REFERENCE as SPEECH_REFERENCE
from ent.engines.audiology.speech_agreement import VERSION as SPEECH_VERSION
from ent.engines.audiology.speech_agreement import score as speech_score
from ent.engines.audiology.threshold_shift import CODE as SHIFT_CODE
from ent.engines.audiology.threshold_shift import FORMULA as SHIFT_FORMULA
from ent.engines.audiology.threshold_shift import REFERENCE as SHIFT_REFERENCE
from ent.engines.audiology.threshold_shift import VERSION as SHIFT_VERSION
from ent.engines.audiology.threshold_shift import score as shift_score
from ent.engines.audiology.tympanometry import CODE as TYMP_CODE
from ent.engines.audiology.tympanometry import FORMULA as TYMP_FORMULA
from ent.engines.audiology.tympanometry import REFERENCE as TYMP_REFERENCE
from ent.engines.audiology.tympanometry import VERSION as TYMP_VERSION
from ent.engines.audiology.tympanometry import TympanogramInput
from ent.engines.audiology.tympanometry import score as tymp_score
from ent.engines.audiology.types import (
    ABG_FREQUENCIES_HZ,
    AIR_CONFIG_FREQUENCIES_HZ,
    IMPAIRMENT_FREQUENCIES_HZ,
    PTA_3_FREQUENCIES_HZ,
    WHO_GRADE_FREQUENCIES_HZ,
    AsymmetryRule,
    ThresholdPoint,
)
from ent.engines.audiology.who_grading import CODE as WHO_CODE
from ent.engines.audiology.who_grading import FORMULA as WHO_FORMULA
from ent.engines.audiology.who_grading import REFERENCE as WHO_REFERENCE
from ent.engines.audiology.who_grading import VERSION as WHO_VERSION
from ent.engines.audiology.who_grading import score as who_score
from ent.engines.calculator_errors import CalculatorInputError
from ent.engines.calculator_parsers import (
    collect_thresholds,
    domain_from_code,
    optional_date,
    optional_decimal,
    optional_int,
    optional_str,
    require_bool,
    require_date,
    require_decimal,
    require_int,
    require_str,
)
from ent.engines.endoscopy.adenoid import CODE as ADENOID_CODE
from ent.engines.endoscopy.adenoid import FORMULA as ADENOID_FORMULA
from ent.engines.endoscopy.adenoid import REFERENCE as ADENOID_REFERENCE
from ent.engines.endoscopy.adenoid import VERSION as ADENOID_VERSION
from ent.engines.endoscopy.adenoid import score as adenoid_score
from ent.engines.endoscopy.lund_kennedy import CODE as LK_CODE
from ent.engines.endoscopy.lund_kennedy import FORMULA as LK_FORMULA
from ent.engines.endoscopy.lund_kennedy import ITEMS as LK_ITEMS
from ent.engines.endoscopy.lund_kennedy import REFERENCE as LK_REFERENCE
from ent.engines.endoscopy.lund_kennedy import VERSION as LK_VERSION
from ent.engines.endoscopy.lund_kennedy import score as lk_score
from ent.engines.endoscopy.lund_mackay import CODE as LM_CODE
from ent.engines.endoscopy.lund_mackay import FORMULA as LM_FORMULA
from ent.engines.endoscopy.lund_mackay import REFERENCE as LM_REFERENCE
from ent.engines.endoscopy.lund_mackay import SINUS_ITEMS as LM_SINUS_ITEMS
from ent.engines.endoscopy.lund_mackay import VERSION as LM_VERSION
from ent.engines.endoscopy.lund_mackay import score as lund_mackay_score
from ent.engines.endoscopy.modified_lund_kennedy import CODE as MODIFIED_LK_CODE
from ent.engines.endoscopy.modified_lund_kennedy import FORMULA as MODIFIED_LK_FORMULA
from ent.engines.endoscopy.modified_lund_kennedy import ITEMS as MODIFIED_LK_ITEMS
from ent.engines.endoscopy.modified_lund_kennedy import (
    REFERENCE as MODIFIED_LK_REFERENCE,
)
from ent.engines.endoscopy.modified_lund_kennedy import VERSION as MODIFIED_LK_VERSION
from ent.engines.endoscopy.modified_lund_kennedy import score as modified_lk_score
from ent.engines.endoscopy.polyp_grade import CODE as POLYP_CODE
from ent.engines.endoscopy.polyp_grade import FORMULA as POLYP_FORMULA
from ent.engines.endoscopy.polyp_grade import REFERENCE as POLYP_REFERENCE
from ent.engines.endoscopy.polyp_grade import VERSION as POLYP_VERSION
from ent.engines.endoscopy.polyp_grade import score as polyp_score
from ent.engines.general.bmi import CODE as BMI_CODE
from ent.engines.general.bmi import FORMULA as BMI_FORMULA
from ent.engines.general.bmi import REFERENCE as BMI_REFERENCE
from ent.engines.general.bmi import VERSION as BMI_VERSION
from ent.engines.general.bmi import score as bmi_score
from ent.engines.general.bsa import CODE as BSA_CODE
from ent.engines.general.bsa import FORMULA as BSA_FORMULA
from ent.engines.general.bsa import REFERENCE as BSA_REFERENCE
from ent.engines.general.bsa import VERSION as BSA_VERSION
from ent.engines.general.bsa import score as bsa_score
from ent.engines.general.corrected_age import CODE as CORRECTED_AGE_CODE
from ent.engines.general.corrected_age import FORMULA as CORRECTED_AGE_FORMULA
from ent.engines.general.corrected_age import REFERENCE as CORRECTED_AGE_REFERENCE
from ent.engines.general.corrected_age import VERSION as CORRECTED_AGE_VERSION
from ent.engines.general.corrected_age import score as corrected_age_score
from ent.engines.laryngoscopy.grbas import CODE as GRBAS_CODE
from ent.engines.laryngoscopy.grbas import FORMULA as GRBAS_FORMULA
from ent.engines.laryngoscopy.grbas import ITEMS as GRBAS_ITEMS
from ent.engines.laryngoscopy.grbas import REFERENCE as GRBAS_REFERENCE
from ent.engines.laryngoscopy.grbas import VERSION as GRBAS_VERSION
from ent.engines.laryngoscopy.grbas import score as grbas_score
from ent.engines.laryngoscopy.penetration_aspiration import CODE as PAS_CODE
from ent.engines.laryngoscopy.penetration_aspiration import (
    FORMULA as PAS_FORMULA,
)
from ent.engines.laryngoscopy.penetration_aspiration import (
    REFERENCE as PAS_REFERENCE,
)
from ent.engines.laryngoscopy.penetration_aspiration import VERSION as PAS_VERSION
from ent.engines.laryngoscopy.penetration_aspiration import score as pas_score
from ent.engines.laryngoscopy.reflux_finding_score import ALLOWED as RFS_ALLOWED
from ent.engines.laryngoscopy.reflux_finding_score import CODE as RFS_CODE
from ent.engines.laryngoscopy.reflux_finding_score import FORMULA as RFS_FORMULA
from ent.engines.laryngoscopy.reflux_finding_score import ITEMS as RFS_ITEMS
from ent.engines.laryngoscopy.reflux_finding_score import REFERENCE as RFS_REFERENCE
from ent.engines.laryngoscopy.reflux_finding_score import VERSION as RFS_VERSION
from ent.engines.laryngoscopy.reflux_finding_score import score as rfs_score
from ent.engines.prescriptions.pediatric_dosing import CODE as PEDIATRIC_CODE
from ent.engines.prescriptions.pediatric_dosing import FORMULA as PEDIATRIC_FORMULA
from ent.engines.prescriptions.pediatric_dosing import REFERENCE as PEDIATRIC_REFERENCE
from ent.engines.prescriptions.pediatric_dosing import (
    VERSION as PEDIATRIC_VERSION,
)
from ent.engines.prescriptions.pediatric_dosing import (
    DosingRule,
    PediatricDoseInput,
    weight_based_dose,
)
from ent.engines.prescriptions.steroid_taper import CODE as TAPER_CODE
from ent.engines.prescriptions.steroid_taper import FORMULA as TAPER_FORMULA
from ent.engines.prescriptions.steroid_taper import REFERENCE as TAPER_REFERENCE
from ent.engines.prescriptions.steroid_taper import VERSION as TAPER_VERSION
from ent.engines.prescriptions.steroid_taper import TaperInput, generate_steroid_taper
from ent.engines.recalls.protocol_resolver import CODE as PROTOCOL_RESOLVER_CODE
from ent.engines.recalls.protocol_resolver import FORMULA as PROTOCOL_RESOLVER_FORMULA
from ent.engines.recalls.protocol_resolver import (
    REFERENCE as PROTOCOL_RESOLVER_REFERENCE,
)
from ent.engines.recalls.protocol_resolver import VERSION as PROTOCOL_RESOLVER_VERSION
from ent.engines.results import CalculationResult
from ent.engines.scoring.sum_scorer import CODE as SCORING_SUM_CODE
from ent.engines.scoring.sum_scorer import FORMULA as SCORING_SUM_FORMULA
from ent.engines.scoring.sum_scorer import REFERENCE as SCORING_SUM_REFERENCE
from ent.engines.scoring.sum_scorer import VERSION as SCORING_SUM_VERSION
from ent.engines.surgery.adenotonsillectomy import CODE as ATOSA_CODE
from ent.engines.surgery.adenotonsillectomy import FORMULA as ATOSA_FORMULA
from ent.engines.surgery.adenotonsillectomy import REFERENCE as ATOSA_REFERENCE
from ent.engines.surgery.adenotonsillectomy import VERSION as ATOSA_VERSION
from ent.engines.surgery.adenotonsillectomy import (
    AdenotonsillectomyInput,
    adenotonsillectomy_checklist,
)
from ent.engines.surgery.paradise import CODE as PARADISE_CODE
from ent.engines.surgery.paradise import FORMULA as PARADISE_FORMULA
from ent.engines.surgery.paradise import REFERENCE as PARADISE_REFERENCE
from ent.engines.surgery.paradise import VERSION as PARADISE_VERSION
from ent.engines.surgery.paradise import ParadiseInput, paradise_checklist
from ent.engines.surgery.tube_criteria import CODE as TUBE_CODE
from ent.engines.surgery.tube_criteria import FORMULA as TUBE_FORMULA
from ent.engines.surgery.tube_criteria import REFERENCE as TUBE_REFERENCE
from ent.engines.surgery.tube_criteria import VERSION as TUBE_VERSION
from ent.engines.surgery.tube_criteria import TubeCriteriaInput, tube_criteria_checklist

InputKind = Literal["integer", "decimal", "select", "boolean", "date"]
Runner = Callable[[Mapping[str, Any]], CalculationResult]


@dataclass(frozen=True, slots=True)
class CalculatorInputOption:
    value: str
    label_key: str


@dataclass(frozen=True, slots=True)
class CalculatorInputField:
    name: str
    kind: InputKind
    required: bool
    label_key: str
    unit: str | None = None
    min_value: str | None = None
    max_value: str | None = None
    default_value: str | None = None
    options: tuple[CalculatorInputOption, ...] = ()


@dataclass(frozen=True, slots=True)
class CalculatorSpec:
    code: str
    version: str
    reference: str
    unit: str | None
    formula: str
    domain: str
    inputs: tuple[CalculatorInputField, ...]
    interactive: bool


def _int_field(
    name: str,
    *,
    label_key: str,
    minimum: int,
    maximum: int,
    required: bool = True,
    unit: str | None = None,
    default_value: str | None = None,
) -> CalculatorInputField:
    return CalculatorInputField(
        name=name,
        kind="integer",
        required=required,
        label_key=label_key,
        unit=unit,
        min_value=str(minimum),
        max_value=str(maximum),
        default_value=default_value,
    )


def _decimal_field(
    name: str,
    *,
    label_key: str,
    minimum: str,
    maximum: str,
    required: bool = True,
    unit: str | None = None,
) -> CalculatorInputField:
    return CalculatorInputField(
        name=name,
        kind="decimal",
        required=required,
        label_key=label_key,
        unit=unit,
        min_value=minimum,
        max_value=maximum,
    )


def _bool_field(
    name: str, *, label_key: str, required: bool = True
) -> CalculatorInputField:
    return CalculatorInputField(
        name=name,
        kind="boolean",
        required=required,
        label_key=label_key,
    )


def _lund_mackay_fields() -> tuple[CalculatorInputField, ...]:
    fields: list[CalculatorInputField] = []
    for side in ("right", "left"):
        for item in LM_SINUS_ITEMS:
            fields.append(
                _int_field(
                    f"{side}_{item}",
                    label_key=f"calculators.fields.endoscopy.lundMackay.{item}.{side}",
                    minimum=0,
                    maximum=2,
                )
            )
        fields.append(
            _int_field(
                f"{side}_ostiomeatal_complex",
                label_key=f"calculators.fields.endoscopy.lundMackay.omc.{side}",
                minimum=0,
                maximum=2,
            )
        )
    return tuple(fields)


def _select_field(
    name: str,
    *,
    label_key: str,
    options: tuple[CalculatorInputOption, ...],
    required: bool = True,
) -> CalculatorInputField:
    return CalculatorInputField(
        name=name,
        kind="select",
        required=required,
        label_key=label_key,
        options=options,
    )


def _ear_select() -> CalculatorInputField:
    return _select_field(
        "ear",
        label_key="calculators.fields.shared.ear",
        options=(
            CalculatorInputOption("right", "calculators.fields.shared.earRight"),
            CalculatorInputOption("left", "calculators.fields.shared.earLeft"),
        ),
    )


def _pta_formula_select() -> CalculatorInputField:
    return _select_field(
        "pta_formula",
        label_key="calculators.fields.audiology.ptaFormula",
        options=(
            CalculatorInputOption("3freq", "calculators.fields.audiology.formula3freq"),
            CalculatorInputOption(
                "4freq_who", "calculators.fields.audiology.formula4freqWho"
            ),
            CalculatorInputOption(
                "high_freq", "calculators.fields.audiology.formulaHighFreq"
            ),
            CalculatorInputOption(
                "fletcher", "calculators.fields.audiology.formulaFletcher"
            ),
        ),
    )


def _ordinal_side_fields(
    items: tuple[str, ...],
    *,
    max_grade: int,
    label_prefix: str,
) -> tuple[CalculatorInputField, ...]:
    fields: list[CalculatorInputField] = []
    for side in ("right", "left"):
        for item in items:
            fields.append(
                _int_field(
                    f"{side}_{item}",
                    label_key=f"{label_prefix}.{item}.{side}",
                    minimum=0,
                    maximum=max_grade,
                )
            )
    return tuple(fields)


def _air_fields(
    frequencies_hz: tuple[int, ...],
    *,
    ears: tuple[str, ...] = ("right", "left"),
    required: bool = False,
    prefix: str = "",
) -> tuple[CalculatorInputField, ...]:
    fields: list[CalculatorInputField] = []
    for ear in ears:
        for hz in frequencies_hz:
            fields.append(
                _int_field(
                    f"{prefix}air_{ear}_{hz}",
                    label_key=f"calculators.fields.audiology.air_{ear}_{hz}",
                    minimum=-10,
                    maximum=120,
                    required=required,
                    unit="dB HL",
                )
            )
    return tuple(fields)


def _bone_fields(
    frequencies_hz: tuple[int, ...],
    *,
    prefix: str = "",
) -> tuple[CalculatorInputField, ...]:
    fields: list[CalculatorInputField] = []
    for ear in ("right", "left"):
        for hz in frequencies_hz:
            fields.append(
                _int_field(
                    f"{prefix}bone_{ear}_{hz}",
                    label_key=f"calculators.fields.audiology.bone_{ear}_{hz}",
                    minimum=-10,
                    maximum=120,
                    required=False,
                    unit="dB HL",
                )
            )
    return tuple(fields)


def _lk_side_maps(
    raw: Mapping[str, Any], items: tuple[str, ...]
) -> tuple[dict[str, int], dict[str, int]]:
    right = {
        item: require_int(raw, f"right_{item}", minimum=0, maximum=2) for item in items
    }
    left = {
        item: require_int(raw, f"left_{item}", minimum=0, maximum=2) for item in items
    }
    return right, left


def _run_lk(raw: Mapping[str, Any]) -> CalculationResult:
    right, left = _lk_side_maps(raw, LK_ITEMS)
    return lk_score(right=right, left=left)


def _run_modified_lk(raw: Mapping[str, Any]) -> CalculationResult:
    right, left = _lk_side_maps(raw, MODIFIED_LK_ITEMS)
    return modified_lk_score(right=right, left=left)


def _run_polyp(raw: Mapping[str, Any]) -> CalculationResult:
    scale = require_str(raw, "scale")
    maximum = 3 if scale == "lildholdt" else 4
    right = require_int(raw, "right", minimum=0, maximum=maximum)
    left = require_int(raw, "left", minimum=0, maximum=maximum)
    return polyp_score(scale=scale, right=right, left=left)


def _run_adenoid(raw: Mapping[str, Any]) -> CalculationResult:
    percent = require_int(raw, "percent", minimum=0, maximum=100)
    return adenoid_score(percent=percent)


def _run_rfs(raw: Mapping[str, Any]) -> CalculationResult:
    items = {item: require_int(raw, item, minimum=0, maximum=4) for item in RFS_ITEMS}
    for item, allowed in RFS_ALLOWED.items():
        if items[item] not in allowed:
            raise CalculatorInputError("calculator.out_of_range", field=item)
    return rfs_score(items=items)


def _run_grbas(raw: Mapping[str, Any]) -> CalculationResult:
    items = {item: require_int(raw, item, minimum=0, maximum=3) for item in GRBAS_ITEMS}
    return grbas_score(items=items)


def _run_pas(raw: Mapping[str, Any]) -> CalculationResult:
    level = require_int(raw, "level", minimum=1, maximum=8)
    return pas_score(level=level)


def _ear_thresholds(
    raw: Mapping[str, Any],
    ear: str,
    frequencies: tuple[int, ...],
    *,
    prefix: str = "",
) -> list[ThresholdPoint]:
    return collect_thresholds(
        raw,
        frequencies_hz=frequencies,
        ears=(ear,),  # type: ignore[arg-type]
        conductions=("air",),
        prefix=prefix,
    )


def _run_pta(raw: Mapping[str, Any]) -> CalculationResult:
    from ent.engines.audiology.types import PTA_HIGH_FREQUENCIES_HZ

    ear = require_str(raw, "ear")
    formula = require_str(raw, "pta_formula")
    if formula not in ("3freq", "4freq_who", "high_freq", "fletcher"):
        raise CalculatorInputError("calculator.invalid_select", field="pta_formula")
    thresholds = collect_thresholds(
        raw,
        frequencies_hz=(250, 500, 1000, 2000, 4000, 6000, 8000),
        ears=(ear,),  # type: ignore[arg-type]
        conductions=("air",),
    )
    if not thresholds:
        if formula == "4freq_who":
            freqs: tuple[int, ...] = WHO_GRADE_FREQUENCIES_HZ
        elif formula == "high_freq":
            freqs = PTA_HIGH_FREQUENCIES_HZ
        else:
            freqs = PTA_3_FREQUENCIES_HZ
        thresholds = _ear_thresholds(raw, ear, freqs)
    return pta_score(
        thresholds=thresholds,
        ear=ear,
        formula=formula,  # type: ignore[arg-type]
    )


def _run_abg(raw: Mapping[str, Any]) -> CalculationResult:
    ear = require_str(raw, "ear")
    thresholds = collect_thresholds(
        raw,
        frequencies_hz=ABG_FREQUENCIES_HZ,
        ears=(ear,),  # type: ignore[arg-type]
    )
    return abg_score(thresholds=thresholds, ear=ear)


def _run_who(raw: Mapping[str, Any]) -> CalculationResult:
    ear = require_str(raw, "ear")
    thresholds = _ear_thresholds(raw, ear, WHO_GRADE_FREQUENCIES_HZ)
    return who_score(thresholds=thresholds, ear=ear)


def _run_loss_type(raw: Mapping[str, Any]) -> CalculationResult:
    ear = require_str(raw, "ear")
    thresholds = collect_thresholds(
        raw,
        frequencies_hz=ABG_FREQUENCIES_HZ,
        ears=(ear,),  # type: ignore[arg-type]
    )
    return loss_type_score(thresholds=thresholds, ear=ear)


def _run_configuration(raw: Mapping[str, Any]) -> CalculationResult:
    ear = require_str(raw, "ear")
    thresholds = _ear_thresholds(raw, ear, AIR_CONFIG_FREQUENCIES_HZ)
    return configuration_score(thresholds=thresholds, ear=ear)


def _run_interaural(raw: Mapping[str, Any]) -> CalculationResult:
    formula = require_str(raw, "pta_formula")
    thresholds = collect_thresholds(
        raw,
        frequencies_hz=WHO_GRADE_FREQUENCIES_HZ,
        conductions=("air",),
    )
    return interaural_score(thresholds=thresholds, pta_formula=formula)  # type: ignore[arg-type]


def _run_impairment(raw: Mapping[str, Any]) -> CalculationResult:
    thresholds = collect_thresholds(
        raw, frequencies_hz=IMPAIRMENT_FREQUENCIES_HZ, conductions=("air",)
    )
    return impairment_score(thresholds=thresholds)


def _run_asymmetry(raw: Mapping[str, Any]) -> CalculationResult:
    thresholds = collect_thresholds(
        raw,
        frequencies_hz=AIR_CONFIG_FREQUENCIES_HZ,
        conductions=("air",),
    )
    rule = AsymmetryRule(
        adjacent_db=require_int(raw, "adjacent_db", minimum=1, maximum=60),
        adjacent_count=require_int(raw, "adjacent_count", minimum=1, maximum=6),
        single_db=require_int(raw, "single_db", minimum=1, maximum=60),
        wrs_percent=require_int(raw, "wrs_percent", minimum=1, maximum=100),
    )
    return asymmetry_score(
        thresholds=thresholds,
        rule=rule,
        speech_right=optional_int(raw, "speech_right", minimum=0, maximum=100),
        speech_left=optional_int(raw, "speech_left", minimum=0, maximum=100),
    )


def _run_shift(raw: Mapping[str, Any]) -> CalculationResult:
    rule = require_str(raw, "rule")
    current = collect_thresholds(
        raw,
        frequencies_hz=AIR_CONFIG_FREQUENCIES_HZ,
        conductions=("air",),
        prefix="current_",
    )
    baseline = collect_thresholds(
        raw,
        frequencies_hz=AIR_CONFIG_FREQUENCIES_HZ,
        conductions=("air",),
        prefix="baseline_",
    )
    return shift_score(current=current, baseline=baseline, rule=rule)  # type: ignore[arg-type]


def _run_speech(raw: Mapping[str, Any]) -> CalculationResult:
    ear = require_str(raw, "ear")
    formula = require_str(raw, "pta_formula")
    thresholds = _ear_thresholds(raw, ear, WHO_GRADE_FREQUENCIES_HZ)
    srt = optional_int(raw, "srt_db", minimum=-10, maximum=120)
    return speech_score(
        thresholds=thresholds,
        ear=ear,
        srt_db=srt,
        pta_formula=formula,  # type: ignore[arg-type]
    )


def _run_tymp(raw: Mapping[str, Any]) -> CalculationResult:
    data = TympanogramInput(
        ecv_ml=optional_decimal(raw, "ecv_ml"),
        peak_pressure_dapa=optional_int(
            raw, "peak_pressure_dapa", minimum=-800, maximum=200
        ),
        compliance_ml=optional_decimal(raw, "compliance_ml"),
        gradient_dapa=optional_int(raw, "gradient_dapa", minimum=0, maximum=1000),
    )
    return tymp_score(data)


def _run_abr(raw: Mapping[str, Any]) -> CalculationResult:
    waves = AbrWaveInput(
        wave_i_ms=optional_decimal(raw, "wave_i_ms"),
        wave_iii_ms=optional_decimal(raw, "wave_iii_ms"),
        wave_v_ms=optional_decimal(raw, "wave_v_ms"),
    )
    contralateral = optional_decimal(raw, "contralateral_wave_v_ms")
    threshold = optional_decimal(raw, "threshold_ms") or Decimal("0.30")
    return abr_score(
        waves,
        contralateral_wave_v_ms=contralateral,
        threshold_ms=threshold,
    )


def _run_ehdi(raw: Mapping[str, Any]) -> CalculationResult:
    data = Ehdi136Input(
        birth_date=require_date(raw, "birth_date"),
        as_of_date=require_date(raw, "as_of_date"),
        screen_date=optional_date(raw, "screen_date"),
        screen_refer=require_bool(raw, "screen_refer"),
        rescreen_date=optional_date(raw, "rescreen_date"),
        diagnostic_abr_date=optional_date(raw, "diagnostic_abr_date"),
        permanent_hearing_loss=require_bool(raw, "permanent_hearing_loss"),
        intervention_date=optional_date(raw, "intervention_date"),
    )
    return ehdi_136_calculation(data)


def _run_candidacy(raw: Mapping[str, Any]) -> CalculationResult:
    data = CandidacyInput(
        pta_right=optional_decimal(raw, "pta_right"),
        pta_left=optional_decimal(raw, "pta_left"),
        wrs_right_percent=optional_int(
            raw, "wrs_right_percent", minimum=0, maximum=100
        ),
        wrs_left_percent=optional_int(raw, "wrs_left_percent", minimum=0, maximum=100),
        loss_type_right=optional_str(raw, "loss_type_right"),
        loss_type_left=optional_str(raw, "loss_type_left"),
        hearing_aid_trial_completed=require_bool(raw, "hearing_aid_trial_completed"),
        imaging_clearance=require_bool(raw, "imaging_clearance"),
        communication_impact_assessed=require_bool(
            raw, "communication_impact_assessed"
        ),
    )
    return device_candidacy_calculation(data)


def _run_pediatric_dose(raw: Mapping[str, Any]) -> CalculationResult:
    rule = DosingRule(
        mg_per_kg_per_day=require_decimal(raw, "mg_per_kg_per_day"),
        doses_per_day=require_int(raw, "doses_per_day", minimum=1, maximum=12),
        max_mg_per_day=optional_decimal(raw, "max_mg_per_day"),
        indication_code=optional_str(raw, "indication_code"),
    )
    data = PediatricDoseInput(
        weight_kg=require_decimal(raw, "weight_kg"),
        rule=rule,
        concentration_mg_per_ml=optional_decimal(raw, "concentration_mg_per_ml"),
        completed_years=optional_int(raw, "completed_years", minimum=0, maximum=18),
    )
    return weight_based_dose(data)


def _run_steroid_taper(raw: Mapping[str, Any]) -> CalculationResult:
    data = TaperInput(
        start_mg=require_decimal(raw, "start_mg"),
        step_mg=require_decimal(raw, "step_mg"),
        days_per_step=require_int(raw, "days_per_step", minimum=1, maximum=30),
        minimum_mg=require_decimal(raw, "minimum_mg"),
    )
    return generate_steroid_taper(data).calculation


def _run_bmi(raw: Mapping[str, Any]) -> CalculationResult:
    return bmi_score(
        weight_kg=require_decimal(raw, "weight_kg"),
        height_cm=require_decimal(raw, "height_cm"),
    )


def _run_bsa(raw: Mapping[str, Any]) -> CalculationResult:
    method = require_str(raw, "method")
    if method not in ("mosteller", "dubois"):
        raise CalculatorInputError("calculator.invalid_select", field="method")
    return bsa_score(
        weight_kg=require_decimal(raw, "weight_kg"),
        height_cm=require_decimal(raw, "height_cm"),
        method=method,  # type: ignore[arg-type]
    )


def _run_corrected_age(raw: Mapping[str, Any]) -> CalculationResult:
    return corrected_age_score(
        birth_date=require_date(raw, "birth_date"),
        as_of_date=require_date(raw, "as_of_date"),
        gestational_age_weeks=require_int(
            raw, "gestational_age_weeks", minimum=22, maximum=42
        ),
        gestational_age_days=(
            optional_int(raw, "gestational_age_days", minimum=0, maximum=6) or 0
        ),
    )


def _run_lund_mackay(raw: Mapping[str, Any]) -> CalculationResult:
    right = {
        item: require_int(raw, f"right_{item}", minimum=0, maximum=2)
        for item in LM_SINUS_ITEMS
    }
    right["ostiomeatal_complex"] = require_int(
        raw, "right_ostiomeatal_complex", minimum=0, maximum=2
    )
    left = {
        item: require_int(raw, f"left_{item}", minimum=0, maximum=2)
        for item in LM_SINUS_ITEMS
    }
    left["ostiomeatal_complex"] = require_int(
        raw, "left_ostiomeatal_complex", minimum=0, maximum=2
    )
    return lund_mackay_score(right=right, left=left)


def _run_myer_cotton(raw: Mapping[str, Any]) -> CalculationResult:
    return myer_cotton_score(
        obstruction_percent=require_int(
            raw, "obstruction_percent", minimum=0, maximum=100
        ),
    )


def _run_ett_size(raw: Mapping[str, Any]) -> CalculationResult:
    cuffed_value = raw.get("cuffed")
    cuffed = (
        True
        if cuffed_value is None or cuffed_value == ""
        else require_bool(raw, "cuffed")
    )
    return ett_score(age_years=require_decimal(raw, "age_years"), cuffed=cuffed)


def _run_paradise(raw: Mapping[str, Any]) -> CalculationResult:
    data = ParadiseInput(
        episodes_last_year=require_int(
            raw, "episodes_last_year", minimum=0, maximum=30
        ),
        episodes_year_2=require_int(raw, "episodes_year_2", minimum=0, maximum=30),
        episodes_year_3=require_int(raw, "episodes_year_3", minimum=0, maximum=30),
        fever_38_3c=require_bool(raw, "fever_38_3c"),
        cervical_adenopathy=require_bool(raw, "cervical_adenopathy"),
        tonsillar_exudate=require_bool(raw, "tonsillar_exudate"),
        positive_strep_a=require_bool(raw, "positive_strep_a"),
        episodes_documented=require_bool(raw, "episodes_documented"),
    )
    return paradise_checklist(data)


def _run_tube_criteria(raw: Mapping[str, Any]) -> CalculationResult:
    data = TubeCriteriaInput(
        aom_episodes_6_months=require_int(
            raw, "aom_episodes_6_months", minimum=0, maximum=24
        ),
        aom_episodes_12_months=require_int(
            raw, "aom_episodes_12_months", minimum=0, maximum=36
        ),
        middle_ear_effusion_present=require_bool(raw, "middle_ear_effusion_present"),
        ome_duration_months=require_int(
            raw, "ome_duration_months", minimum=0, maximum=60
        ),
        bilateral_ome=require_bool(raw, "bilateral_ome"),
        hearing_difficulty_documented=require_bool(
            raw, "hearing_difficulty_documented"
        ),
        at_risk_or_symptomatic_ome=require_bool(raw, "at_risk_or_symptomatic_ome"),
    )
    return tube_criteria_checklist(data)


def _run_adenotonsillectomy(raw: Mapping[str, Any]) -> CalculationResult:
    data = AdenotonsillectomyInput(
        sdb_symptoms_present=require_bool(raw, "sdb_symptoms_present"),
        tonsil_brodsky_grade=require_int(
            raw, "tonsil_brodsky_grade", minimum=0, maximum=4
        ),
        adenoid_hypertrophy=require_bool(raw, "adenoid_hypertrophy"),
        psg_performed=require_bool(raw, "psg_performed"),
        psg_ahi=optional_decimal(raw, "psg_ahi"),
        age_under_3_years=require_bool(raw, "age_under_3_years"),
        high_risk_comorbidity=require_bool(raw, "high_risk_comorbidity"),
    )
    return adenotonsillectomy_checklist(data)


def _spec(
    *,
    code: str,
    version: str,
    reference: str,
    unit: str | None,
    formula: str,
    inputs: tuple[CalculatorInputField, ...],
    interactive: bool,
    runner: Runner | None,
) -> tuple[CalculatorSpec, Runner | None]:
    spec = CalculatorSpec(
        code=code,
        version=version,
        reference=reference,
        unit=unit,
        formula=formula,
        domain=domain_from_code(code),
        inputs=inputs,
        interactive=interactive,
    )
    return spec, runner


def _catalog_entries() -> list[tuple[CalculatorSpec, Runner | None]]:
    polyp_scale = _select_field(
        "scale",
        label_key="calculators.fields.endoscopy.polypScale",
        options=(
            CalculatorInputOption(
                "meltzer", "calculators.fields.endoscopy.scaleMeltzer"
            ),
            CalculatorInputOption(
                "lildholdt", "calculators.fields.endoscopy.scaleLildholdt"
            ),
        ),
    )
    rfs_fields = tuple(
        _int_field(
            item,
            label_key=f"calculators.fields.laryngoscopy.rfs.{item}",
            minimum=min(RFS_ALLOWED[item]),
            maximum=max(RFS_ALLOWED[item]),
        )
        for item in RFS_ITEMS
    )
    grbas_fields = tuple(
        _int_field(
            item,
            label_key=f"calculators.fields.laryngoscopy.grbas.{item}",
            minimum=0,
            maximum=3,
        )
        for item in GRBAS_ITEMS
    )
    shift_rule = _select_field(
        "rule",
        label_key="calculators.fields.audiology.shiftRule",
        options=(
            CalculatorInputOption("asha", "calculators.fields.audiology.ruleAsha"),
            CalculatorInputOption(
                "occupational", "calculators.fields.audiology.ruleOccupational"
            ),
        ),
    )
    entries: list[tuple[CalculatorSpec, Runner | None]] = [
        _spec(
            code=PEDIATRIC_CODE,
            version=PEDIATRIC_VERSION,
            reference=PEDIATRIC_REFERENCE,
            unit="mg",
            formula=PEDIATRIC_FORMULA,
            inputs=(
                _decimal_field(
                    "weight_kg",
                    label_key="calculators.fields.prescriptions.weightKg",
                    minimum="0.1",
                    maximum="500",
                    unit="kg",
                ),
                _decimal_field(
                    "mg_per_kg_per_day",
                    label_key="calculators.fields.prescriptions.mgPerKgPerDay",
                    minimum="0.01",
                    maximum="500",
                    unit="mg/kg/day",
                ),
                _int_field(
                    "doses_per_day",
                    label_key="calculators.fields.prescriptions.dosesPerDay",
                    minimum=1,
                    maximum=12,
                ),
                _decimal_field(
                    "max_mg_per_day",
                    label_key="calculators.fields.prescriptions.maxMgPerDay",
                    minimum="0",
                    maximum="20000",
                    required=False,
                    unit="mg",
                ),
                _decimal_field(
                    "concentration_mg_per_ml",
                    label_key="calculators.fields.prescriptions.concentrationMgPerMl",
                    minimum="0.01",
                    maximum="500",
                    required=False,
                    unit="mg/mL",
                ),
                _int_field(
                    "completed_years",
                    label_key="calculators.fields.prescriptions.completedYears",
                    minimum=0,
                    maximum=18,
                    required=False,
                ),
            ),
            interactive=True,
            runner=_run_pediatric_dose,
        ),
        _spec(
            code=TAPER_CODE,
            version=TAPER_VERSION,
            reference=TAPER_REFERENCE,
            unit="day",
            formula=TAPER_FORMULA,
            inputs=(
                _decimal_field(
                    "start_mg",
                    label_key="calculators.fields.prescriptions.taperStartMg",
                    minimum="0.1",
                    maximum="200",
                    unit="mg",
                ),
                _decimal_field(
                    "step_mg",
                    label_key="calculators.fields.prescriptions.taperStepMg",
                    minimum="0.1",
                    maximum="200",
                    unit="mg",
                ),
                _int_field(
                    "days_per_step",
                    label_key="calculators.fields.prescriptions.taperDaysPerStep",
                    minimum=1,
                    maximum=30,
                ),
                _decimal_field(
                    "minimum_mg",
                    label_key="calculators.fields.prescriptions.taperMinimumMg",
                    minimum="0",
                    maximum="200",
                    unit="mg",
                ),
            ),
            interactive=True,
            runner=_run_steroid_taper,
        ),
        _spec(
            code=LK_CODE,
            version=LK_VERSION,
            reference=LK_REFERENCE,
            unit="points",
            formula=LK_FORMULA,
            inputs=_ordinal_side_fields(
                LK_ITEMS, max_grade=2, label_prefix="calculators.fields.endoscopy.lk"
            ),
            interactive=True,
            runner=_run_lk,
        ),
        _spec(
            code=MODIFIED_LK_CODE,
            version=MODIFIED_LK_VERSION,
            reference=MODIFIED_LK_REFERENCE,
            unit="points",
            formula=MODIFIED_LK_FORMULA,
            inputs=_ordinal_side_fields(
                MODIFIED_LK_ITEMS,
                max_grade=2,
                label_prefix="calculators.fields.endoscopy.modifiedLk",
            ),
            interactive=True,
            runner=_run_modified_lk,
        ),
        _spec(
            code=POLYP_CODE,
            version=POLYP_VERSION,
            reference=POLYP_REFERENCE,
            unit="grade",
            formula=POLYP_FORMULA,
            inputs=(
                polyp_scale,
                _int_field(
                    "right",
                    label_key="calculators.fields.shared.sideRight",
                    minimum=0,
                    maximum=4,
                ),
                _int_field(
                    "left",
                    label_key="calculators.fields.shared.sideLeft",
                    minimum=0,
                    maximum=4,
                ),
            ),
            interactive=True,
            runner=_run_polyp,
        ),
        _spec(
            code=ADENOID_CODE,
            version=ADENOID_VERSION,
            reference=ADENOID_REFERENCE,
            unit="%",
            formula=ADENOID_FORMULA,
            inputs=(
                _int_field(
                    "percent",
                    label_key="calculators.fields.endoscopy.adenoidPercent",
                    minimum=0,
                    maximum=100,
                    unit="%",
                ),
            ),
            interactive=True,
            runner=_run_adenoid,
        ),
        _spec(
            code=RFS_CODE,
            version=RFS_VERSION,
            reference=RFS_REFERENCE,
            unit="points",
            formula=RFS_FORMULA,
            inputs=rfs_fields,
            interactive=True,
            runner=_run_rfs,
        ),
        _spec(
            code=GRBAS_CODE,
            version=GRBAS_VERSION,
            reference=GRBAS_REFERENCE,
            unit="points",
            formula=GRBAS_FORMULA,
            inputs=grbas_fields,
            interactive=True,
            runner=_run_grbas,
        ),
        _spec(
            code=PAS_CODE,
            version=PAS_VERSION,
            reference=PAS_REFERENCE,
            unit="grade",
            formula=PAS_FORMULA,
            inputs=(
                _int_field(
                    "level",
                    label_key="calculators.fields.laryngoscopy.pasLevel",
                    minimum=1,
                    maximum=8,
                ),
            ),
            interactive=True,
            runner=_run_pas,
        ),
        _spec(
            code=PROTOCOL_RESOLVER_CODE,
            version=PROTOCOL_RESOLVER_VERSION,
            reference=PROTOCOL_RESOLVER_REFERENCE,
            unit="recall",
            formula=PROTOCOL_RESOLVER_FORMULA,
            inputs=(),
            interactive=False,
            runner=None,
        ),
        _spec(
            code=AUDIOGRAM_SVG_CODE,
            version=AUDIOGRAM_SVG_VERSION,
            reference=AUDIOGRAM_SVG_REFERENCE,
            unit=None,
            formula=AUDIOGRAM_SVG_FORMULA,
            inputs=(),
            interactive=False,
            runner=None,
        ),
        _spec(
            code=PTA_CODE,
            version=PTA_VERSION,
            reference=PTA_REFERENCE,
            unit="dB HL",
            formula=PTA_FORMULA,
            inputs=(_ear_select(), _pta_formula_select())
            + _air_fields((500, 1000, 2000, 4000, 8000)),
            interactive=True,
            runner=_run_pta,
        ),
        _spec(
            code=ABG_CODE,
            version=ABG_VERSION,
            reference=ABG_REFERENCE,
            unit="dB",
            formula=ABG_FORMULA,
            inputs=(_ear_select(),)
            + _air_fields(ABG_FREQUENCIES_HZ)
            + _bone_fields(ABG_FREQUENCIES_HZ),
            interactive=True,
            runner=_run_abg,
        ),
        _spec(
            code=WHO_CODE,
            version=WHO_VERSION,
            reference=WHO_REFERENCE,
            unit=None,
            formula=WHO_FORMULA,
            inputs=(_ear_select(),) + _air_fields(WHO_GRADE_FREQUENCIES_HZ),
            interactive=True,
            runner=_run_who,
        ),
        _spec(
            code=LOSS_TYPE_CODE,
            version=LOSS_TYPE_VERSION,
            reference=LOSS_TYPE_REFERENCE,
            unit=None,
            formula=LOSS_TYPE_FORMULA,
            inputs=(_ear_select(),)
            + _air_fields(ABG_FREQUENCIES_HZ)
            + _bone_fields(ABG_FREQUENCIES_HZ),
            interactive=True,
            runner=_run_loss_type,
        ),
        _spec(
            code=CONFIG_CODE,
            version=CONFIG_VERSION,
            reference=CONFIG_REFERENCE,
            unit=None,
            formula=CONFIG_FORMULA,
            inputs=(_ear_select(),) + _air_fields(AIR_CONFIG_FREQUENCIES_HZ),
            interactive=True,
            runner=_run_configuration,
        ),
        _spec(
            code=INTERAURAL_CODE,
            version=INTERAURAL_VERSION,
            reference=INTERAURAL_REFERENCE,
            unit="dB",
            formula=INTERAURAL_FORMULA,
            inputs=(_pta_formula_select(),) + _air_fields(WHO_GRADE_FREQUENCIES_HZ),
            interactive=True,
            runner=_run_interaural,
        ),
        _spec(
            code=IMPAIRMENT_CODE,
            version=IMPAIRMENT_VERSION,
            reference=IMPAIRMENT_REFERENCE,
            unit="%",
            formula=IMPAIRMENT_FORMULA,
            inputs=_air_fields(IMPAIRMENT_FREQUENCIES_HZ),
            interactive=True,
            runner=_run_impairment,
        ),
        _spec(
            code=ASYMMETRY_CODE,
            version=ASYMMETRY_VERSION,
            reference=ASYMMETRY_REFERENCE,
            unit=None,
            formula=ASYMMETRY_FORMULA,
            inputs=(
                _int_field(
                    "adjacent_db",
                    label_key="calculators.fields.audiology.adjacentDb",
                    minimum=1,
                    maximum=60,
                    default_value="15",
                ),
                _int_field(
                    "adjacent_count",
                    label_key="calculators.fields.audiology.adjacentCount",
                    minimum=1,
                    maximum=6,
                    default_value="2",
                ),
                _int_field(
                    "single_db",
                    label_key="calculators.fields.audiology.singleDb",
                    minimum=1,
                    maximum=60,
                    default_value="20",
                ),
                _int_field(
                    "wrs_percent",
                    label_key="calculators.fields.audiology.wrsPercent",
                    minimum=1,
                    maximum=100,
                    default_value="15",
                ),
                _int_field(
                    "speech_right",
                    label_key="calculators.fields.audiology.speechRight",
                    minimum=0,
                    maximum=100,
                    required=False,
                    unit="%",
                ),
                _int_field(
                    "speech_left",
                    label_key="calculators.fields.audiology.speechLeft",
                    minimum=0,
                    maximum=100,
                    required=False,
                    unit="%",
                ),
            )
            + _air_fields(AIR_CONFIG_FREQUENCIES_HZ),
            interactive=True,
            runner=_run_asymmetry,
        ),
        _spec(
            code=SHIFT_CODE,
            version=SHIFT_VERSION,
            reference=SHIFT_REFERENCE,
            unit=None,
            formula=SHIFT_FORMULA,
            inputs=(shift_rule,)
            + _air_fields(AIR_CONFIG_FREQUENCIES_HZ, prefix="current_")
            + _air_fields(AIR_CONFIG_FREQUENCIES_HZ, prefix="baseline_"),
            interactive=True,
            runner=_run_shift,
        ),
        _spec(
            code=SPEECH_CODE,
            version=SPEECH_VERSION,
            reference=SPEECH_REFERENCE,
            unit=None,
            formula=SPEECH_FORMULA,
            inputs=(_ear_select(), _pta_formula_select())
            + (
                _int_field(
                    "srt_db",
                    label_key="calculators.fields.audiology.srtDb",
                    minimum=-10,
                    maximum=120,
                    required=False,
                    unit="dB HL",
                ),
            )
            + _air_fields(WHO_GRADE_FREQUENCIES_HZ),
            interactive=True,
            runner=_run_speech,
        ),
        _spec(
            code=TYMP_CODE,
            version=TYMP_VERSION,
            reference=TYMP_REFERENCE,
            unit=None,
            formula=TYMP_FORMULA,
            inputs=(
                CalculatorInputField(
                    name="compliance_ml",
                    kind="decimal",
                    required=False,
                    label_key="calculators.fields.audiology.complianceMl",
                    unit="mL",
                ),
                CalculatorInputField(
                    name="peak_pressure_dapa",
                    kind="integer",
                    required=False,
                    label_key="calculators.fields.audiology.peakPressureDapa",
                    unit="daPa",
                ),
                CalculatorInputField(
                    name="ecv_ml",
                    kind="decimal",
                    required=False,
                    label_key="calculators.fields.audiology.ecvMl",
                    unit="mL",
                ),
                CalculatorInputField(
                    name="gradient_dapa",
                    kind="integer",
                    required=False,
                    label_key="calculators.fields.audiology.gradientDapa",
                    unit="daPa",
                ),
            ),
            interactive=True,
            runner=_run_tymp,
        ),
        _spec(
            code=ABR_CODE,
            version=ABR_VERSION,
            reference=ABR_REFERENCE,
            unit="ms",
            formula=ABR_FORMULA,
            inputs=(
                CalculatorInputField(
                    name="wave_i_ms",
                    kind="decimal",
                    required=False,
                    label_key="calculators.fields.audiology.waveI",
                    unit="ms",
                ),
                CalculatorInputField(
                    name="wave_iii_ms",
                    kind="decimal",
                    required=False,
                    label_key="calculators.fields.audiology.waveIii",
                    unit="ms",
                ),
                CalculatorInputField(
                    name="wave_v_ms",
                    kind="decimal",
                    required=False,
                    label_key="calculators.fields.audiology.waveV",
                    unit="ms",
                ),
                CalculatorInputField(
                    name="contralateral_wave_v_ms",
                    kind="decimal",
                    required=False,
                    label_key="calculators.fields.audiology.contralateralWaveV",
                    unit="ms",
                ),
                CalculatorInputField(
                    name="threshold_ms",
                    kind="decimal",
                    required=False,
                    label_key="calculators.fields.audiology.abrThreshold",
                    unit="ms",
                    default_value="0.30",
                ),
            ),
            interactive=True,
            runner=_run_abr,
        ),
        _spec(
            code=EHDI_CODE,
            version=EHDI_VERSION,
            reference=EHDI_REFERENCE,
            unit="overdue_benchmark",
            formula=EHDI_FORMULA,
            inputs=(
                CalculatorInputField(
                    name="birth_date",
                    kind="date",
                    required=True,
                    label_key="calculators.fields.audiology.birthDate",
                ),
                CalculatorInputField(
                    name="as_of_date",
                    kind="date",
                    required=True,
                    label_key="calculators.fields.audiology.asOfDate",
                ),
                CalculatorInputField(
                    name="screen_date",
                    kind="date",
                    required=False,
                    label_key="calculators.fields.audiology.screenDate",
                ),
                CalculatorInputField(
                    name="screen_refer",
                    kind="boolean",
                    required=True,
                    label_key="calculators.fields.audiology.screenRefer",
                ),
                CalculatorInputField(
                    name="rescreen_date",
                    kind="date",
                    required=False,
                    label_key="calculators.fields.audiology.rescreenDate",
                ),
                CalculatorInputField(
                    name="diagnostic_abr_date",
                    kind="date",
                    required=False,
                    label_key="calculators.fields.audiology.diagnosticAbrDate",
                ),
                CalculatorInputField(
                    name="permanent_hearing_loss",
                    kind="boolean",
                    required=True,
                    label_key="calculators.fields.audiology.permanentHearingLoss",
                ),
                CalculatorInputField(
                    name="intervention_date",
                    kind="date",
                    required=False,
                    label_key="calculators.fields.audiology.interventionDate",
                ),
            ),
            interactive=True,
            runner=_run_ehdi,
        ),
        _spec(
            code=CANDIDACY_CODE,
            version=CANDIDACY_VERSION,
            reference=CANDIDACY_REFERENCE,
            unit=None,
            formula=CANDIDACY_FORMULA,
            inputs=(
                CalculatorInputField(
                    name="pta_right",
                    kind="decimal",
                    required=False,
                    label_key="calculators.fields.audiology.ptaRight",
                    unit="dB HL",
                ),
                CalculatorInputField(
                    name="pta_left",
                    kind="decimal",
                    required=False,
                    label_key="calculators.fields.audiology.ptaLeft",
                    unit="dB HL",
                ),
                CalculatorInputField(
                    name="wrs_right_percent",
                    kind="integer",
                    required=False,
                    label_key="calculators.fields.audiology.wrsRight",
                    unit="%",
                ),
                CalculatorInputField(
                    name="wrs_left_percent",
                    kind="integer",
                    required=False,
                    label_key="calculators.fields.audiology.wrsLeft",
                    unit="%",
                ),
                CalculatorInputField(
                    name="loss_type_right",
                    kind="select",
                    required=False,
                    label_key="calculators.fields.audiology.lossTypeRight",
                    options=(
                        CalculatorInputOption(
                            "conductive",
                            "calculators.fields.audiology.lossConductive",
                        ),
                        CalculatorInputOption(
                            "sensorineural",
                            "calculators.fields.audiology.lossSensorineural",
                        ),
                        CalculatorInputOption(
                            "mixed", "calculators.fields.audiology.lossMixed"
                        ),
                    ),
                ),
                CalculatorInputField(
                    name="loss_type_left",
                    kind="select",
                    required=False,
                    label_key="calculators.fields.audiology.lossTypeLeft",
                    options=(
                        CalculatorInputOption(
                            "conductive",
                            "calculators.fields.audiology.lossConductive",
                        ),
                        CalculatorInputOption(
                            "sensorineural",
                            "calculators.fields.audiology.lossSensorineural",
                        ),
                        CalculatorInputOption(
                            "mixed", "calculators.fields.audiology.lossMixed"
                        ),
                    ),
                ),
                CalculatorInputField(
                    name="hearing_aid_trial_completed",
                    kind="boolean",
                    required=True,
                    label_key="calculators.fields.audiology.haTrialCompleted",
                ),
                CalculatorInputField(
                    name="imaging_clearance",
                    kind="boolean",
                    required=True,
                    label_key="calculators.fields.audiology.imagingClearance",
                ),
                CalculatorInputField(
                    name="communication_impact_assessed",
                    kind="boolean",
                    required=True,
                    label_key="calculators.fields.audiology.communicationImpact",
                ),
            ),
            interactive=True,
            runner=_run_candidacy,
        ),
        _spec(
            code=BMI_CODE,
            version=BMI_VERSION,
            reference=BMI_REFERENCE,
            unit="kg/m2",
            formula=BMI_FORMULA,
            inputs=(
                _decimal_field(
                    "weight_kg",
                    label_key="calculators.fields.general.weightKg",
                    minimum="0.1",
                    maximum="500",
                    unit="kg",
                ),
                _decimal_field(
                    "height_cm",
                    label_key="calculators.fields.general.heightCm",
                    minimum="30",
                    maximum="250",
                    unit="cm",
                ),
            ),
            interactive=True,
            runner=_run_bmi,
        ),
        _spec(
            code=BSA_CODE,
            version=BSA_VERSION,
            reference=BSA_REFERENCE,
            unit="m2",
            formula=BSA_FORMULA,
            inputs=(
                _decimal_field(
                    "weight_kg",
                    label_key="calculators.fields.general.weightKg",
                    minimum="0.1",
                    maximum="500",
                    unit="kg",
                ),
                _decimal_field(
                    "height_cm",
                    label_key="calculators.fields.general.heightCm",
                    minimum="20",
                    maximum="250",
                    unit="cm",
                ),
                _select_field(
                    "method",
                    label_key="calculators.fields.general.bsaMethod",
                    options=(
                        CalculatorInputOption(
                            "mosteller", "calculators.fields.general.bsaMosteller"
                        ),
                        CalculatorInputOption(
                            "dubois", "calculators.fields.general.bsaDuBois"
                        ),
                    ),
                ),
            ),
            interactive=True,
            runner=_run_bsa,
        ),
        _spec(
            code=CORRECTED_AGE_CODE,
            version=CORRECTED_AGE_VERSION,
            reference=CORRECTED_AGE_REFERENCE,
            unit="weeks",
            formula=CORRECTED_AGE_FORMULA,
            inputs=(
                CalculatorInputField(
                    name="birth_date",
                    kind="date",
                    required=True,
                    label_key="calculators.fields.general.birthDate",
                ),
                CalculatorInputField(
                    name="as_of_date",
                    kind="date",
                    required=True,
                    label_key="calculators.fields.general.asOfDate",
                ),
                _int_field(
                    "gestational_age_weeks",
                    label_key="calculators.fields.general.gestationalWeeks",
                    minimum=22,
                    maximum=42,
                ),
                _int_field(
                    "gestational_age_days",
                    label_key="calculators.fields.general.gestationalDays",
                    minimum=0,
                    maximum=6,
                    required=False,
                    default_value="0",
                ),
            ),
            interactive=True,
            runner=_run_corrected_age,
        ),
        _spec(
            code=LM_CODE,
            version=LM_VERSION,
            reference=LM_REFERENCE,
            unit="points",
            formula=LM_FORMULA,
            inputs=_lund_mackay_fields(),
            interactive=True,
            runner=_run_lund_mackay,
        ),
        _spec(
            code=MYER_COTTON_CODE,
            version=MYER_COTTON_VERSION,
            reference=MYER_COTTON_REFERENCE,
            unit="grade",
            formula=MYER_COTTON_FORMULA,
            inputs=(
                _int_field(
                    "obstruction_percent",
                    label_key="calculators.fields.airway.obstructionPercent",
                    minimum=0,
                    maximum=100,
                    unit="%",
                ),
            ),
            interactive=True,
            runner=_run_myer_cotton,
        ),
        _spec(
            code=ETT_CODE,
            version=ETT_VERSION,
            reference=ETT_REFERENCE,
            unit="mm",
            formula=ETT_FORMULA,
            inputs=(
                _decimal_field(
                    "age_years",
                    label_key="calculators.fields.airway.ageYears",
                    minimum="1",
                    maximum="16",
                ),
                _bool_field(
                    "cuffed",
                    label_key="calculators.fields.airway.cuffedTube",
                    required=False,
                ),
            ),
            interactive=True,
            runner=_run_ett_size,
        ),
        _spec(
            code=PARADISE_CODE,
            version=PARADISE_VERSION,
            reference=PARADISE_REFERENCE,
            unit=None,
            formula=PARADISE_FORMULA,
            inputs=(
                _int_field(
                    "episodes_last_year",
                    label_key="calculators.fields.surgery.episodesLastYear",
                    minimum=0,
                    maximum=30,
                ),
                _int_field(
                    "episodes_year_2",
                    label_key="calculators.fields.surgery.episodesYear2",
                    minimum=0,
                    maximum=30,
                ),
                _int_field(
                    "episodes_year_3",
                    label_key="calculators.fields.surgery.episodesYear3",
                    minimum=0,
                    maximum=30,
                ),
                _bool_field(
                    "fever_38_3c", label_key="calculators.fields.surgery.fever383"
                ),
                _bool_field(
                    "cervical_adenopathy",
                    label_key="calculators.fields.surgery.cervicalAdenopathy",
                ),
                _bool_field(
                    "tonsillar_exudate",
                    label_key="calculators.fields.surgery.tonsillarExudate",
                ),
                _bool_field(
                    "positive_strep_a",
                    label_key="calculators.fields.surgery.positiveStrepA",
                ),
                _bool_field(
                    "episodes_documented",
                    label_key="calculators.fields.surgery.episodesDocumented",
                ),
            ),
            interactive=True,
            runner=_run_paradise,
        ),
        _spec(
            code=TUBE_CODE,
            version=TUBE_VERSION,
            reference=TUBE_REFERENCE,
            unit=None,
            formula=TUBE_FORMULA,
            inputs=(
                _int_field(
                    "aom_episodes_6_months",
                    label_key="calculators.fields.surgery.aom6Months",
                    minimum=0,
                    maximum=24,
                ),
                _int_field(
                    "aom_episodes_12_months",
                    label_key="calculators.fields.surgery.aom12Months",
                    minimum=0,
                    maximum=36,
                ),
                _bool_field(
                    "middle_ear_effusion_present",
                    label_key="calculators.fields.surgery.effusionPresent",
                ),
                _int_field(
                    "ome_duration_months",
                    label_key="calculators.fields.surgery.omeDurationMonths",
                    minimum=0,
                    maximum=60,
                ),
                _bool_field(
                    "bilateral_ome", label_key="calculators.fields.surgery.bilateralOme"
                ),
                _bool_field(
                    "hearing_difficulty_documented",
                    label_key="calculators.fields.surgery.hearingDifficulty",
                ),
                _bool_field(
                    "at_risk_or_symptomatic_ome",
                    label_key="calculators.fields.surgery.atRiskOme",
                ),
            ),
            interactive=True,
            runner=_run_tube_criteria,
        ),
        _spec(
            code=ATOSA_CODE,
            version=ATOSA_VERSION,
            reference=ATOSA_REFERENCE,
            unit=None,
            formula=ATOSA_FORMULA,
            inputs=(
                _bool_field(
                    "sdb_symptoms_present",
                    label_key="calculators.fields.surgery.sdbSymptoms",
                ),
                _int_field(
                    "tonsil_brodsky_grade",
                    label_key="calculators.fields.surgery.brodskyGrade",
                    minimum=0,
                    maximum=4,
                ),
                _bool_field(
                    "adenoid_hypertrophy",
                    label_key="calculators.fields.surgery.adenoidHypertrophy",
                ),
                _bool_field(
                    "psg_performed",
                    label_key="calculators.fields.surgery.psgPerformed",
                ),
                _decimal_field(
                    "psg_ahi",
                    label_key="calculators.fields.surgery.psgAhi",
                    minimum="0",
                    maximum="200",
                    required=False,
                ),
                _bool_field(
                    "age_under_3_years",
                    label_key="calculators.fields.surgery.ageUnder3",
                ),
                _bool_field(
                    "high_risk_comorbidity",
                    label_key="calculators.fields.surgery.highRiskComorbidity",
                ),
            ),
            interactive=True,
            runner=_run_adenotonsillectomy,
        ),
        _spec(
            code=SCORING_SUM_CODE,
            version=SCORING_SUM_VERSION,
            reference=SCORING_SUM_REFERENCE,
            unit="points",
            formula=SCORING_SUM_FORMULA,
            inputs=(),
            interactive=False,
            runner=None,
        ),
    ]
    return entries


_CATALOG: dict[str, tuple[CalculatorSpec, Runner | None]] = {
    spec.code: (spec, runner) for spec, runner in _catalog_entries()
}


def registered_calculators() -> tuple[CalculatorSpec, ...]:
    """Metadata for every registered engine (discoverable without new UI code)."""

    return tuple(spec for spec, _ in _CATALOG.values())


def get_calculator_spec(code: str) -> CalculatorSpec | None:
    entry = _CATALOG.get(code)
    if entry is None:
        return None
    return entry[0]


def evaluate_calculator(code: str, raw_inputs: Mapping[str, Any]) -> CalculationResult:
    entry = _CATALOG.get(code)
    if entry is None:
        raise CalculatorInputError("calculator.not_found", calculator_code=code)
    spec, runner = entry
    if not spec.interactive or runner is None:
        raise CalculatorInputError("calculator.not_interactive", calculator_code=code)
    try:
        return runner(raw_inputs)
    except CalculatorInputError:
        raise
    except Exception as exc:
        from ent.engines.airway.errors import AirwayInputError
        from ent.engines.audiology.errors import AudiometryInputError
        from ent.engines.endoscopy.errors import ScoreInputError
        from ent.engines.general.errors import GeneralCalculatorInputError
        from ent.engines.laryngoscopy.errors import ScoreInputError as LScoreInputError
        from ent.engines.prescriptions.errors import EngineInputError
        from ent.engines.surgery.errors import SurgeryChecklistInputError

        if isinstance(exc, (ScoreInputError, LScoreInputError)):
            raise CalculatorInputError(
                "calculator.clinical_input", calculator_code=code
            ) from exc
        if isinstance(exc, AudiometryInputError):
            raise CalculatorInputError(
                "calculator.clinical_input", calculator_code=code
            ) from exc
        if isinstance(exc, EngineInputError):
            raise CalculatorInputError(
                "calculator.clinical_input", calculator_code=code
            ) from exc
        if isinstance(
            exc,
            (
                GeneralCalculatorInputError,
                AirwayInputError,
                SurgeryChecklistInputError,
            ),
        ):
            raise CalculatorInputError(
                "calculator.clinical_input", calculator_code=code
            ) from exc
        raise
