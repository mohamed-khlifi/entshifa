import type { useTranslations } from "next-intl";

type PatientTranslator = ReturnType<typeof useTranslations<"patients">>;

export function sexLabel(t: PatientTranslator, sex: string): string {
  switch (sex) {
    case "male":
      return t("sex.male");
    case "female":
      return t("sex.female");
    case "other":
      return t("sex.other");
    default:
      return t("sex.unknown");
  }
}

export function flagLabel(t: PatientTranslator, code: string): string {
  switch (code) {
    case "only_hearing_ear":
      return t("flags.onlyHearingEar");
    case "anticoagulant":
      return t("flags.anticoagulant");
    case "ototoxic_therapy":
      return t("flags.ototoxicTherapy");
    case "difficult_airway":
      return t("flags.difficultAirway");
    case "tracheostomy":
      return t("flags.tracheostomy");
    case "laryngeal_stenosis":
      return t("flags.laryngealStenosis");
    case "cochlear_implant":
      return t("flags.cochlearImplant");
    case "pacemaker":
      return t("flags.pacemaker");
    case "immunosuppressed":
      return t("flags.immunosuppressed");
    case "diabetes":
      return t("flags.diabetes");
    case "pregnancy":
      return t("flags.pregnancy");
    case "breastfeeding":
      return t("flags.breastfeeding");
    case "pediatric_weight_missing":
      return t("flags.pediatricWeightMissing");
    default:
      return t("flags.unknown", { code });
  }
}

export function allergyCategoryLabel(
  t: PatientTranslator,
  value: string,
): string {
  switch (value) {
    case "drug":
      return t("allergy.drug");
    case "food":
      return t("allergy.food");
    default:
      return t("allergy.other");
  }
}

export function severityLabel(t: PatientTranslator, value: string): string {
  switch (value) {
    case "mild":
      return t("severity.mild");
    case "moderate":
      return t("severity.moderate");
    case "severe":
      return t("severity.severe");
    default:
      return t("severity.mild");
  }
}

export function medicationSourceLabel(
  t: PatientTranslator,
  value: string,
): string {
  switch (value) {
    case "prescribed_here":
      return t("medicationSource.prescribedHere");
    case "reported":
      return t("medicationSource.reported");
    default:
      return t("medicationSource.external");
  }
}

export function problemStatusLabel(
  t: PatientTranslator,
  value: string,
): string {
  switch (value) {
    case "active":
      return t("problem.active");
    case "resolved":
      return t("problem.resolved");
    case "suspected":
      return t("problem.suspected");
    default:
      return t("problem.ruledOut");
  }
}

export function historyCategoryLabel(
  t: PatientTranslator,
  value: string,
): string {
  switch (value) {
    case "ent_surgery":
      return t("history.entSurgery");
    case "other_surgery":
      return t("history.otherSurgery");
    case "medical":
      return t("history.medical");
    case "family":
      return t("history.family");
    case "social":
      return t("history.social");
    default:
      return t("history.obstetric");
  }
}

export function identifierTypeLabel(
  t: PatientTranslator,
  value: string,
): string {
  switch (value) {
    case "national_id":
      return t("identifier.nationalId");
    case "passport":
      return t("identifier.passport");
    default:
      return t("identifier.insurance");
  }
}
