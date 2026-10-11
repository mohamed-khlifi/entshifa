"""System templates for the six P2-10 clinical documents.

Display strings live in the version rows. Python does not assemble sentences
at render time.
"""

from __future__ import annotations

from typing import Any

from ent.features.documents.clinical_labels import (
    ABSENCE_TYPE_LABELS,
    COMMON_LABELS,
    ENCOUNTER_TYPE_LABELS,
    MODALITY_LABELS,
    PANEL_LABELS,
    PURPOSE_LABELS,
    SECTION_LABELS,
    SEX_LABELS,
)
from ent.features.documents.constants import (
    ABSENCE_TYPES,
    CERTIFICATE_PURPOSES,
    CONSULTATION_REPORT_CODE,
    IMAGING_MODALITIES,
    IMAGING_REQUEST_CODE,
    LAB_PANELS,
    LAB_REQUEST_CODE,
    MEDICAL_CERTIFICATE_CODE,
    REFERRAL_LETTER_CODE,
    SICK_LEAVE_CODE,
)
from ent.features.encounters.constants import ENCOUNTER_TYPES
from ent.features.patients.constants import SEX_VALUES

_CSS = """
body { font-family: "Segoe UI", Tahoma, "Noto Naskh Arabic", "DejaVu Sans", sans-serif;
       font-size: 11pt; }
h1 { font-size: 16pt; margin: 0 0 8pt; }
h2 { font-size: 13pt; margin: 12pt 0 4pt; }
table { width: 100%; border-collapse: collapse; margin: 8pt 0 12pt; }
th, td { border: 1px solid #444; padding: 4pt 6pt; text-align: start; vertical-align: top; }
th { width: 34%; }
td.num, .num { direction: ltr; unicode-bidi: isolate; }
ul { margin: 0; padding-inline-start: 16pt; }
footer { margin-top: 16pt; font-size: 9pt; }
"""

_FOOTER = (
    "<footer><p>{{ clinic.name }}</p>"
    '<p class="num">{{ clinic.phone }}</p>'
    "<p>{{ clinic.address }}</p></footer>"
)

_PATIENT_CLINIC = {
    "patient.fullName": {"type": "string", "required": True},
    "patient.mrn": {"type": "string", "required": True},
    "patient.birthDate": {"type": "date", "required": True},
    "patient.sex": {"type": "code", "required": True},
    "clinic.name": {"type": "string", "required": True},
    "clinic.phone": {"type": "string", "required": False},
    "clinic.address": {"type": "string", "required": False},
    "document.issuedOn": {"type": "date", "required": True},
    "encounter.date": {"type": "date", "required": True},
    "encounter.clinicianName": {"type": "string", "required": True},
    "encounter.siteName": {"type": "string", "required": True},
    "encounter.type": {"type": "code", "required": True},
}

_VISIT_LISTS = {
    "encounter.complaints": {"type": "text_list", "required": True},
    "encounter.history": {"type": "string", "required": False},
    "encounter.diagnoses": {"type": "text_list", "required": True},
    "encounter.assessment": {"type": "string", "required": False},
    "encounter.plan": {"type": "string", "required": False},
}


def _j(path: str) -> str:
    return "{{ " + path + " }}"


def _choice_chain(variable: str, labels: dict[str, str]) -> str:
    lines: list[str] = []
    for index, (code, label) in enumerate(labels.items()):
        keyword = "if" if index == 0 else "elif"
        lines.append("{% " + keyword + " " + variable + " == '" + code + "' %}" + label)
    lines.append("{% else %}" + _j(variable) + "{% endif %}")
    return "".join(lines)


def _text_list(variable: str, none_label: str) -> str:
    return (
        "{% if "
        + variable
        + " %}<ul>{% for item in "
        + variable
        + " %}<li>{{ item }}</li>{% endfor %}</ul>"
        + "{% else %}<p>"
        + none_label
        + "</p>{% endif %}"
    )


def _row(label: str, value: str, *, numeric: bool = False) -> str:
    cell = f'<td class="num">{value}</td>' if numeric else f"<td>{value}</td>"
    return f"<tr><th>{label}</th>{cell}</tr>"


def _require_codes(
    labels: dict[str, str], expected: tuple[str, ...], *, name: str
) -> None:
    missing = [code for code in expected if code not in labels]
    if missing:
        msg = f"{name} labels missing: {missing[0]}"
        raise RuntimeError(msg)


def _identity(locale: str) -> str:
    common = COMMON_LABELS[locale]
    _require_codes(SEX_LABELS[locale], SEX_VALUES, name=f"sex {locale}")
    _require_codes(
        ENCOUNTER_TYPE_LABELS[locale],
        ENCOUNTER_TYPES,
        name=f"encounter type {locale}",
    )
    rows = "".join(
        (
            _row(common["name"], _j("patient.fullName")),
            _row(common["mrn"], _j("patient.mrn"), numeric=True),
            _row(common["birth"], _j("patient.birthDate"), numeric=True),
            _row(common["sex"], _choice_chain("patient.sex", SEX_LABELS[locale])),
            _row(common["visit_date"], _j("encounter.date"), numeric=True),
            _row(common["clinician"], _j("encounter.clinicianName")),
            _row(common["site"], _j("encounter.siteName")),
            _row(
                common["visit_type"],
                _choice_chain("encounter.type", ENCOUNTER_TYPE_LABELS[locale]),
            ),
            _row(common["issued"], _j("document.issuedOn"), numeric=True),
        )
    )
    return "<table><tbody>" + rows + "</tbody></table>"


def _section(title: str, body: str) -> str:
    return f"<h2>{title}</h2>{body}"


def _page(title: str) -> dict[str, Any]:
    return {
        "size": "A4",
        "orientation": "portrait",
        "margin_top_mm": 16,
        "margin_bottom_mm": 16,
        "margin_left_mm": 14,
        "margin_right_mm": 14,
        "title": title,
    }


def _versions(body_for: Any) -> list[dict[str, Any]]:
    versions: list[dict[str, Any]] = []
    for locale in ("en", "fr", "ar"):
        versions.append(
            {
                "locale": locale,
                "direction": "rtl" if locale == "ar" else "ltr",
                "header_html": "",
                "body_html": body_for(locale),
                "footer_html": _FOOTER,
                "css": _CSS,
                "page_setup": _page(str(SECTION_LABELS[locale][body_for.title_key])),
            }
        )
    return versions


def _consultation_body(locale: str) -> str:
    labels = SECTION_LABELS[locale]
    none = COMMON_LABELS[locale]["none"]
    return (
        f"<h1>{labels['consultation_title']}</h1>"
        + _identity(locale)
        + _section(labels["complaints"], _text_list("encounter.complaints", none))
        + _section(labels["history"], "<p>" + _j("encounter.history") + "</p>")
        + _section(labels["diagnoses"], _text_list("encounter.diagnoses", none))
        + _section(labels["assessment"], "<p>" + _j("encounter.assessment") + "</p>")
        + _section(labels["plan"], "<p>" + _j("encounter.plan") + "</p>")
    )


def _referral_body(locale: str) -> str:
    labels = SECTION_LABELS[locale]
    none = COMMON_LABELS[locale]["none"]
    return (
        f"<h1>{labels['referral_title']}</h1>"
        + _identity(locale)
        + _section(
            labels["referring_doctor"],
            "<p>" + _j("referringDoctor.name") + "</p>",
        )
        + _section(labels["complaints"], _text_list("encounter.complaints", none))
        + _section(labels["diagnoses"], _text_list("encounter.diagnoses", none))
        + _section(labels["assessment"], "<p>" + _j("encounter.assessment") + "</p>")
        + _section(labels["plan"], "<p>" + _j("encounter.plan") + "</p>")
        + _section(
            labels["recommendations"],
            "<p>" + _j("referral.recommendations") + "</p>",
        )
    )


def _sick_leave_body(locale: str) -> str:
    labels = SECTION_LABELS[locale]
    _require_codes(ABSENCE_TYPE_LABELS[locale], ABSENCE_TYPES, name=f"absence {locale}")
    reason = (
        "{% if absence.reasonMode == 'medical_reasons' %}"
        + labels["medical_reasons"]
        + "{% else %}"
        + _j("absence.reasonText")
        + "{% endif %}"
    )
    rows = "".join(
        (
            _row(
                labels["absence_type"],
                _choice_chain("absence.absenceType", ABSENCE_TYPE_LABELS[locale]),
            ),
            _row(labels["start"], _j("absence.startDate"), numeric=True),
            _row(labels["end"], _j("absence.endDate"), numeric=True),
            _row(labels["days"], _j("absence.durationDays"), numeric=True),
            _row(labels["reason"], reason),
        )
    )
    return (
        f"<h1>{labels['sick_leave_title']}</h1>"
        + _identity(locale)
        + "<table><tbody>"
        + rows
        + "</tbody></table>"
    )


def _certificate_body(locale: str) -> str:
    labels = SECTION_LABELS[locale]
    _require_codes(
        PURPOSE_LABELS[locale], CERTIFICATE_PURPOSES, name=f"purpose {locale}"
    )
    return (
        f"<h1>{labels['certificate_title']}</h1>"
        + _identity(locale)
        + _section(
            labels["purpose"],
            "<p>"
            + _choice_chain("certificate.purpose", PURPOSE_LABELS[locale])
            + "</p>",
        )
        + _section(labels["statement"], "<p>" + _j("certificate.body") + "</p>")
    )


def _yes_no(variable: str, locale: str) -> str:
    common = COMMON_LABELS[locale]
    return _choice_chain(variable, {"yes": common["yes"], "no": common["no"]})


def _imaging_body(locale: str) -> str:
    labels = SECTION_LABELS[locale]
    _require_codes(
        MODALITY_LABELS[locale], IMAGING_MODALITIES, name=f"modality {locale}"
    )
    flags = "".join(
        (
            _row(labels["pregnancy"], _yes_no("request.pregnancy", locale)),
            _row(labels["pacemaker"], _yes_no("request.pacemaker", locale)),
            _row(
                labels["cochlear_implant"],
                _yes_no("request.cochlearImplant", locale),
            ),
            _row(
                labels["contrast_allergy"],
                _yes_no("request.contrastAllergy", locale),
            ),
            _row(labels["renal"], _yes_no("request.renalImpairment", locale)),
        )
    )
    override = (
        "{% if request.mriStatus == 'overridden' %}<p>"
        + labels["override"]
        + ": "
        + _j("request.overrideReason")
        + " ("
        + _j("request.overrideClinicianPublicId")
        + ")</p>{% elif request.mriStatus == 'clear' %}<p>"
        + labels["mri_clear"]
        + "</p>{% endif %}"
    )
    return (
        f"<h1>{labels['imaging_title']}</h1>"
        + _identity(locale)
        + _section(
            labels["modality"],
            "<p>" + _choice_chain("request.modality", MODALITY_LABELS[locale]) + "</p>",
        )
        + _section(labels["question"], "<p>" + _j("request.clinicalQuestion") + "</p>")
        + "<table><tbody>"
        + flags
        + "</tbody></table>"
        + override
    )


def _lab_body(locale: str) -> str:
    labels = SECTION_LABELS[locale]
    none = COMMON_LABELS[locale]["none"]
    _require_codes(PANEL_LABELS[locale], LAB_PANELS, name=f"panel {locale}")
    chain = _choice_chain("code", PANEL_LABELS[locale])
    panels = (
        "{% if request.panels %}<ul>{% for code in request.panels %}<li>"
        + chain
        + "</li>{% endfor %}</ul>{% else %}<p>"
        + none
        + "</p>{% endif %}"
    )
    return (
        f"<h1>{labels['lab_title']}</h1>"
        + _identity(locale)
        + _section(labels["panels"], panels)
        + _section(labels["indication"], "<p>" + _j("request.indication") + "</p>")
    )


_consultation_body.title_key = "consultation_title"  # type: ignore[attr-defined]
_referral_body.title_key = "referral_title"  # type: ignore[attr-defined]
_sick_leave_body.title_key = "sick_leave_title"  # type: ignore[attr-defined]
_certificate_body.title_key = "certificate_title"  # type: ignore[attr-defined]
_imaging_body.title_key = "imaging_title"  # type: ignore[attr-defined]
_lab_body.title_key = "lab_title"  # type: ignore[attr-defined]


def _placeholders(*extra: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    merged = dict(_PATIENT_CLINIC)
    for item in extra:
        merged.update(item)
    return merged


CONSULTATION_PLACEHOLDERS = _placeholders(_VISIT_LISTS)
REFERRAL_PLACEHOLDERS = _placeholders(
    _VISIT_LISTS,
    {
        "referringDoctor.name": {"type": "string", "required": False},
        "referral.recommendations": {"type": "string", "required": False},
    },
)
SICK_LEAVE_PLACEHOLDERS = _placeholders(
    {
        "absence.absenceType": {"type": "code", "required": True},
        "absence.startDate": {"type": "date", "required": True},
        "absence.endDate": {"type": "date", "required": True},
        "absence.durationDays": {"type": "integer", "required": True},
        "absence.reasonMode": {"type": "code", "required": True},
        "absence.reasonText": {"type": "string", "required": False},
    }
)
CERTIFICATE_PLACEHOLDERS = _placeholders(
    {
        "certificate.purpose": {"type": "code", "required": True},
        "certificate.body": {"type": "string", "required": True},
    }
)
IMAGING_PLACEHOLDERS = _placeholders(
    {
        "request.modality": {"type": "code", "required": True},
        "request.clinicalQuestion": {"type": "string", "required": False},
        "request.pregnancy": {"type": "code", "required": True},
        "request.pacemaker": {"type": "code", "required": True},
        "request.cochlearImplant": {"type": "code", "required": True},
        "request.contrastAllergy": {"type": "code", "required": True},
        "request.renalImpairment": {"type": "code", "required": True},
        "request.mriStatus": {"type": "code", "required": True},
        "request.overrideReason": {"type": "string", "required": False},
        "request.overrideClinicianPublicId": {"type": "string", "required": False},
    }
)
LAB_PLACEHOLDERS = _placeholders(
    {
        "request.panels": {"type": "code_list", "required": True},
        "request.indication": {"type": "string", "required": False},
    }
)


def clinical_template_specs() -> list[dict[str, Any]]:
    """One spec per system template: code, category, placeholders, versions."""

    return [
        {
            "code": CONSULTATION_REPORT_CODE,
            "category": "consultation_report",
            "placeholders": CONSULTATION_PLACEHOLDERS,
            "versions": _versions(_consultation_body),
        },
        {
            "code": REFERRAL_LETTER_CODE,
            "category": "referral_letter",
            "placeholders": REFERRAL_PLACEHOLDERS,
            "versions": _versions(_referral_body),
        },
        {
            "code": SICK_LEAVE_CODE,
            "category": "certificate",
            "placeholders": SICK_LEAVE_PLACEHOLDERS,
            "versions": _versions(_sick_leave_body),
        },
        {
            "code": MEDICAL_CERTIFICATE_CODE,
            "category": "certificate",
            "placeholders": CERTIFICATE_PLACEHOLDERS,
            "versions": _versions(_certificate_body),
        },
        {
            "code": IMAGING_REQUEST_CODE,
            "category": "imaging_request",
            "placeholders": IMAGING_PLACEHOLDERS,
            "versions": _versions(_imaging_body),
        },
        {
            "code": LAB_REQUEST_CODE,
            "category": "lab_request",
            "placeholders": LAB_PLACEHOLDERS,
            "versions": _versions(_lab_body),
        },
    ]
