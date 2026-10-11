import type { useTranslations } from "next-intl";

type PatientsT = ReturnType<typeof useTranslations<"patients">>;

export function timelineEventLabel(t: PatientsT, eventType: string): string {
  switch (eventType) {
    case "appointment":
      return t("timeline.events.appointment");
    case "attachment":
      return t("timeline.events.attachment");
    case "consultation":
      return t("timeline.events.consultation");
    case "diagnosis":
      return t("timeline.events.diagnosis");
    case "document":
      return t("timeline.events.document");
    case "follow_up":
      return t("timeline.events.followUp");
    case "no_show":
      return t("timeline.events.noShow");
    case "phone_call":
      return t("timeline.events.phoneCall");
    case "post_op":
      return t("timeline.events.postOp");
    case "prescription":
      return t("timeline.events.prescription");
    case "procedure":
      return t("timeline.events.procedure");
    case "recall":
      return t("timeline.events.recall");
    case "recall_sent":
      return t("timeline.events.recallSent");
    case "result_review":
      return t("timeline.events.resultReview");
    case "teleconsultation":
      return t("timeline.events.teleconsultation");
    default:
      return t("timeline.events.consultation");
  }
}

export function timelineStatusLabel(t: PatientsT, status: string): string {
  switch (status) {
    case "active":
      return t("timeline.status.active");
    case "amended":
      return t("timeline.status.amended");
    case "arrived":
      return t("timeline.status.arrived");
    case "booked":
      return t("timeline.status.booked");
    case "cancelled":
      return t("timeline.status.cancelled");
    case "completed":
      return t("timeline.status.completed");
    case "done":
      return t("timeline.status.done");
    case "draft":
      return t("timeline.status.draft");
    case "in_room":
      return t("timeline.status.inRoom");
    case "overdue":
      return t("timeline.status.overdue");
    case "pending":
      return t("timeline.status.pending");
    case "recorded":
      return t("timeline.status.recorded");
    case "scheduled":
      return t("timeline.status.scheduled");
    case "signed":
      return t("timeline.status.signed");
    case "unreachable":
      return t("timeline.status.unreachable");
    default:
      return t("timeline.status.recorded");
  }
}

export function timelineLateralityLabel(t: PatientsT, value: string): string {
  switch (value) {
    case "bilateral":
      return t("timeline.laterality.bilateral");
    case "left":
      return t("timeline.laterality.left");
    case "midline":
      return t("timeline.laterality.midline");
    case "na":
      return t("timeline.laterality.na");
    case "right":
      return t("timeline.laterality.right");
    default:
      return "";
  }
}
