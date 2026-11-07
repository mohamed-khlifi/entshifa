"""Shared response-scale labels for launch instruments (en, fr, ar)."""

from __future__ import annotations

from typing import Final

# Keys are scale identifiers; values map locale -> option value (str) -> label text.


def _likert_0_5_en() -> dict[str, str]:
    return {
        "0": "No problem",
        "1": "Very mild problem",
        "2": "Mild or slight problem",
        "3": "Moderate problem",
        "4": "Severe problem",
        "5": "Problem as bad as it can be",
    }


def _likert_0_5_fr() -> dict[str, str]:
    return {
        "0": "Aucun problème",
        "1": "Problème très léger",
        "2": "Problème léger",
        "3": "Problème modéré",
        "4": "Problème sévère",
        "5": "Problème maximal",
    }


def _likert_0_5_ar() -> dict[str, str]:
    return {
        "0": "لا مشكلة",
        "1": "مشكلة خفيفة جداً",
        "2": "مشكلة خفيفة",
        "3": "مشكلة متوسطة",
        "4": "مشكلة شديدة",
        "5": "أسوأ مشكلة ممكنة",
    }


def _likert_0_4_en() -> dict[str, str]:
    return {
        "0": "Not a problem",
        "1": "Very mild problem",
        "2": "Moderate problem",
        "3": "Fairly bad problem",
        "4": "Severe problem",
    }


def _likert_0_4_fr() -> dict[str, str]:
    return {
        "0": "Pas un problème",
        "1": "Problème très léger",
        "2": "Problème modéré",
        "3": "Problème assez important",
        "4": "Problème sévère",
    }


def _likert_0_4_ar() -> dict[str, str]:
    return {
        "0": "ليست مشكلة",
        "1": "مشكلة خفيفة جداً",
        "2": "مشكلة متوسطة",
        "3": "مشكلة ملحوظة",
        "4": "مشكلة شديدة",
    }


def _vhi_0_4_en() -> dict[str, str]:
    return {
        "0": "Never",
        "1": "Almost never",
        "2": "Sometimes",
        "3": "Almost always",
        "4": "Always",
    }


def _vhi_0_4_fr() -> dict[str, str]:
    return {
        "0": "Jamais",
        "1": "Presque jamais",
        "2": "Parfois",
        "3": "Presque toujours",
        "4": "Toujours",
    }


def _vhi_0_4_ar() -> dict[str, str]:
    return {
        "0": "أبداً",
        "1": "نادراً جداً",
        "2": "أحياناً",
        "3": "كثيراً",
        "4": "دائماً",
    }


def _thi_dhi_en() -> dict[str, str]:
    return {
        "0": "No",
        "2": "Sometimes",
        "4": "Yes",
    }


def _thi_dhi_fr() -> dict[str, str]:
    return {
        "0": "Non",
        "2": "Parfois",
        "4": "Oui",
    }


def _thi_dhi_ar() -> dict[str, str]:
    return {
        "0": "لا",
        "2": "أحياناً",
        "4": "نعم",
    }


def _likert_0_5_rsi_en() -> dict[str, str]:
    return {
        "0": "No problem",
        "1": "Very mild problem",
        "2": "Mild or slight problem",
        "3": "Moderate problem",
        "4": "Severe problem",
        "5": "Very severe problem",
    }


def _likert_0_5_rsi_fr() -> dict[str, str]:
    return {
        "0": "Aucun problème",
        "1": "Problème très léger",
        "2": "Problème léger",
        "3": "Problème modéré",
        "4": "Problème sévère",
        "5": "Problème très sévère",
    }


def _likert_0_5_rsi_ar() -> dict[str, str]:
    return {
        "0": "لا مشكلة",
        "1": "مشكلة خفيفة جداً",
        "2": "مشكلة خفيفة",
        "3": "مشكلة متوسطة",
        "4": "مشكلة شديدة",
        "5": "مشكلة شديدة جداً",
    }


def _epworth_en() -> dict[str, str]:
    return {
        "0": "Would never doze",
        "1": "Slight chance of dozing",
        "2": "Moderate chance of dozing",
        "3": "High chance of dozing",
    }


def _epworth_fr() -> dict[str, str]:
    return {
        "0": "Ne somnolerait jamais",
        "1": "Faible chance de somnoler",
        "2": "Chance modérée de somnoler",
        "3": "Forte chance de somnoler",
    }


def _epworth_ar() -> dict[str, str]:
    return {
        "0": "لن أغفو أبداً",
        "1": "احتمال ضعيف للغفو",
        "2": "احتمال متوسط للغفو",
        "3": "احتمال كبير للغفو",
    }


def _yes_no_en() -> dict[str, str]:
    return {"0": "No", "1": "Yes"}


def _yes_no_fr() -> dict[str, str]:
    return {"0": "Non", "1": "Oui"}


def _yes_no_ar() -> dict[str, str]:
    return {"0": "لا", "1": "نعم"}


def _osa_1_7_en() -> dict[str, str]:
    return {
        "1": "None of the time",
        "2": "Hardly any of the time",
        "3": "A little of the time",
        "4": "Some of the time",
        "5": "A good bit of the time",
        "6": "Most of the time",
        "7": "All of the time",
    }


def _osa_1_7_fr() -> dict[str, str]:
    return {
        "1": "Jamais",
        "2": "Presque jamais",
        "3": "Un peu du temps",
        "4": "Une partie du temps",
        "5": "Souvent",
        "6": "La plupart du temps",
        "7": "Tout le temps",
    }


def _osa_1_7_ar() -> dict[str, str]:
    return {
        "1": "أبداً",
        "2": "بالكاد",
        "3": "قليلاً",
        "4": "أحياناً",
        "5": "كثيراً",
        "6": "معظم الوقت",
        "7": "طوال الوقت",
    }


SCALE_OPTION_LABELS: Final[dict[str, dict[str, dict[str, str]]]] = {
    "likert_0_5": {
        "en": _likert_0_5_en(),
        "fr": _likert_0_5_fr(),
        "ar": _likert_0_5_ar(),
    },
    "likert_0_4": {
        "en": _likert_0_4_en(),
        "fr": _likert_0_4_fr(),
        "ar": _likert_0_4_ar(),
    },
    "vhi_0_4": {
        "en": _vhi_0_4_en(),
        "fr": _vhi_0_4_fr(),
        "ar": _vhi_0_4_ar(),
    },
    "thi_dhi": {
        "en": _thi_dhi_en(),
        "fr": _thi_dhi_fr(),
        "ar": _thi_dhi_ar(),
    },
    "likert_0_5_rsi": {
        "en": _likert_0_5_rsi_en(),
        "fr": _likert_0_5_rsi_fr(),
        "ar": _likert_0_5_rsi_ar(),
    },
    "epworth": {
        "en": _epworth_en(),
        "fr": _epworth_fr(),
        "ar": _epworth_ar(),
    },
    "yes_no": {
        "en": _yes_no_en(),
        "fr": _yes_no_fr(),
        "ar": _yes_no_ar(),
    },
    "osa_1_7": {
        "en": _osa_1_7_en(),
        "fr": _osa_1_7_fr(),
        "ar": _osa_1_7_ar(),
    },
}


def option_values_for_scale(scale_key: str) -> tuple[int, ...]:
    labels = SCALE_OPTION_LABELS[scale_key]["en"]
    return tuple(sorted(int(v) for v in labels))


def shared_option_translations(
    scale_key: str,
) -> dict[str, dict[str, str]]:
    """Return locale -> option value string -> label for seed translations."""
    out: dict[str, dict[str, str]] = {}
    for locale in ("en", "fr", "ar"):
        out[locale] = dict(SCALE_OPTION_LABELS[scale_key][locale])
    return out
