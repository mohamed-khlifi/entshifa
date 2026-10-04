import type { useTranslations } from "next-intl";

type EncountersTranslator = ReturnType<typeof useTranslations<"encounters">>;

export function examSectionLabel(
  t: EncountersTranslator,
  section: string,
): string {
  switch (section) {
    case "blood_pressure":
      return t("suggestions.examSections.blood_pressure");
    case "ear":
      return t("suggestions.examSections.ear");
    case "endoscopy":
      return t("suggestions.examSections.endoscopy");
    case "face":
      return t("suggestions.examSections.face");
    case "laryngoscopy":
      return t("suggestions.examSections.laryngoscopy");
    case "neck":
      return t("suggestions.examSections.neck");
    case "neck_auscultation":
      return t("suggestions.examSections.neck_auscultation");
    case "nose":
      return t("suggestions.examSections.nose");
    case "oral_cavity":
      return t("suggestions.examSections.oral_cavity");
    case "tuning_forks":
      return t("suggestions.examSections.tuning_forks");
    case "vestibular_exam":
      return t("suggestions.examSections.vestibular_exam");
    default:
      return t("suggestions.unknown");
  }
}

export function instrumentLabel(t: EncountersTranslator, code: string): string {
  switch (code) {
    case "dhi":
      return t("suggestions.instruments.dhi");
    case "hhie":
      return t("suggestions.instruments.hhie");
    case "nose":
      return t("suggestions.instruments.nose");
    case "rsi":
      return t("suggestions.instruments.rsi");
    case "snot22":
      return t("suggestions.instruments.snot22");
    case "thi":
      return t("suggestions.instruments.thi");
    case "vhi10":
      return t("suggestions.instruments.vhi10");
    default:
      return t("suggestions.unknown");
  }
}

export function testLabel(t: EncountersTranslator, code: string): string {
  switch (code) {
    case "aria_classification":
      return t("suggestions.tests.aria_classification");
    case "audiogram":
      return t("suggestions.tests.audiogram");
    case "cautery_record":
      return t("suggestions.tests.cautery_record");
    case "coagulation_panel":
      return t("suggestions.tests.coagulation_panel");
    case "ct_sinuses":
      return t("suggestions.tests.ct_sinuses");
    case "dix_hallpike_maneuver":
      return t("suggestions.tests.dix_hallpike_maneuver");
    case "ear_swab_culture":
      return t("suggestions.tests.ear_swab_culture");
    case "flexible_laryngoscopy":
      return t("suggestions.tests.flexible_laryngoscopy");
    case "microscopy":
      return t("suggestions.tests.microscopy");
    case "mri_internal_auditory_canal":
      return t("suggestions.tests.mri_internal_auditory_canal");
    case "nasal_endoscopy":
      return t("suggestions.tests.nasal_endoscopy");
    case "otoscopy":
      return t("suggestions.tests.otoscopy");
    case "prick_test":
      return t("suggestions.tests.prick_test");
    case "rapid_strep_test":
      return t("suggestions.tests.rapid_strep_test");
    case "specific_ige":
      return t("suggestions.tests.specific_ige");
    case "throat_swab_culture":
      return t("suggestions.tests.throat_swab_culture");
    case "tympanogram":
      return t("suggestions.tests.tympanogram");
    case "vestibular_testing":
      return t("suggestions.tests.vestibular_testing");
    case "videostroboscopy":
      return t("suggestions.tests.videostroboscopy");
    default:
      return t("suggestions.unknown");
  }
}

export function documentLabel(t: EncountersTranslator, code: string): string {
  switch (code) {
    case "allergen_avoidance_handout":
      return t("suggestions.documents.allergen_avoidance_handout");
    case "bppv_home_exercises_handout":
      return t("suggestions.documents.bppv_home_exercises_handout");
    case "dry_ear_precautions_handout":
      return t("suggestions.documents.dry_ear_precautions_handout");
    case "hearing_protection_guide":
      return t("suggestions.documents.hearing_protection_guide");
    case "nosebleed_first_aid_handout":
      return t("suggestions.documents.nosebleed_first_aid_handout");
    case "saline_irrigation_handout":
      return t("suggestions.documents.saline_irrigation_handout");
    case "sinusitis_advice":
      return t("suggestions.documents.sinusitis_advice");
    case "tinnitus_management_handout":
      return t("suggestions.documents.tinnitus_management_handout");
    case "tonsillitis_care_guide":
      return t("suggestions.documents.tonsillitis_care_guide");
    case "vocal_hygiene_handout":
      return t("suggestions.documents.vocal_hygiene_handout");
    default:
      return t("suggestions.unknown");
  }
}
