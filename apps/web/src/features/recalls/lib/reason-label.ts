import type { useTranslations } from "next-intl";

type RecallTranslator = ReturnType<typeof useTranslations<"recalls">>;

export function recallReasonLabel(
  t: RecallTranslator,
  reasonKey: string | null | undefined,
  reasonText: string | null | undefined,
): string {
  switch (reasonKey) {
    case "office_pack_removal":
      return t("reasons.packRemoval");
    case "office_splint_removal":
      return t("reasons.splintRemoval");
    case "office_specimen_review":
      return t("reasons.specimenReview");
    case "office_sialendoscopy_review":
      return t("reasons.sialendoscopyReview");
    case "otology_wick_removal":
      return t("reasons.otologyWickRemoval");
    case "otology_tube_patency":
      return t("reasons.otologyTubePatency");
    case "otology_tube_audiogram":
      return t("reasons.otologyTubeAudiogram");
    case "otology_tube_check":
      return t("reasons.otologyTubeCheck");
    case "otology_cavity_cleaning":
      return t("reasons.otologyCavityCleaning");
    case "otology_canal_injury":
      return t("reasons.otologyCanalInjury");
    default:
      return reasonText ?? "";
  }
}
