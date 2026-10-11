import type { PatientTimelineItemRead } from "@/lib/api/generated";

const VISIT_TYPES = new Set([
  "consultation",
  "follow_up",
  "procedure",
  "post_op",
  "result_review",
  "teleconsultation",
]);

export function timelineHref(
  patientId: string,
  item: Pick<
    PatientTimelineItemRead,
    "eventType" | "publicId" | "encounterPublicId"
  >,
): string {
  if (VISIT_TYPES.has(item.eventType)) {
    return `/patients/${patientId}/encounters/${item.publicId}`;
  }
  switch (item.eventType) {
    case "diagnosis":
      return item.encounterPublicId
        ? `/patients/${patientId}/encounters/${item.encounterPublicId}`
        : `/patients/${patientId}/examination`;
    case "prescription":
      return `/patients/${patientId}/prescriptions`;
    case "document":
      return `/patients/${patientId}/documents`;
    case "appointment":
    case "no_show":
      return "/schedule";
    case "attachment":
      return `/patients/${patientId}/attachments`;
    default:
      return "/recalls";
  }
}
