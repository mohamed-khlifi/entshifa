"""Load audiology facts frozen into an audiology_report snapshot (P4-07)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.errors.exceptions import NotFoundError, ValidationError
from ent.core.repository.pagination import normalize_pagination
from ent.core.schemas.base import PaginationParams
from ent.core.security.principal import CurrentUser
from ent.engines.audiology.audiogram_svg import render_audiogram_svg_data_uri
from ent.engines.audiology.types import ThresholdPoint
from ent.features.audiology.models import Audiogram, AudiogramThreshold
from ent.features.audiology.repository import AudiogramRepository
from ent.features.audiology.test_records import (
    AbrResult,
    OaeResult,
    SpeechAudiometry,
    Tympanometry,
)
from ent.features.audiology.test_repository import (
    AbrResultRepository,
    OaeResultRepository,
    SpeechAudiometryRepository,
    TympanometryRepository,
)
from ent.features.clinics.models import Clinic
from ent.features.documents.assemble import VisitFacts
from ent.features.documents.context import load_visit_facts
from ent.features.documents.snapshot import clinic_address, person_name
from ent.features.documents.support import utcnow
from ent.features.encounters.models import Encounter
from ent.features.encounters.repository import EncounterRepository
from ent.features.patients.models import Patient
from ent.features.patients.repository import PatientRepository


async def resolve_audiology_encounter(
    session: AsyncSession,
    user: CurrentUser,
    *,
    patient: Patient,
    body_encounter_public_id: str | None,
    audiogram: Audiogram,
) -> tuple[Encounter | None, VisitFacts]:
    """Choose the encounter for header facts, or synthesize minimal visit metadata."""

    clinic_id = user.clinic_id
    encounter_repo = EncounterRepository(session, clinic_id=clinic_id)
    encounter_public_id = body_encounter_public_id
    if encounter_public_id is None and audiogram.encounter is not None:
        encounter_public_id = audiogram.encounter.public_id
    if encounter_public_id is not None:
        encounter = await encounter_repo.get_detail(encounter_public_id)
        if encounter is None or int(encounter.patient_id) != int(patient.id):
            raise NotFoundError()
        clinic = await _clinic(session, clinic_id)
        locale = patient.preferred_locale
        facts = await load_visit_facts(
            session,
            user,
            patient=patient,
            clinic=clinic,
            encounter=encounter,
            locale=locale,
        )
        return encounter, facts
    clinic = await _clinic(session, clinic_id)
    performed_by = audiogram.performed_by
    clinician_name = person_name(performed_by.first_name, performed_by.last_name)
    performed = audiogram.performed_at
    if performed.tzinfo is not None:
        performed = performed.replace(tzinfo=None)
    facts = VisitFacts(
        patient_name=person_name(patient.first_name, patient.last_name),
        mrn=patient.mrn,
        birth_date=patient.birth_date.isoformat(),
        sex=patient.sex,
        clinic_name=clinic.name,
        clinic_phone=clinic.phone or "",
        clinic_address=clinic_address(clinic),
        issued_on=utcnow().date().isoformat(),
        encounter_date=performed.date().isoformat(),
        clinician_name=clinician_name,
        site_name=clinic.name,
        encounter_type="procedure",
        complaints=(),
        history="",
        diagnoses=(),
        assessment="",
        plan="",
        referring_doctor_name=(patient.referring_doctor_name or "").strip(),
        referring_doctor_locale=patient.referring_doctor_locale,
        preferred_locale=patient.preferred_locale,
        clinic_default_locale=clinic.default_locale,
        flag_codes=(),
        allergy_labels=(),
    )
    return None, facts


async def load_audiogram_for_report(
    session: AsyncSession,
    user: CurrentUser,
    *,
    patient: Patient,
    audiogram_public_id: str | None,
    encounter: Encounter | None,
) -> Audiogram:
    repo = AudiogramRepository(session, clinic_id=user.clinic_id)
    if audiogram_public_id:
        row = await repo.get_detail(audiogram_public_id)
        if row is None or int(row.patient_id) != int(patient.id):
            raise NotFoundError()
        return row
    page = await repo.list_audiograms(
        normalize_pagination(PaginationParams(limit=1, offset=0)),
        patient_id=int(patient.id),
        encounter_id=int(encounter.id) if encounter is not None else None,
    )
    if not page.items:
        raise ValidationError(reason="audiogram_not_found")
    return page.items[0]


async def build_audiology_snapshot(
    session: AsyncSession,
    user: CurrentUser,
    *,
    audiogram: Audiogram,
    conclusion: str | None,
    locale: str,
) -> dict[str, Any]:
    patient_id = int(audiogram.patient_id)
    encounter_id = int(audiogram.encounter_id) if audiogram.encounter_id else None
    thresholds = _threshold_points(audiogram.thresholds)
    chart_uri = render_audiogram_svg_data_uri(
        thresholds,
        has_extended_high_frequencies=_has_extended_high(thresholds),
    )
    speech_repo = SpeechAudiometryRepository(session, clinic_id=user.clinic_id)
    tymp_repo = TympanometryRepository(session, clinic_id=user.clinic_id)
    oae_repo = OaeResultRepository(session, clinic_id=user.clinic_id)
    abr_repo = AbrResultRepository(session, clinic_id=user.clinic_id)
    page_size = PaginationParams(limit=40, offset=0)
    speech_rows = (
        await speech_repo.list_for_patient(
            page_size,
            patient_id=patient_id,
            encounter_id=encounter_id,
            audiogram_id=int(audiogram.id),
        )
    ).items
    tymp_rows = (
        await tymp_repo.list_for_patient(
            page_size,
            patient_id=patient_id,
            encounter_id=encounter_id,
        )
    ).items
    oae_rows = (
        await oae_repo.list_for_patient(
            page_size,
            patient_id=patient_id,
            encounter_id=encounter_id,
        )
    ).items
    abr_rows = (
        await abr_repo.list_for_patient(
            page_size,
            patient_id=patient_id,
            encounter_id=encounter_id,
        )
    ).items
    speech_right = _latest_ear(speech_rows, "right")
    speech_left = _latest_ear(speech_rows, "left")
    tymp_right = _latest_ear(tymp_rows, "right")
    tymp_left = _latest_ear(tymp_rows, "left")
    alerts = _alert_codes(
        audiogram,
        speech_right=speech_right,
        speech_left=speech_left,
        tymp_right=tymp_right,
        tymp_left=tymp_left,
        abr_rows=abr_rows,
    )
    conclusion_text = (conclusion or "").strip()
    if not conclusion_text:
        conclusion_text = (audiogram.interpretation_text or "").strip()
    performed = audiogram.performed_at
    if performed.tzinfo is not None:
        performed = performed.replace(tzinfo=None)
    calibration = (
        audiogram.calibration_date.isoformat()
        if isinstance(audiogram.calibration_date, date)
        else ""
    )
    return {
        "audiogram": {
            "performedAt": performed.date().isoformat(),
            "transducer": audiogram.transducer,
            "method": audiogram.method,
            "reliability": audiogram.reliability,
            "equipment": (audiogram.equipment or "").strip(),
            "calibrationDate": calibration,
            "ptaFormula": audiogram.pta_formula or "",
            "chartDataUri": chart_uri,
            "ptaRight": _format_db(audiogram.pta_right),
            "ptaLeft": _format_db(audiogram.pta_left),
            "gradeRight": audiogram.grade_right or "",
            "gradeLeft": audiogram.grade_left or "",
            "lossTypeRight": audiogram.loss_type_right or "",
            "lossTypeLeft": audiogram.loss_type_left or "",
            "configurationRight": audiogram.configuration_right or "",
            "configurationLeft": audiogram.configuration_left or "",
            "abgRight": _format_db(audiogram.abg_right),
            "abgLeft": _format_db(audiogram.abg_left),
            "alerts": alerts,
            "negativeFindings": _negative_findings(audiogram),
            "conclusion": conclusion_text,
        },
        "tympanometry": {
            "rightSummary": _tymp_summary(tymp_right),
            "leftSummary": _tymp_summary(tymp_left),
        },
        "speech": {
            "rightSummary": _speech_summary(speech_right),
            "leftSummary": _speech_summary(speech_left),
        },
        "evoked": {
            "summary": _evoked_summary(oae_rows, abr_rows),
        },
    }


def _threshold_points(rows: list[AudiogramThreshold]) -> list[ThresholdPoint]:
    return [
        ThresholdPoint(
            ear=row.ear,  # type: ignore[arg-type]
            conduction=row.conduction,  # type: ignore[arg-type]
            frequency_hz=int(row.frequency_hz),
            level_db=int(row.level_db) if row.level_db is not None else None,
            is_masked=bool(row.is_masked),
            is_no_response=bool(row.is_no_response),
        )
        for row in rows
    ]


def _has_extended_high(thresholds: list[ThresholdPoint]) -> bool:
    extended = {10000, 12500, 14000, 16000}
    return any(point.frequency_hz in extended for point in thresholds)


def _format_db(value: Decimal | float | None) -> str:
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return format(value.quantize(Decimal("0.1")), "f")
    return f"{value:.1f}"


def _latest_ear(rows: list[Any], ear: str) -> Any:
    for row in rows:
        if getattr(row, "ear", None) == ear:
            return row
    return None


def _alert_codes(
    audiogram: Audiogram,
    *,
    speech_right: SpeechAudiometry | None,
    speech_left: SpeechAudiometry | None,
    tymp_right: Tympanometry | None,
    tymp_left: Tympanometry | None,
    abr_rows: list[AbrResult],
) -> list[str]:
    codes: list[str] = []
    if audiogram.asymmetry_flag:
        codes.append("asymmetry")
    if audiogram.shift_flag:
        codes.append("shift")
    if speech_right and speech_right.speech_pta_discrepancy_flag:
        codes.append("speech_discrepancy")
    elif speech_left and speech_left.speech_pta_discrepancy_flag:
        codes.append("speech_discrepancy")
    if tymp_right and tymp_right.large_canal_volume_flag:
        codes.append("large_canal")
    elif tymp_left and tymp_left.large_canal_volume_flag:
        codes.append("large_canal")
    if any(row.interaural_v_flag for row in abr_rows):
        codes.append("abr_wave_v")
    return codes


def _negative_findings(audiogram: Audiogram) -> list[str]:
    negatives: list[str] = []
    for ear, grade in (
        ("right", audiogram.grade_right),
        ("left", audiogram.grade_left),
    ):
        if grade in (None, "", "normal"):
            negatives.append(f"{ear}_hearing_normal")
    return negatives


def _tymp_summary(row: Tympanometry | None) -> str:
    if row is None:
        return ""
    jerger = row.jerger_type or row.suggested_jerger_type or ""
    parts: list[str] = []
    if jerger:
        parts.append(f"Jerger {jerger}")
    if row.ecv_ml is not None:
        parts.append(f"ECV {row.ecv_ml} mL")
    if row.peak_pressure_dapa is not None:
        parts.append(f"Peak {row.peak_pressure_dapa} daPa")
    if row.compliance_ml is not None:
        parts.append(f"Compliance {row.compliance_ml} mL")
    if row.etf_result:
        parts.append(f"ETF {row.etf_result}")
    return " · ".join(parts)


def _speech_summary(row: SpeechAudiometry | None) -> str:
    if row is None:
        return ""
    parts: list[str] = []
    if row.srt_db is not None:
        parts.append(f"SRT {row.srt_db} dB HL")
    if row.wrs_percent is not None:
        level = f" at {row.wrs_level_db} dB HL" if row.wrs_level_db is not None else ""
        parts.append(f"WRS {row.wrs_percent}%{level}")
    if row.mcl_db is not None:
        parts.append(f"MCL {row.mcl_db} dB HL")
    if row.ucl_db is not None:
        parts.append(f"UCL {row.ucl_db} dB HL")
    if row.sin_test:
        extra: list[str] = [row.sin_test]
        if row.sin_snr_db is not None:
            extra.append(f"SNR {row.sin_snr_db} dB")
        if row.sin_score_percent is not None:
            extra.append(f"score {row.sin_score_percent}%")
        parts.append("SIN " + " ".join(extra))
    return " · ".join(parts)


def _evoked_summary(oae_rows: list[OaeResult], abr_rows: list[AbrResult]) -> str:
    parts: list[str] = []
    for ear in ("right", "left"):
        oae = _latest_ear(oae_rows, ear)
        if oae is not None:
            parts.append(
                f"OAE {ear}: {oae.oae_type} {oae.overall_result}"
                + (f" ({oae.screening_stage})" if oae.screening_stage else ""),
            )
    for row in abr_rows[:4]:
        wave_v = f", wave V {row.wave_v_ms} ms" if row.wave_v_ms is not None else ""
        thresh = (
            f"threshold {row.threshold_db} dB"
            if row.threshold_db is not None
            else "threshold not set"
        )
        parts.append(f"ABR {row.ear}: {row.stimulus} {thresh}{wave_v}")
    return " · ".join(parts)


async def load_patient_for_report(
    session: AsyncSession,
    user: CurrentUser,
    public_id: str,
) -> Patient:
    from ent.features.patients.policies import created_by_scope

    patient = await PatientRepository(session, clinic_id=user.clinic_id).get_visible(
        public_id,
        created_by_id=created_by_scope(user),
    )
    if patient is None:
        raise NotFoundError()
    return patient


async def _clinic(session: AsyncSession, clinic_id: int) -> Clinic:
    from ent.features.clinics.repository import ClinicRepository

    clinic = await ClinicRepository(session).get(clinic_id)
    if clinic is None:
        raise NotFoundError()
    return clinic
