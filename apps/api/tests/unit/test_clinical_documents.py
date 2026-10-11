"""Known-answer tests for visit documents (P2-10)."""

from __future__ import annotations

from datetime import date

import pytest

from ent.engines.documents.absence import VERSION as ABSENCE_VERSION
from ent.engines.documents.absence import inclusive_absence_days
from ent.engines.documents.placeholders import validate_placeholders
from ent.engines.documents.question import clinical_question
from ent.engines.documents.safety import (
    MIN_OVERRIDE_REASON_LENGTH,
    MRI_MODALITIES,
    NON_MRI_SAFE_IMPLANT_FLAGS,
    evaluate_mri_safety,
    mentions_contrast_media,
)
from ent.engines.documents.safety import (
    VERSION as SAFETY_VERSION,
)
from ent.features.documents.assemble import (
    VisitFacts,
    build_document_data,
    resolve_document_locale,
)
from ent.features.documents.clinical_catalog import clinical_template_specs
from ent.features.documents.constants import IMAGING_MODALITIES, LAB_PANELS
from ent.features.documents.exceptions import (
    DocumentAbsenceRangeError,
    DocumentPayloadError,
    ImagingMriBlockedError,
)
from ent.features.documents.html_render import (
    compose_visit_batch,
    render_document_sheet,
)
from ent.features.documents.schemas.requests import (
    DocumentCreate,
    ImagingRequestInput,
    LabRequestInput,
    SickLeaveInput,
)
from ent.features.patients.constants import PATIENT_FLAG_CODES as FLAG_CODES

PATIENT_ID = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
ENCOUNTER_ID = "01ARZ3NDEKTSV4RRFFQ69G5FB0"


def test_engine_versions_are_recorded() -> None:
    assert SAFETY_VERSION == "1.0.0"
    assert ABSENCE_VERSION == "1.0.0"


def test_mri_modalities_match_the_ent_list() -> None:
    assert MRI_MODALITIES <= set(IMAGING_MODALITIES)
    assert MRI_MODALITIES == {
        code for code in IMAGING_MODALITIES if code.startswith("mri_")
    }
    assert NON_MRI_SAFE_IMPLANT_FLAGS <= set(FLAG_CODES)


def test_mri_without_an_implant_is_clear() -> None:
    decision = evaluate_mri_safety(
        modality="mri_iac_gadolinium",
        flag_codes=("pregnancy",),
        override_reason=None,
    )
    assert decision.blocked is False
    assert decision.overridden is False


def test_mri_implant_blocks_until_a_real_override() -> None:
    blocked = evaluate_mri_safety(
        modality="mri_neck",
        flag_codes=("cochlear_implant", "pacemaker"),
        override_reason="short",
    )
    assert blocked.blocked is True
    assert blocked.flags == ("cochlear_implant", "pacemaker")
    assert len("short") < MIN_OVERRIDE_REASON_LENGTH
    allowed = evaluate_mri_safety(
        modality="mri_neck",
        flag_codes=("pacemaker",),
        override_reason="Conditional device, radiology agreed",
    )
    assert allowed.blocked is False
    assert allowed.overridden is True


def test_ct_ignores_an_implant_flag() -> None:
    decision = evaluate_mri_safety(
        modality="ct_sinuses_noncontrast",
        flag_codes=("cochlear_implant",),
        override_reason=None,
    )
    assert decision.blocked is False


def test_contrast_tokens_are_recognized() -> None:
    assert mentions_contrast_media(("Iodinated contrast",)) is True
    assert mentions_contrast_media(("Pénicilline",)) is False


def test_clinical_question_keeps_the_doctor_text() -> None:
    assert (
        clinical_question(
            complaints=("nasal obstruction",),
            diagnoses=("deviated septum",),
            assessment="plan surgery",
            supplied="  Rule out orbital complication  ",
        )
        == "Rule out orbital complication"
    )


def test_clinical_question_joins_recorded_facts_when_blank() -> None:
    assert (
        clinical_question(
            complaints=("nasal obstruction",),
            diagnoses=("deviated septum",),
            assessment="plan surgery",
            supplied="  ",
        )
        == "nasal obstruction · deviated septum · plan surgery"
    )


def test_sick_leave_counts_both_endpoints() -> None:
    assert inclusive_absence_days(date(2026, 10, 1), date(2026, 10, 3)) == 3
    with pytest.raises(ValueError, match="end_before_start"):
        inclusive_absence_days(date(2026, 10, 3), date(2026, 10, 1))


def test_referral_locale_follows_the_referring_doctor() -> None:
    assert (
        resolve_document_locale(
            template_code="referral_letter",
            requested=None,
            referring_doctor_locale="ar",
            preferred_locale="en",
            clinic_default_locale="fr",
        )
        == "ar"
    )
    assert (
        resolve_document_locale(
            template_code="referral_letter",
            requested="fr",
            referring_doctor_locale="ar",
            preferred_locale="en",
            clinic_default_locale="fr",
        )
        == "fr"
    )
    assert (
        resolve_document_locale(
            template_code="consultation_report",
            requested=None,
            referring_doctor_locale="ar",
            preferred_locale="en",
            clinic_default_locale="fr",
        )
        == "en"
    )


def test_every_clinical_template_locale_declares_its_placeholders() -> None:
    specs = clinical_template_specs()
    assert {spec["code"] for spec in specs} == {
        "consultation_report",
        "referral_letter",
        "sick_leave",
        "medical_certificate",
        "imaging_request",
        "lab_request",
    }
    for spec in specs:
        declared = set(spec["placeholders"])
        locales = set()
        for version in spec["versions"]:
            locales.add(version["locale"])
            issue = validate_placeholders(
                (
                    version["header_html"],
                    version["body_html"],
                    version["footer_html"],
                ),
                declared,
            )
            assert issue is None
            if version["locale"] == "ar":
                assert version["direction"] == "rtl"
            else:
                assert version["direction"] == "ltr"
        assert locales == {"en", "fr", "ar"}


def test_imaging_template_names_every_modality_and_panel() -> None:
    specs = {spec["code"]: spec for spec in clinical_template_specs()}
    imaging = specs["imaging_request"]["versions"][0]["body_html"]
    laboratory = specs["lab_request"]["versions"][0]["body_html"]
    for code in IMAGING_MODALITIES:
        assert code in imaging
    for code in LAB_PANELS:
        assert code in laboratory


def test_imaging_request_blocks_and_records_an_override() -> None:
    facts = _facts(flag_codes=("cochlear_implant",))
    body = _create(
        "imaging_request",
        imaging=ImagingRequestInput(modality="mri_iac_gadolinium"),
    )
    with pytest.raises(ImagingMriBlockedError):
        build_document_data(facts, body, clinician_public_id="01CLINICIAN")
    allowed = _create(
        "imaging_request",
        imaging=ImagingRequestInput(
            modality="mri_iac_gadolinium",
            override_reason="Radiology confirmed a conditional implant",
            contrast_allergy=True,
            renal_impairment=True,
        ),
    )
    data = build_document_data(facts, allowed, clinician_public_id="01CLINICIAN")
    request = data["request"]
    assert request["mriStatus"] == "overridden"
    assert request["overrideClinicianPublicId"] == "01CLINICIAN"
    assert request["cochlearImplant"] == "yes"
    assert request["contrastAllergy"] == "yes"
    assert request["renalImpairment"] == "yes"
    assert request["pregnancy"] == "no"


def test_wrong_payload_is_rejected() -> None:
    facts = _facts()
    body = _create(
        "sick_leave",
        imaging=ImagingRequestInput(modality="pet_ct"),
        sick_leave=SickLeaveInput(
            start_date=date(2026, 10, 1),
            end_date=date(2026, 10, 2),
            absence_type="work",
            reason_mode="medical_reasons",
        ),
    )
    with pytest.raises(DocumentPayloadError):
        build_document_data(facts, body, clinician_public_id="01CLINICIAN")


def test_sick_leave_range_and_day_count() -> None:
    facts = _facts()
    body = _create(
        "sick_leave",
        sick_leave=SickLeaveInput(
            start_date=date(2026, 10, 5),
            end_date=date(2026, 10, 1),
            absence_type="school",
            reason_mode="medical_reasons",
        ),
    )
    with pytest.raises(DocumentAbsenceRangeError):
        build_document_data(facts, body, clinician_public_id="01CLINICIAN")
    ok = _create(
        "sick_leave",
        sick_leave=SickLeaveInput(
            start_date=date(2026, 10, 1),
            end_date=date(2026, 10, 1),
            absence_type="school",
            reason_mode="diagnosis",
        ),
    )
    data = build_document_data(
        _facts(diagnoses=("acute otitis media",)), ok, clinician_public_id="c"
    )
    assert data["absence"]["durationDays"] == 1
    assert data["absence"]["reasonText"] == "acute otitis media"


def test_lab_request_keeps_panel_codes() -> None:
    data = build_document_data(
        _facts(),
        _create(
            "lab_request",
            laboratory=LabRequestInput(
                panels=["thyroid_calcitonin", "hpv_status"],
                indication="neck mass",
            ),
        ),
        clinician_public_id="c",
    )
    assert data["request"]["panels"] == ["thyroid_calcitonin", "hpv_status"]
    assert data["request"]["indication"] == "neck mass"


def test_batch_html_keeps_each_document_direction() -> None:
    english = render_document_sheet(
        locale="en",
        direction="ltr",
        header_html="",
        body_html="<p>{{ patient.fullName }}</p>",
        footer_html="",
        css="",
        data={"patient": {"fullName": "Leila"}},
    )
    arabic = render_document_sheet(
        locale="ar",
        direction="rtl",
        header_html="",
        body_html="<p>{{ patient.fullName }}</p>",
        footer_html="",
        css="",
        data={"patient": {"fullName": "ليلى"}},
    )
    html = compose_visit_batch([english, arabic])
    assert 'lang="en"' in html
    assert 'dir="ltr"' in html
    assert 'lang="ar"' in html
    assert 'dir="rtl"' in html
    assert "page-break-after:always" in html
    assert html.index('lang="en"') < html.index('lang="ar"')


def _facts(
    *,
    flag_codes: tuple[str, ...] = (),
    diagnoses: tuple[str, ...] = (),
) -> VisitFacts:
    return VisitFacts(
        patient_name="Leila Ben Salem",
        mrn="MRN-1",
        birth_date="1975-03-12",
        sex="female",
        clinic_name="Clinic",
        clinic_phone="",
        clinic_address="",
        issued_on="2026-10-11",
        encounter_date="2026-10-11",
        clinician_name="Dr Amari",
        site_name="Main",
        encounter_type="consultation",
        complaints=("nasal obstruction",),
        history="",
        diagnoses=diagnoses,
        assessment="",
        plan="",
        referring_doctor_name="Dr Karim",
        referring_doctor_locale="fr",
        preferred_locale="en",
        clinic_default_locale="en",
        flag_codes=flag_codes,
        allergy_labels=(),
    )


def _create(code: str, **payload: object) -> DocumentCreate:
    return DocumentCreate(
        patient_public_id=PATIENT_ID,
        template_code=code,
        encounter_public_id=ENCOUNTER_ID,
        **payload,  # type: ignore[arg-type]
    )
