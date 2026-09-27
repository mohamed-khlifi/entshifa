"""Patient summary template bodies for en, fr, and ar.

Display strings live in the template version rows. Python does not assemble
the sentences.
"""

from __future__ import annotations

from typing import Any

from ent.features.documents.constants import PATIENT_SUMMARY_CODE
from ent.features.patients.constants import PATIENT_FLAG_CODES, SEX_VALUES

_SHARED_CSS = """
body { font-family: "Segoe UI", Tahoma, "Noto Naskh Arabic", "DejaVu Sans", sans-serif;
       font-size: 11pt; }
h1 { font-size: 16pt; margin: 0 0 8pt; }
table { width: 100%; border-collapse: collapse; margin: 8pt 0 12pt; }
th, td { border: 1px solid #444; padding: 4pt 6pt; text-align: start; vertical-align: top; }
th { width: 34%; }
td.num { direction: ltr; unicode-bidi: isolate; }
ul { margin: 0; padding-inline-start: 16pt; }
footer { margin-top: 16pt; font-size: 9pt; }
"""

_SEX = {
    "en": {
        "male": "Male",
        "female": "Female",
        "other": "Other",
        "unknown": "Unknown",
    },
    "fr": {
        "male": "Masculin",
        "female": "Féminin",
        "other": "Autre",
        "unknown": "Inconnu",
    },
    "ar": {
        "male": "ذكر",
        "female": "أنثى",
        "other": "آخر",
        "unknown": "غير معروف",
    },
}

_FLAGS = {
    "en": {
        "only_hearing_ear": "Only hearing ear",
        "anticoagulant": "Anticoagulant or antiplatelet",
        "ototoxic_therapy": "Ototoxic therapy",
        "difficult_airway": "Difficult airway",
        "tracheostomy": "Tracheostomy",
        "laryngeal_stenosis": "Laryngeal stenosis",
        "cochlear_implant": "Cochlear implant",
        "pacemaker": "Pacemaker",
        "immunosuppressed": "Immunosuppressed",
        "diabetes": "Diabetes",
        "pregnancy": "Pregnancy",
        "breastfeeding": "Breastfeeding",
        "pediatric_weight_missing": "Pediatric weight missing",
    },
    "fr": {
        "only_hearing_ear": "Oreille unique",
        "anticoagulant": "Anticoagulant ou antiagrégant",
        "ototoxic_therapy": "Traitement ototoxique",
        "difficult_airway": "Voies aériennes difficiles",
        "tracheostomy": "Trachéotomie",
        "laryngeal_stenosis": "Sténose laryngée",
        "cochlear_implant": "Implant cochléaire",
        "pacemaker": "Pacemaker",
        "immunosuppressed": "Immunodépression",
        "diabetes": "Diabète",
        "pregnancy": "Grossesse",
        "breastfeeding": "Allaitement",
        "pediatric_weight_missing": "Poids pédiatrique manquant",
    },
    "ar": {
        "only_hearing_ear": "أذن سمع وحيدة",
        "anticoagulant": "مضاد تخثر أو مضاد صفيحات",
        "ototoxic_therapy": "علاج سام للأذن",
        "difficult_airway": "مجرى هوائي صعب",
        "tracheostomy": "فغر الرغامى",
        "laryngeal_stenosis": "تضيق الحنجرة",
        "cochlear_implant": "زرعة قوقعة",
        "pacemaker": "ناظمة قلبية",
        "immunosuppressed": "نقص المناعة",
        "diabetes": "السكري",
        "pregnancy": "حمل",
        "breastfeeding": "إرضاع",
        "pediatric_weight_missing": "وزن الطفل غير مسجل",
    },
}

_LABELS = {
    "en": {
        "title": "Patient summary",
        "name": "Name",
        "name_alt": "Name (other script)",
        "mrn": "MRN",
        "birth": "Date of birth",
        "years": "Completed years",
        "months": "Completed months",
        "sex": "Sex",
        "alerts": "Safety alerts",
        "allergies": "Allergies",
        "problems": "Active problems",
        "medications": "Current medications",
        "none": "None recorded",
        "issued": "Issued",
    },
    "fr": {
        "title": "Synthèse du patient",
        "name": "Nom",
        "name_alt": "Nom (autre écriture)",
        "mrn": "IPP",
        "birth": "Date de naissance",
        "years": "Années révolues",
        "months": "Mois révolus",
        "sex": "Sexe",
        "alerts": "Alertes de sécurité",
        "allergies": "Allergies",
        "problems": "Problèmes actifs",
        "medications": "Traitements en cours",
        "none": "Aucun élément",
        "issued": "Émis le",
    },
    "ar": {
        "title": "ملخص المريض",
        "name": "الاسم",
        "name_alt": "الاسم بكتابة أخرى",
        "mrn": "رقم الملف",
        "birth": "تاريخ الميلاد",
        "years": "السنوات المكتملة",
        "months": "الأشهر المكتملة",
        "sex": "الجنس",
        "alerts": "تنبيهات السلامة",
        "allergies": "الحساسية",
        "problems": "المشكلات النشطة",
        "medications": "الأدوية الحالية",
        "none": "لا يوجد تسجيل",
        "issued": "تاريخ الإصدار",
    },
}

PATIENT_SUMMARY_PLACEHOLDERS: dict[str, dict[str, Any]] = {
    "patient.fullName": {"type": "string", "required": True},
    "patient.fullNameAlt": {"type": "string", "required": False},
    "patient.mrn": {"type": "string", "required": True},
    "patient.birthDate": {"type": "date", "required": True},
    "patient.ageYears": {"type": "integer", "required": True},
    "patient.ageMonths": {"type": "integer", "required": True},
    "patient.sex": {"type": "code", "required": True},
    "patient.safetyAlerts": {"type": "code_list", "required": True},
    "patient.allergies": {"type": "text_list", "required": True},
    "patient.problems": {"type": "text_list", "required": True},
    "patient.medications": {"type": "text_list", "required": True},
    "clinic.name": {"type": "string", "required": True},
    "clinic.phone": {"type": "string", "required": False},
    "clinic.address": {"type": "string", "required": False},
    "document.issuedOn": {"type": "date", "required": True},
}


def _choice_chain(variable: str, labels: dict[str, str]) -> str:
    lines: list[str] = []
    for index, (code, label) in enumerate(labels.items()):
        keyword = "if" if index == 0 else "elif"
        lines.append(f"{{% {keyword} {variable} == '{code}' %}}{label}")
    lines.append("{% else %}{{ " + variable + " }}{% endif %}")
    return "".join(lines)


def _flag_list(locale: str, none_label: str) -> str:
    flags = _FLAGS[locale]
    missing = [code for code in PATIENT_FLAG_CODES if code not in flags]
    if missing:
        msg = f"patient summary flags missing for {locale}"
        raise RuntimeError(msg)
    chain = _choice_chain("code", flags)
    return (
        "{% if patient.safetyAlerts %}<ul>"
        "{% for code in patient.safetyAlerts %}<li>"
        + chain
        + "</li>{% endfor %}</ul>{% else %}<p>"
        + none_label
        + "</p>{% endif %}"
    )


def _text_list(variable: str, none_label: str) -> str:
    return (
        "{% if " + variable + " %}<ul>{% for item in " + variable + " %}"
        "<li>{{ item }}</li>{% endfor %}</ul>{% else %}<p>"
        + none_label
        + "</p>{% endif %}"
    )


def patient_summary_versions() -> list[dict[str, Any]]:
    """Locale rows inserted as document_template_version data."""

    versions: list[dict[str, Any]] = []
    for locale, labels in _LABELS.items():
        direction = "rtl" if locale == "ar" else "ltr"
        sex_chain = _choice_chain("patient.sex", _SEX[locale])
        none = str(labels["none"])
        body = f"""
<h1>{labels["title"]}</h1>
<table class="identity">
<tbody>
<tr><th>{labels["name"]}</th><td>{{{{ patient.fullName }}}}</td></tr>
{{% if patient.fullNameAlt %}}<tr><th>{labels["name_alt"]}</th><td>{{{{ patient.fullNameAlt }}}}</td></tr>{{% endif %}}
<tr><th>{labels["mrn"]}</th><td class="num">{{{{ patient.mrn }}}}</td></tr>
<tr><th>{labels["birth"]}</th><td class="num">{{{{ patient.birthDate }}}}</td></tr>
<tr><th>{labels["years"]}</th><td class="num">{{{{ patient.ageYears }}}}</td></tr>
<tr><th>{labels["months"]}</th><td class="num">{{{{ patient.ageMonths }}}}</td></tr>
<tr><th>{labels["sex"]}</th><td>{sex_chain}</td></tr>
<tr><th>{labels["issued"]}</th><td class="num">{{{{ document.issuedOn }}}}</td></tr>
</tbody>
</table>
<h2>{labels["alerts"]}</h2>
{_flag_list(locale, none)}
<h2>{labels["allergies"]}</h2>
{_text_list("patient.allergies", none)}
<h2>{labels["problems"]}</h2>
{_text_list("patient.problems", none)}
<h2>{labels["medications"]}</h2>
{_text_list("patient.medications", none)}
"""
        versions.append(
            {
                "locale": locale,
                "direction": direction,
                "header_html": "",
                "body_html": body,
                "footer_html": (
                    "<footer><p>{{ clinic.name }}</p>"
                    '<p class="num">{{ clinic.phone }}</p>'
                    "<p>{{ clinic.address }}</p></footer>"
                ),
                "css": _SHARED_CSS,
                "page_setup": {
                    "size": "A4",
                    "orientation": "portrait",
                    "margin_top_mm": 16,
                    "margin_bottom_mm": 16,
                    "margin_left_mm": 14,
                    "margin_right_mm": 14,
                    "title": labels["title"],
                },
            }
        )
    return versions


def declared_placeholder_names() -> set[str]:
    return set(PATIENT_SUMMARY_PLACEHOLDERS)


def template_code() -> str:
    return PATIENT_SUMMARY_CODE


def sex_codes_covered() -> tuple[str, ...]:
    return SEX_VALUES
