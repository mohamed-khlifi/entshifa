import type { useTranslations } from "next-intl";
import { z } from "zod";

import { LATERALITY_VALUES, PATIENT_ATTACHMENT_CATEGORIES } from "../constants";

type AttachmentTranslator = ReturnType<typeof useTranslations<"attachments">>;

const lateralityField = ["", ...LATERALITY_VALUES] as [
  "",
  ...(typeof LATERALITY_VALUES)[number][],
];

export function createAttachmentUploadSchema(t: AttachmentTranslator) {
  return z.object({
    category: z.enum(PATIENT_ATTACHMENT_CATEGORIES),
    laterality: z.enum(lateralityField),
    bodySiteConceptId: z.string(),
    bodySiteDisplay: z.string(),
    capturedAt: z.string(),
    caption: z.string().max(255, t("validation.caption")),
    isConsentedForTeaching: z.boolean(),
  });
}

export type AttachmentUploadFormValues = z.infer<
  ReturnType<typeof createAttachmentUploadSchema>
>;
