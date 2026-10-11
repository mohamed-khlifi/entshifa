import type { useTranslations } from "next-intl";

import { ApiError } from "@/lib/api/client";

type RecallsT = ReturnType<typeof useTranslations<"recalls">>;

export function recallActionTypeLabel(
  t: ReturnType<typeof useTranslations<"recalls">>,
  value: string,
): string {
  switch (value) {
    case "call":
      return t("actionTypes.call");
    case "document":
      return t("actionTypes.document");
    case "questionnaire":
      return t("actionTypes.questionnaire");
    case "test":
      return t("actionTypes.test");
    case "visit":
      return t("actionTypes.visit");
    default:
      return t("actionTypes.visit");
  }
}

export function recallTestLabel(t: RecallsT, value: string): string {
  switch (value) {
    case "audiogram":
      return t("tests.audiogram");
    case "endoscopy":
      return t("tests.endoscopy");
    case "imaging":
      return t("tests.imaging");
    case "tympanometry":
      return t("tests.tympanometry");
    default:
      return "";
  }
}

export function recallStatusLabel(t: RecallsT, value: string): string {
  switch (value) {
    case "booked":
      return t("status.booked");
    case "cancelled":
      return t("status.cancelled");
    case "done":
      return t("status.done");
    case "overdue":
      return t("status.overdue");
    case "pending":
      return t("status.pending");
    case "unreachable":
      return t("status.unreachable");
    default:
      return t("status.pending");
  }
}

export function recallOutcomeLabel(t: RecallsT, value: string): string {
  switch (value) {
    case "confirmed":
      return t("outcomes.confirmed");
    case "declined":
      return t("outcomes.declined");
    case "no_answer":
      return t("outcomes.noAnswer");
    case "reached":
      return t("outcomes.reached");
    case "unreachable":
      return t("outcomes.unreachable");
    case "voicemail":
      return t("outcomes.voicemail");
    default:
      return "";
  }
}

export function recallIntervalLabel(t: RecallsT, days: number): string {
  switch (days) {
    case 7:
      return t("intervals.days7");
    case 14:
      return t("intervals.days14");
    case 28:
      return t("intervals.days28");
    case 42:
      return t("intervals.days42");
    case 90:
      return t("intervals.days90");
    case 180:
      return t("intervals.days180");
    case 365:
      return t("intervals.days365");
    default:
      return t("intervals.days42");
  }
}

export function recallBucketLabel(t: RecallsT, bucket: string): string {
  switch (bucket) {
    case "active":
      return t("buckets.active");
    case "overdue":
      return t("buckets.overdue");
    case "unreachable":
      return t("buckets.unreachable");
    case "upcoming":
      return t("buckets.upcoming");
    default:
      return t("buckets.overdue");
  }
}

export function recallErrorText(
  errors: ReturnType<typeof useTranslations<"errors">>,
  error: unknown,
): string {
  if (!(error instanceof ApiError)) {
    return errors("generic");
  }
  switch (error.code) {
    case "recall.due_required":
      return errors("recall.due_required");
    case "recall.idempotency_mismatch":
      return errors("recall.idempotency_mismatch");
    case "recall.invalid_status":
      return errors("recall.invalid_status");
    case "recall.not_found":
      return errors("recall.not_found");
    case "recall.version_conflict":
      return errors("recall.version_conflict");
    default:
      return errors("generic");
  }
}
