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
    default:
      return reasonText ?? "";
  }
}
