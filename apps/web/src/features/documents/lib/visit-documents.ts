import type { ImagingRequestInput } from "@/lib/api/generated";

/** Matches engines.documents.safety.MIN_OVERRIDE_REASON_LENGTH. */
export const MIN_OVERRIDE_REASON_LENGTH = 8;

export const IMAGING_MODALITIES = [
  "ct_sinuses_noncontrast",
  "ct_temporal_bone_hr",
  "ct_neck_contrast",
  "mri_iac_gadolinium",
  "mri_neck",
  "pet_ct",
  "us_neck_fna",
  "panoramic_dental",
  "lateral_neck_adenoids",
] as const satisfies readonly ImagingRequestInput["modality"][];

export const LAB_PANELS = [
  "preoperative",
  "thyroid_calcitonin",
  "allergy_ige",
  "autoimmune_inner_ear",
  "sudden_hearing_loss_screen",
  "ear_discharge_culture",
  "hpv_status",
  "epistaxis_coagulation",
] as const;

export const CERTIFICATE_PURPOSES = [
  "fitness",
  "swimming_tubes",
  "air_travel",
  "diving",
  "voice",
  "attendance",
  "other",
] as const;

export const VISIT_DOCUMENT_KINDS = [
  "consultation",
  "referral",
  "sick_leave",
  "certificate",
  "imaging",
  "laboratory",
  "batch",
] as const;

export type VisitDocumentKind = (typeof VISIT_DOCUMENT_KINDS)[number];

const MRI_MODALITIES = new Set<string>(["mri_iac_gadolinium", "mri_neck"]);
const IMPLANT_FLAGS = new Set<string>(["cochlear_implant", "pacemaker"]);

export function isMriModality(modality: string): boolean {
  return MRI_MODALITIES.has(modality);
}

export function mriOverrideRequired(
  modality: string,
  flagCodes: readonly string[],
): boolean {
  return (
    isMriModality(modality) && flagCodes.some((code) => IMPLANT_FLAGS.has(code))
  );
}

export function overrideReasonAccepted(reason: string): boolean {
  return reason.trim().length >= MIN_OVERRIDE_REASON_LENGTH;
}

export function documentKindForPlan(kind: string): VisitDocumentKind | null {
  switch (kind) {
    case "imaging_requested":
      return "imaging";
    case "sick_leave":
      return "sick_leave";
    case "referral":
      return "referral";
    case "certificate":
      return "certificate";
    case "test_requested":
      return "laboratory";
    default:
      return null;
  }
}

export function suggestedClinicalQuestion(parts: {
  complaints: readonly string[];
  diagnoses: readonly string[];
  assessment: string;
}): string {
  return [...parts.complaints, ...parts.diagnoses, parts.assessment]
    .map((item) => item.trim())
    .filter((item) => item.length > 0)
    .join(" · ");
}

export function activeFlagCodes(
  flags: readonly { flagCode: string; endedOn: string | null }[],
): string[] {
  return flags
    .filter((flag) => flag.endedOn == null || flag.endedOn.length === 0)
    .map((flag) => flag.flagCode);
}
