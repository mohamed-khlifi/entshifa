import type { useTranslations } from "next-intl";

type DocumentsT = ReturnType<typeof useTranslations<"documents">>;

export function documentStatusLabel(t: DocumentsT, status: string): string {
  switch (status) {
    case "draft":
      return t("status.draft");
    case "final":
      return t("status.final");
    case "cancelled":
      return t("status.cancelled");
    default:
      return t("status.draft");
  }
}

export function documentLocaleLabel(t: DocumentsT, locale: string): string {
  switch (locale) {
    case "en":
      return t("locale.en");
    case "fr":
      return t("locale.fr");
    case "ar":
      return t("locale.ar");
    default:
      return t("locale.en");
  }
}

export function documentCategoryLabel(t: DocumentsT, category: string): string {
  switch (category) {
    case "patient_summary":
      return t("category.patient_summary");
    case "handout":
      return t("category.handout");
    case "consultation_report":
      return t("category.consultation_report");
    case "endoscopy_report":
      return t("category.endoscopy_report");
    case "audiology_report":
      return t("category.audiology_report");
    case "prescription":
      return t("category.prescription");
    case "certificate":
      return t("category.certificate");
    case "imaging_request":
      return t("category.imaging_request");
    case "referral_letter":
      return t("category.referral_letter");
    case "consent":
      return t("category.consent");
    case "quote":
      return t("category.quote");
    case "operative_note":
      return t("category.operative_note");
    case "tumor_board":
      return t("category.tumor_board");
    default:
      return t("category.unknown");
  }
}
