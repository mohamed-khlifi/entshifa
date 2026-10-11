"""Build the frozen placeholder map for a clinical document.

Chart facts are already resolved. This module chooses which payload is legal
for the template and applies the MRI and sick-leave engines.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ent.engines.documents.absence import inclusive_absence_days
from ent.engines.documents.question import clinical_question
from ent.engines.documents.safety import (
    MRI_MODALITIES,
    evaluate_mri_safety,
    mentions_contrast_media,
)
from ent.features.documents.constants import (
    CLINICAL_TEMPLATE_CODES,
    CONSULTATION_REPORT_CODE,
    DOCUMENT_LOCALES,
    IMAGING_REQUEST_CODE,
    LAB_REQUEST_CODE,
    MEDICAL_CERTIFICATE_CODE,
    REFERRAL_LETTER_CODE,
    SICK_LEAVE_CODE,
)
from ent.features.documents.exceptions import (
    DocumentAbsenceRangeError,
    DocumentPayloadError,
    ImagingMriBlockedError,
)
from ent.features.documents.schemas.requests import DocumentCreate


@dataclass(frozen=True, slots=True)
class VisitFacts:
    """Locale-resolved visit values a clinical template may print."""

    patient_name: str
    mrn: str
    birth_date: str
    sex: str
    clinic_name: str
    clinic_phone: str
    clinic_address: str
    issued_on: str
    encounter_date: str
    clinician_name: str
    site_name: str
    encounter_type: str
    complaints: tuple[str, ...]
    history: str
    diagnoses: tuple[str, ...]
    assessment: str
    plan: str
    referring_doctor_name: str
    referring_doctor_locale: str | None
    preferred_locale: str
    clinic_default_locale: str
    flag_codes: tuple[str, ...]
    allergy_labels: tuple[str, ...]


def is_clinical_template(code: str) -> bool:
    return code in CLINICAL_TEMPLATE_CODES


def resolve_document_locale(
    *,
    template_code: str,
    requested: str | None,
    referring_doctor_locale: str | None,
    preferred_locale: str,
    clinic_default_locale: str,
) -> str:
    """Referral letters follow the referring doctor unless a locale is chosen."""

    if requested is not None:
        return requested
    if (
        template_code == REFERRAL_LETTER_CODE
        and referring_doctor_locale in DOCUMENT_LOCALES
    ):
        return str(referring_doctor_locale)
    if preferred_locale in DOCUMENT_LOCALES:
        return preferred_locale
    if clinic_default_locale in DOCUMENT_LOCALES:
        return clinic_default_locale
    return "en"


def build_document_data(
    facts: VisitFacts,
    body: DocumentCreate,
    *,
    clinician_public_id: str,
) -> dict[str, Any]:
    """Return the snapshot data for this template, or raise a domain error."""

    _reject_unexpected_payload(body)
    data = _common(facts)
    code = body.template_code
    if code == CONSULTATION_REPORT_CODE:
        data.update(_visit_lists(facts, conclusion=_conclusion(facts, body)))
        return data
    if code == REFERRAL_LETTER_CODE:
        data.update(_visit_lists(facts, conclusion=facts.assessment))
        recommendations = ""
        if body.referral is not None and body.referral.recommendations:
            recommendations = body.referral.recommendations.strip()
        data["referringDoctor"] = {"name": facts.referring_doctor_name}
        data["referral"] = {"recommendations": recommendations}
        return data
    if code == SICK_LEAVE_CODE:
        if body.sick_leave is None:
            raise DocumentPayloadError()
        leave = body.sick_leave
        try:
            days = inclusive_absence_days(leave.start_date, leave.end_date)
        except ValueError as exc:
            raise DocumentAbsenceRangeError() from exc
        reason = (leave.reason_text or "").strip()
        if leave.reason_mode == "diagnosis" and not reason:
            reason = " · ".join(item for item in facts.diagnoses if item)
        data["absence"] = {
            "absenceType": leave.absence_type,
            "startDate": leave.start_date.isoformat(),
            "endDate": leave.end_date.isoformat(),
            "durationDays": days,
            "reasonMode": leave.reason_mode,
            "reasonText": reason,
        }
        return data
    if code == MEDICAL_CERTIFICATE_CODE:
        if body.certificate is None:
            raise DocumentPayloadError()
        data["certificate"] = {
            "purpose": body.certificate.purpose,
            "body": body.certificate.body_text.strip(),
        }
        return data
    if code == IMAGING_REQUEST_CODE:
        if body.imaging is None:
            raise DocumentPayloadError()
        data["request"] = _imaging_request(
            facts,
            body,
            clinician_public_id=clinician_public_id,
        )
        return data
    if code == LAB_REQUEST_CODE:
        if body.laboratory is None:
            raise DocumentPayloadError()
        data["request"] = {
            "panels": list(body.laboratory.panels),
            "indication": (body.laboratory.indication or "").strip(),
        }
        return data
    raise DocumentPayloadError()


def recheck_imaging(data: dict[str, Any], flag_codes: tuple[str, ...]) -> None:
    """Block finalization if an implant appeared after the draft was saved."""

    request = data.get("request")
    if not isinstance(request, dict):
        raise DocumentPayloadError()
    modality = request.get("modality")
    override = request.get("overrideReason")
    decision = evaluate_mri_safety(
        modality=str(modality or ""),
        flag_codes=flag_codes,
        override_reason=override if isinstance(override, str) else None,
    )
    if decision.blocked:
        raise ImagingMriBlockedError(flags=decision.flags)


def _common(facts: VisitFacts) -> dict[str, Any]:
    return {
        "patient": {
            "fullName": facts.patient_name,
            "mrn": facts.mrn,
            "birthDate": facts.birth_date,
            "sex": facts.sex,
        },
        "clinic": {
            "name": facts.clinic_name,
            "phone": facts.clinic_phone,
            "address": facts.clinic_address,
        },
        "document": {"issuedOn": facts.issued_on},
        "encounter": {
            "date": facts.encounter_date,
            "clinicianName": facts.clinician_name,
            "siteName": facts.site_name,
            "type": facts.encounter_type,
        },
    }


def _visit_lists(facts: VisitFacts, *, conclusion: str) -> dict[str, Any]:
    encounter = {
        "date": facts.encounter_date,
        "clinicianName": facts.clinician_name,
        "siteName": facts.site_name,
        "type": facts.encounter_type,
        "complaints": list(facts.complaints),
        "history": facts.history,
        "diagnoses": list(facts.diagnoses),
        "assessment": conclusion,
        "plan": facts.plan,
    }
    return {"encounter": encounter}


def _conclusion(facts: VisitFacts, body: DocumentCreate) -> str:
    if body.consultation is not None and body.consultation.conclusion:
        text = body.consultation.conclusion.strip()
        if text:
            return text
    return facts.assessment


def _imaging_request(
    facts: VisitFacts,
    body: DocumentCreate,
    *,
    clinician_public_id: str,
) -> dict[str, Any]:
    imaging = body.imaging
    if imaging is None:
        raise DocumentPayloadError()
    decision = evaluate_mri_safety(
        modality=imaging.modality,
        flag_codes=facts.flag_codes,
        override_reason=imaging.override_reason,
    )
    if decision.blocked:
        raise ImagingMriBlockedError(flags=decision.flags)
    if decision.overridden:
        status = "overridden"
        reason = (imaging.override_reason or "").strip()
        clinician = clinician_public_id
    elif imaging.modality in MRI_MODALITIES:
        status = "clear"
        reason = ""
        clinician = ""
    else:
        status = "not_applicable"
        reason = ""
        clinician = ""
    question = clinical_question(
        complaints=facts.complaints,
        diagnoses=facts.diagnoses,
        assessment=facts.assessment,
        supplied=imaging.clinical_question,
    )
    contrast = imaging.contrast_allergy or mentions_contrast_media(facts.allergy_labels)
    flags = set(facts.flag_codes)
    return {
        "modality": imaging.modality,
        "clinicalQuestion": question,
        "pregnancy": _yes("pregnancy" in flags),
        "pacemaker": _yes("pacemaker" in flags),
        "cochlearImplant": _yes("cochlear_implant" in flags),
        "contrastAllergy": _yes(contrast),
        "renalImpairment": _yes(imaging.renal_impairment),
        "mriStatus": status,
        "overrideReason": reason,
        "overrideClinicianPublicId": clinician,
    }


def _yes(value: bool) -> str:
    return "yes" if value else "no"


def _reject_unexpected_payload(body: DocumentCreate) -> None:
    present = {
        name
        for name, value in (
            ("imaging", body.imaging),
            ("laboratory", body.laboratory),
            ("sick_leave", body.sick_leave),
            ("certificate", body.certificate),
            ("referral", body.referral),
            ("consultation", body.consultation),
        )
        if value is not None
    }
    allowed = {
        CONSULTATION_REPORT_CODE: frozenset({"consultation"}),
        REFERRAL_LETTER_CODE: frozenset({"referral"}),
        SICK_LEAVE_CODE: frozenset({"sick_leave"}),
        MEDICAL_CERTIFICATE_CODE: frozenset({"certificate"}),
        IMAGING_REQUEST_CODE: frozenset({"imaging"}),
        LAB_REQUEST_CODE: frozenset({"laboratory"}),
    }[body.template_code]
    if not present <= allowed:
        raise DocumentPayloadError()
