"""Evaluate every interactive calculator with minimal valid fixtures."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from ent.engines.audiology.types import (
    ABG_FREQUENCIES_HZ,
    AIR_CONFIG_FREQUENCIES_HZ,
)
from ent.engines.calculator_catalog import (
    evaluate_calculator,
    get_calculator_spec,
    registered_calculators,
)
from ent.engines.endoscopy.lund_kennedy import CODE as LK_CODE
from ent.engines.endoscopy.lund_kennedy import ITEMS as LK_ITEMS
from ent.engines.endoscopy.lund_mackay import SINUS_ITEMS as LM_SINUS_ITEMS
from ent.engines.endoscopy.modified_lund_kennedy import ITEMS as MLK_ITEMS
from ent.engines.laryngoscopy.grbas import ITEMS as GRBAS_ITEMS
from ent.engines.laryngoscopy.reflux_finding_score import ITEMS as RFS_ITEMS


def _audiometry_base() -> dict[str, str]:
    raw: dict[str, str] = {
        "ear": "right",
        "pta_formula": "3freq",
        "rule": "asha",
        "adjacent_db": "15",
        "adjacent_count": "2",
        "single_db": "20",
        "wrs_percent": "50",
        "srt_db": "30",
    }
    air_freqs = (250, 500, 1000, 2000, 4000, 6000, 8000)
    for ear in ("right", "left"):
        for hz in air_freqs:
            raw[f"air_{ear}_{hz}"] = "25"
    for ear in ("right", "left"):
        for hz in ABG_FREQUENCIES_HZ:
            raw[f"bone_{ear}_{hz}"] = "15"
    for prefix in ("current_", "baseline_"):
        for ear in ("right", "left"):
            for hz in AIR_CONFIG_FREQUENCIES_HZ:
                base = "22" if prefix == "baseline_" else "30"
                raw[f"{prefix}air_{ear}_{hz}"] = base
    return raw


def _fixtures() -> dict[str, dict[str, object]]:
    today = date(2024, 6, 1)
    audio = _audiometry_base()
    lk = {f"right_{item}": 0 for item in LK_ITEMS} | {
        f"left_{item}": 0 for item in LK_ITEMS
    }
    mlk = {f"right_{item}": 0 for item in MLK_ITEMS} | {
        f"left_{item}": 0 for item in MLK_ITEMS
    }
    rfs = {item: 0 for item in RFS_ITEMS}
    grbas = {item: 1 for item in GRBAS_ITEMS}
    lm = {}
    for side in ("right", "left"):
        for item in LM_SINUS_ITEMS:
            lm[f"{side}_{item}"] = 0
        lm[f"{side}_ostiomeatal_complex"] = 0
    return {
        LK_CODE: lk,
        "endoscopy.modified_lund_kennedy": mlk,
        "endoscopy.polyp_grade": {"scale": "meltzer", "right": 1, "left": 2},
        "endoscopy.adenoid_obstruction": {"percent": 40},
        "laryngoscopy.reflux_finding_score": rfs,
        "laryngoscopy.grbas": grbas,
        "laryngoscopy.penetration_aspiration": {"level": 3},
        "audiology.pta": audio,
        "audiology.air_bone_gap": audio,
        "audiology.who_grade": audio,
        "audiology.loss_type": audio,
        "audiology.configuration": audio,
        "audiology.interaural_difference": audio,
        "audiology.impairment": audio,
        "audiology.asymmetry": audio,
        "audiology.threshold_shift": audio,
        "audiology.speech_pta_agreement": audio,
        "audiology.jerger_tympanogram": {
            "ecv_ml": "1.0",
            "peak_pressure_dapa": "-100",
            "compliance_ml": "0.8",
            "gradient_dapa": "80",
        },
        "audiology.abr_latencies": {
            "wave_i_ms": "1.5",
            "wave_iii_ms": "3.8",
            "wave_v_ms": "5.6",
        },
        "audiology.ehdi_136": {
            "birth_date": (today - timedelta(days=120)).isoformat(),
            "as_of_date": today.isoformat(),
            "screen_date": (today - timedelta(days=90)).isoformat(),
            "screen_refer": "false",
            "rescreen_date": "",
            "diagnostic_abr_date": "",
            "permanent_hearing_loss": "false",
            "intervention_date": "",
        },
        "audiology.device_candidacy": {
            "pta_right": "45",
            "pta_left": "50",
            "hearing_aid_trial_completed": "true",
            "imaging_clearance": "true",
            "communication_impact_assessed": "true",
        },
        "prescriptions.pediatric_dose": {
            "weight_kg": "10",
            "mg_per_kg_per_day": "80",
            "doses_per_day": "2",
        },
        "prescriptions.steroid_taper": {
            "start_mg": "30",
            "step_mg": "5",
            "days_per_step": "2",
            "minimum_mg": "5",
        },
        "general.bmi": {"weight_kg": "70", "height_cm": "170"},
        "general.bsa": {
            "weight_kg": "70",
            "height_cm": "170",
            "method": "mosteller",
        },
        "general.corrected_age": {
            "birth_date": "2024-01-01",
            "as_of_date": "2024-04-01",
            "gestational_age_weeks": "32",
            "gestational_age_days": "0",
        },
        "endoscopy.lund_mackay": lm,
        "airway.myer_cotton": {"obstruction_percent": 40},
        "airway.ett_size": {"age_years": "6"},
        "surgery.paradise_criteria": {
            "episodes_last_year": "3",
            "episodes_year_2": "3",
            "episodes_year_3": "3",
            "fever_38_3c": "false",
            "cervical_adenopathy": "false",
            "tonsillar_exudate": "false",
            "positive_strep_a": "false",
            "episodes_documented": "true",
        },
        "surgery.tube_criteria": {
            "aom_episodes_6_months": "0",
            "aom_episodes_12_months": "0",
            "middle_ear_effusion_present": "false",
            "ome_duration_months": "3",
            "bilateral_ome": "true",
            "hearing_difficulty_documented": "true",
            "at_risk_or_symptomatic_ome": "false",
        },
        "surgery.adenotonsillectomy_osa": {
            "sdb_symptoms_present": "true",
            "tonsil_brodsky_grade": "3",
            "adenoid_hypertrophy": "true",
            "psg_performed": "false",
            "age_under_3_years": "false",
            "high_risk_comorbidity": "false",
        },
    }


@pytest.mark.clinical
@pytest.mark.parametrize(
    "code",
    [spec.code for spec in registered_calculators() if spec.interactive],
)
def test_interactive_calculator_smoke(code: str) -> None:
    assert get_calculator_spec(code) is not None
    raw = _fixtures().get(code, {})
    if not raw:
        spec = get_calculator_spec(code)
        assert spec is not None
        for field in spec.inputs:
            if field.default_value:
                raw[field.name] = field.default_value
            elif field.kind == "select" and field.options:
                raw[field.name] = field.options[0].value
            elif field.kind == "boolean":
                raw[field.name] = False
            elif field.kind == "integer":
                raw[field.name] = field.min_value or 0
            elif field.kind == "decimal":
                raw[field.name] = field.min_value or "0"
    result = evaluate_calculator(code, raw)
    assert result.value
    assert result.version
