import type { useTranslations } from "next-intl";

import type { SafetyAlertRead } from "@/lib/api/generated";

import {
  ALLERGY_OVERRIDE,
  DOSE_OVERRIDE,
  PRESCRIPTION_ROUTES,
  PRESCRIPTION_STATUSES,
  WEIGHT_BLOCK,
  type PrescriptionRoute,
} from "../constants";

type PrescriptionT = ReturnType<typeof useTranslations<"prescriptions">>;

export function statusLabel(t: PrescriptionT, status: string): string {
  switch (status) {
    case "draft":
      return t("status.draft");
    case "issued":
      return t("status.issued");
    case "cancelled":
      return t("status.cancelled");
    default:
      return t("status.unknown");
  }
}

export function routeLabel(t: PrescriptionT, route: string): string {
  switch (route) {
    case "oral":
      return t("route.oral");
    case "nasal":
      return t("route.nasal");
    case "otic":
      return t("route.otic");
    case "topical":
      return t("route.topical");
    case "injection":
      return t("route.injection");
    default:
      return t("route.unknown");
  }
}

export function safetyLabel(t: PrescriptionT, code: string): string {
  switch (code) {
    case ALLERGY_OVERRIDE:
      return t("safety.allergyConflict");
    case DOSE_OVERRIDE:
      return t("safety.doseAboveMaximum");
    case WEIGHT_BLOCK:
      return t("safety.pediatricWeightMissing");
    case "prescription.ototoxic_with_hearing_loss":
      return t("safety.ototoxic");
    case "prescription.duplicate_class":
      return t("safety.duplicateClass");
    case "prescription.pregnancy_caution":
      return t("safety.pregnancy");
    case "prescription.breastfeeding_caution":
      return t("safety.breastfeeding");
    case "prescription.unstructured_item":
      return t("safety.unstructured");
    default:
      return t("safety.unknown");
  }
}

export function isRoute(value: string): value is PrescriptionRoute {
  return (PRESCRIPTION_ROUTES as readonly string[]).includes(value);
}

export function isKnownStatus(value: string): boolean {
  return (PRESCRIPTION_STATUSES as readonly string[]).includes(value);
}

export function alertCopy(t: PrescriptionT, alert: SafetyAlertRead): string {
  return safetyLabel(t, alert.code);
}
