"""Seed system encounter templates mapped from feature spec Appendix B."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.utils.ids import new_ulid
from ent.features.encounters.models import EncounterTemplate
from ent.features.terminology.models import Concept


@dataclass(frozen=True, slots=True)
class _TemplateSeedSpec:
    code: str
    name_key: str
    trigger_concept_codes: tuple[str, ...]
    config: dict[str, Any]


SYSTEM_TEMPLATES: tuple[_TemplateSeedSpec, ...] = (
    _TemplateSeedSpec(
        code="TPL.NASAL_OBSTRUCTION",
        name_key="encounters.templates.nasal_obstruction.name",
        trigger_concept_codes=("CC.NASAL_OBSTRUCTION",),
        config={
            "historyFields": [
                {
                    "id": "pattern",
                    "labelKey": "encounters.templates.nasal_obstruction.fields.pattern",
                    "fieldType": "select",
                    "options": ["constant", "alternating"],
                    "required": False,
                },
                {
                    "id": "worse_lying_down",
                    "labelKey": "encounters.templates.nasal_obstruction.fields.worse_lying_down",
                    "fieldType": "boolean",
                    "required": False,
                },
                {
                    "id": "mouth_breathing",
                    "labelKey": "encounters.templates.nasal_obstruction.fields.mouth_breathing",
                    "fieldType": "boolean",
                    "required": False,
                },
                {
                    "id": "hyposmia",
                    "labelKey": "encounters.templates.nasal_obstruction.fields.hyposmia",
                    "fieldType": "boolean",
                    "required": False,
                },
                {
                    "id": "facial_pressure",
                    "labelKey": "encounters.templates.nasal_obstruction.fields.facial_pressure",
                    "fieldType": "boolean",
                    "required": False,
                },
                {
                    "id": "spray_overuse",
                    "labelKey": "encounters.templates.nasal_obstruction.fields.spray_overuse",
                    "fieldType": "boolean",
                    "required": False,
                },
            ],
            "examSections": ["nose", "endoscopy", "oral_cavity"],
            "suggestedInstruments": ["nose", "snot22"],
            "suggestedTests": ["nasal_endoscopy", "ct_sinuses"],
            "suggestedDocuments": ["saline_irrigation_handout"],
            "favoriteDiagnoses": ["J34.2", "J30.9", "J32.9"],
            "defaultFollowUpDays": 42,
        },
    ),
    _TemplateSeedSpec(
        code="TPL.FACIAL_PAIN",
        name_key="encounters.templates.facial_pain.name",
        trigger_concept_codes=("CC.FACIAL_PAIN",),
        config={
            "historyFields": [
                {
                    "id": "sinus_distribution",
                    "labelKey": "encounters.templates.facial_pain.fields.sinus_distribution",
                    "fieldType": "select",
                    "options": [
                        "frontal",
                        "maxillary",
                        "ethmoid",
                        "sphenoid",
                        "diffuse",
                    ],
                    "required": False,
                },
                {
                    "id": "bending_forward_worse",
                    "labelKey": "encounters.templates.facial_pain.fields.bending_forward_worse",
                    "fieldType": "boolean",
                    "required": False,
                },
                {
                    "id": "dental_symptoms",
                    "labelKey": "encounters.templates.facial_pain.fields.dental_symptoms",
                    "fieldType": "boolean",
                    "required": False,
                },
            ],
            "examSections": ["nose", "endoscopy", "face"],
            "suggestedInstruments": ["snot22"],
            "suggestedTests": ["nasal_endoscopy", "ct_sinuses"],
            "suggestedDocuments": ["sinusitis_advice"],
            "favoriteDiagnoses": ["J01.9", "J32.9", "G44.8"],
            "defaultFollowUpDays": 30,
        },
    ),
    _TemplateSeedSpec(
        code="TPL.RHINORRHEA",
        name_key="encounters.templates.rhinorrhea.name",
        trigger_concept_codes=("CC.RHINORRHEA",),
        config={
            "historyFields": [
                {
                    "id": "discharge_character",
                    "labelKey": "encounters.templates.rhinorrhea.fields.discharge_character",
                    "fieldType": "select",
                    "options": ["clear_watery", "mucoid", "purulent", "blood_stained"],
                    "required": False,
                },
                {
                    "id": "seasonality",
                    "labelKey": "encounters.templates.rhinorrhea.fields.seasonality",
                    "fieldType": "select",
                    "options": ["perennial", "spring", "summer", "autumn"],
                    "required": False,
                },
                {
                    "id": "sneezing_paroxysms",
                    "labelKey": "encounters.templates.rhinorrhea.fields.sneezing_paroxysms",
                    "fieldType": "boolean",
                    "required": False,
                },
                {
                    "id": "itchy_eyes_palate",
                    "labelKey": "encounters.templates.rhinorrhea.fields.itchy_eyes_palate",
                    "fieldType": "boolean",
                    "required": False,
                },
            ],
            "examSections": ["nose", "endoscopy"],
            "suggestedInstruments": ["snot22"],
            "suggestedTests": ["prick_test", "specific_ige", "aria_classification"],
            "suggestedDocuments": ["allergen_avoidance_handout"],
            "favoriteDiagnoses": ["J30.1", "J30.2", "J30.8"],
            "defaultFollowUpDays": 60,
        },
    ),
    _TemplateSeedSpec(
        code="TPL.EPISTAXIS",
        name_key="encounters.templates.epistaxis.name",
        trigger_concept_codes=("CC.EPISTAXIS",),
        config={
            "historyFields": [
                {
                    "id": "frequency",
                    "labelKey": "encounters.templates.epistaxis.fields.frequency",
                    "fieldType": "select",
                    "options": ["isolated", "recurrent_weekly", "recurrent_daily"],
                    "required": False,
                },
                {
                    "id": "anticoagulant_use",
                    "labelKey": "encounters.templates.epistaxis.fields.anticoagulant_use",
                    "fieldType": "boolean",
                    "required": False,
                },
                {
                    "id": "hypertension_history",
                    "labelKey": "encounters.templates.epistaxis.fields.hypertension_history",
                    "fieldType": "boolean",
                    "required": False,
                },
            ],
            "examSections": ["nose", "endoscopy", "blood_pressure"],
            "suggestedInstruments": [],
            "suggestedTests": ["cautery_record", "coagulation_panel"],
            "suggestedDocuments": ["nosebleed_first_aid_handout"],
            "favoriteDiagnoses": ["R04.0"],
            "defaultFollowUpDays": 14,
        },
    ),
    _TemplateSeedSpec(
        code="TPL.HEARING_LOSS",
        name_key="encounters.templates.hearing_loss.name",
        trigger_concept_codes=("CC.HEARING_LOSS",),
        config={
            "historyFields": [
                {
                    "id": "onset_profile",
                    "labelKey": "encounters.templates.hearing_loss.fields.onset_profile",
                    "fieldType": "select",
                    "options": ["sudden", "progressive", "fluctuating"],
                    "required": False,
                },
                {
                    "id": "noise_exposure",
                    "labelKey": "encounters.templates.hearing_loss.fields.noise_exposure",
                    "fieldType": "boolean",
                    "required": False,
                },
                {
                    "id": "ototoxic_medications",
                    "labelKey": "encounters.templates.hearing_loss.fields.ototoxic_medications",
                    "fieldType": "boolean",
                    "required": False,
                },
                {
                    "id": "family_history",
                    "labelKey": "encounters.templates.hearing_loss.fields.family_history",
                    "fieldType": "boolean",
                    "required": False,
                },
            ],
            "examSections": ["ear", "tuning_forks"],
            "suggestedInstruments": ["hhie"],
            "suggestedTests": ["audiogram", "tympanogram"],
            "suggestedDocuments": ["hearing_protection_guide"],
            "favoriteDiagnoses": ["H90.3", "H90.0", "H91.9"],
            "defaultFollowUpDays": 90,
        },
    ),
    _TemplateSeedSpec(
        code="TPL.EAR_PAIN",
        name_key="encounters.templates.ear_pain.name",
        trigger_concept_codes=("CC.EAR_PAIN",),
        config={
            "historyFields": [
                {
                    "id": "radiation_to_jaw",
                    "labelKey": "encounters.templates.ear_pain.fields.radiation_to_jaw",
                    "fieldType": "boolean",
                    "required": False,
                },
                {
                    "id": "swimming_exposure",
                    "labelKey": "encounters.templates.ear_pain.fields.swimming_exposure",
                    "fieldType": "boolean",
                    "required": False,
                },
                {
                    "id": "associated_discharge",
                    "labelKey": "encounters.templates.ear_pain.fields.associated_discharge",
                    "fieldType": "boolean",
                    "required": False,
                },
            ],
            "examSections": ["ear", "oral_cavity", "neck"],
            "suggestedInstruments": [],
            "suggestedTests": ["otoscopy", "microscopy", "ear_swab_culture"],
            "suggestedDocuments": ["dry_ear_precautions_handout"],
            "favoriteDiagnoses": ["H60.9", "H66.9", "K07.6"],
            "defaultFollowUpDays": 14,
        },
    ),
    _TemplateSeedSpec(
        code="TPL.TINNITUS",
        name_key="encounters.templates.tinnitus.name",
        trigger_concept_codes=("CC.TINNITUS",),
        config={
            "historyFields": [
                {
                    "id": "pulsatile",
                    "labelKey": "encounters.templates.tinnitus.fields.pulsatile",
                    "fieldType": "boolean",
                    "required": False,
                },
                {
                    "id": "pitch_character",
                    "labelKey": "encounters.templates.tinnitus.fields.pitch_character",
                    "fieldType": "select",
                    "options": ["high_pitched", "low_hum", "clicking", "white_noise"],
                    "required": False,
                },
                {
                    "id": "sleep_interference",
                    "labelKey": "encounters.templates.tinnitus.fields.sleep_interference",
                    "fieldType": "boolean",
                    "required": False,
                },
            ],
            "examSections": ["ear", "neck_auscultation"],
            "suggestedInstruments": ["thi"],
            "suggestedTests": [
                "audiogram",
                "tympanogram",
                "mri_internal_auditory_canal",
            ],
            "suggestedDocuments": ["tinnitus_management_handout"],
            "favoriteDiagnoses": ["H93.1"],
            "defaultFollowUpDays": 90,
        },
    ),
    _TemplateSeedSpec(
        code="TPL.VERTIGO",
        name_key="encounters.templates.vertigo.name",
        trigger_concept_codes=("CC.VERTIGO",),
        config={
            "historyFields": [
                {
                    "id": "timing_and_triggers",
                    "labelKey": "encounters.templates.vertigo.fields.timing_and_triggers",
                    "fieldType": "select",
                    "options": [
                        "positional_seconds",
                        "spontaneous_hours",
                        "continuous_days",
                        "head_motion_induced",
                    ],
                    "required": False,
                },
                {
                    "id": "auditory_symptoms",
                    "labelKey": "encounters.templates.vertigo.fields.auditory_symptoms",
                    "fieldType": "boolean",
                    "required": False,
                },
                {
                    "id": "migraine_history",
                    "labelKey": "encounters.templates.vertigo.fields.migraine_history",
                    "fieldType": "boolean",
                    "required": False,
                },
                {
                    "id": "neurological_red_flags",
                    "labelKey": "encounters.templates.vertigo.fields.neurological_red_flags",
                    "fieldType": "boolean",
                    "required": False,
                },
            ],
            "examSections": ["vestibular_exam", "ear"],
            "suggestedInstruments": ["dhi"],
            "suggestedTests": [
                "audiogram",
                "dix_hallpike_maneuver",
                "vestibular_testing",
            ],
            "suggestedDocuments": ["bppv_home_exercises_handout"],
            "favoriteDiagnoses": ["H81.1", "H81.0", "H81.3"],
            "defaultFollowUpDays": 30,
        },
    ),
    _TemplateSeedSpec(
        code="TPL.SORE_THROAT",
        name_key="encounters.templates.sore_throat.name",
        trigger_concept_codes=("CC.SORE_THROAT",),
        config={
            "historyFields": [
                {
                    "id": "episodes_past_12m",
                    "labelKey": "encounters.templates.sore_throat.fields.episodes_past_12m",
                    "fieldType": "number",
                    "required": False,
                },
                {
                    "id": "antibiotic_courses",
                    "labelKey": "encounters.templates.sore_throat.fields.antibiotic_courses",
                    "fieldType": "number",
                    "required": False,
                },
                {
                    "id": "peritonsillar_abscess_history",
                    "labelKey": "encounters.templates.sore_throat.fields.peritonsillar_abscess_history",
                    "fieldType": "boolean",
                    "required": False,
                },
            ],
            "examSections": ["oral_cavity", "neck"],
            "suggestedInstruments": [],
            "suggestedTests": ["rapid_strep_test", "throat_swab_culture"],
            "suggestedDocuments": ["tonsillitis_care_guide"],
            "favoriteDiagnoses": ["J03.9", "J02.9", "J35.0"],
            "defaultFollowUpDays": 21,
        },
    ),
    _TemplateSeedSpec(
        code="TPL.HOARSENESS",
        name_key="encounters.templates.hoarseness.name",
        trigger_concept_codes=("CC.HOARSENESS",),
        config={
            "historyFields": [
                {
                    "id": "duration_weeks",
                    "labelKey": "encounters.templates.hoarseness.fields.duration_weeks",
                    "fieldType": "number",
                    "required": False,
                },
                {
                    "id": "professional_voice_user",
                    "labelKey": "encounters.templates.hoarseness.fields.professional_voice_user",
                    "fieldType": "boolean",
                    "required": False,
                },
                {
                    "id": "smoking_history",
                    "labelKey": "encounters.templates.hoarseness.fields.smoking_history",
                    "fieldType": "boolean",
                    "required": False,
                },
                {
                    "id": "dysphagia_or_weight_loss",
                    "labelKey": "encounters.templates.hoarseness.fields.dysphagia_or_weight_loss",
                    "fieldType": "boolean",
                    "required": False,
                },
            ],
            "examSections": ["laryngoscopy", "neck"],
            "suggestedInstruments": ["vhi10", "rsi"],
            "suggestedTests": ["flexible_laryngoscopy", "videostroboscopy"],
            "suggestedDocuments": ["vocal_hygiene_handout"],
            "favoriteDiagnoses": ["R49.0", "J38.0", "J38.2"],
            "defaultFollowUpDays": 30,
        },
    ),
)


async def seed_encounter_templates(session: AsyncSession) -> int:
    """Ensure system encounter templates exist with current triggers and configs."""
    created_count = 0

    concepts = (
        (await session.execute(select(Concept).where(Concept.deleted_at.is_(None))))
        .scalars()
        .all()
    )
    concept_id_by_code = {c.code: int(c.id) for c in concepts}

    for spec in SYSTEM_TEMPLATES:
        trigger_ids: list[int] = [
            concept_id_by_code[c]
            for c in spec.trigger_concept_codes
            if c in concept_id_by_code
        ]

        existing = (
            await session.execute(
                select(EncounterTemplate).where(
                    EncounterTemplate.clinic_id.is_(None),
                    EncounterTemplate.user_id.is_(None),
                    EncounterTemplate.code == spec.code,
                    EncounterTemplate.deleted_at.is_(None),
                )
            )
        ).scalar_one_or_none()

        if existing is None:
            template = EncounterTemplate(
                public_id=new_ulid(),
                clinic_id=None,
                user_id=None,
                code=spec.code,
                name_key=spec.name_key,
                trigger_concept_ids=trigger_ids,
                config=spec.config,
                is_active=True,
            )
            session.add(template)
            created_count += 1
        else:
            existing.name_key = spec.name_key
            existing.trigger_concept_ids = trigger_ids
            existing.config = spec.config
            existing.is_active = True

    await session.flush()
    return created_count
