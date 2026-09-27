import type { useTranslations } from "next-intl";

type AttachmentTranslator = ReturnType<typeof useTranslations<"attachments">>;

export function categoryLabel(
  t: AttachmentTranslator,
  category: string,
): string {
  switch (category) {
    case "endoscopy_image":
      return t("category.endoscopy_image");
    case "endoscopy_video":
      return t("category.endoscopy_video");
    case "clinical_photo":
      return t("category.clinical_photo");
    case "audiogram_scan":
      return t("category.audiogram_scan");
    case "imaging_report":
      return t("category.imaging_report");
    case "pathology":
      return t("category.pathology");
    case "external_letter":
      return t("category.external_letter");
    case "document_pdf":
      return t("category.document_pdf");
    case "signature":
      return t("category.signature");
    case "logo":
      return t("category.logo");
    case "voice_recording":
      return t("category.voice_recording");
    default:
      return t("category.unknown");
  }
}

export function lateralityLabel(
  t: AttachmentTranslator,
  laterality: string | null | undefined,
): string {
  switch (laterality) {
    case "left":
      return t("laterality.left");
    case "right":
      return t("laterality.right");
    case "bilateral":
      return t("laterality.bilateral");
    case "midline":
      return t("laterality.midline");
    case "na":
      return t("laterality.na");
    default:
      return t("laterality.unspecified");
  }
}

export function processingLabel(
  t: AttachmentTranslator,
  status: string,
): string {
  switch (status) {
    case "processing":
      return t("viewer.statusValues.processing");
    case "ready":
      return t("viewer.statusValues.ready");
    case "failed":
      return t("viewer.statusValues.failed");
    default:
      return t("viewer.statusValues.pending");
  }
}

export function presetLabel(t: AttachmentTranslator, category: string): string {
  switch (category) {
    case "endoscopy_image":
      return t("upload.presets.endoscopyImage");
    case "endoscopy_video":
      return t("upload.presets.endoscopyVideo");
    case "clinical_photo":
      return t("upload.presets.clinicalPhoto");
    case "audiogram_scan":
      return t("upload.presets.audiogramScan");
    case "imaging_report":
      return t("upload.presets.imagingReport");
    case "pathology":
      return t("upload.presets.pathology");
    case "external_letter":
      return t("upload.presets.externalLetter");
    case "document_pdf":
      return t("upload.presets.documentPdf");
    default:
      return t("category.unknown");
  }
}

export function consentLabel(
  t: AttachmentTranslator,
  consented: boolean,
): string {
  return consented ? t("consent.yes") : t("consent.no");
}
