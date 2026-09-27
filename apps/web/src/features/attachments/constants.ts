/** Patient-chart categories. Logo and signature stay on clinic branding. */

export const PATIENT_ATTACHMENT_CATEGORIES = [
  "endoscopy_image",
  "endoscopy_video",
  "clinical_photo",
  "audiogram_scan",
  "imaging_report",
  "pathology",
  "external_letter",
  "document_pdf",
] as const;

export type PatientAttachmentCategory =
  (typeof PATIENT_ATTACHMENT_CATEGORIES)[number];

export const EXTERNAL_DOCUMENT_CATEGORIES = [
  "audiogram_scan",
  "imaging_report",
  "pathology",
  "external_letter",
  "document_pdf",
] as const satisfies readonly PatientAttachmentCategory[];

export const LATERALITY_VALUES = [
  "right",
  "left",
  "bilateral",
  "midline",
  "na",
] as const;

export type LateralityValue = (typeof LATERALITY_VALUES)[number];

/** Mirrors the API hard cap in AttachmentUploadUrlRequest.size_bytes. */
export const MAX_UPLOAD_BYTES = 2_147_483_648;

export const GALLERY_PAGE_SIZE = 24;
