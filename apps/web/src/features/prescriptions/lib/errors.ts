import type { useTranslations } from "next-intl";

import { ApiError } from "@/lib/api/errors";

type ErrorsT = ReturnType<typeof useTranslations<"errors">>;

export function prescriptionErrorText(t: ErrorsT, error: unknown): string {
  if (!(error instanceof ApiError)) {
    return t("generic");
  }
  switch (error.code) {
    case "prescription.allergy_conflict":
      return t("prescription.allergy_conflict");
    case "prescription.breastfeeding_caution":
      return t("prescription.breastfeeding_caution");
    case "prescription.dose_above_maximum":
      return t("prescription.dose_above_maximum");
    case "prescription.dosing_input_invalid":
      return t("prescription.dosing_input_invalid");
    case "prescription.dosing_rule_invalid":
      return t("prescription.dosing_rule_invalid");
    case "prescription.duplicate_class":
      return t("prescription.duplicate_class");
    case "prescription.formulary_not_found":
      return t("prescription.formulary_not_found");
    case "prescription.idempotency_mismatch":
      return t("prescription.idempotency_mismatch");
    case "prescription.invalid_status":
      return t("prescription.invalid_status");
    case "prescription.not_found":
      return t("prescription.not_found");
    case "prescription.ototoxic_with_hearing_loss":
      return t("prescription.ototoxic_with_hearing_loss");
    case "prescription.pediatric_weight_missing":
      return t("prescription.pediatric_weight_missing");
    case "prescription.pregnancy_caution":
      return t("prescription.pregnancy_caution");
    case "prescription.safety_blocked":
      return t("prescription.safety_blocked");
    case "prescription.unstructured_item":
      return t("prescription.unstructured_item");
    case "prescription.version_conflict":
      return t("prescription.version_conflict");
    default:
      return t("generic");
  }
}
