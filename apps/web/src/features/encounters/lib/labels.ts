import type { useTranslations } from "next-intl";

import type { RedFlagId } from "./red-flags";

type EncountersTranslator = ReturnType<typeof useTranslations<"encounters">>;

export function redFlagLabel(t: EncountersTranslator, flag: RedFlagId): string {
  switch (flag) {
    case "dysphagiaWeightLoss":
      return t("redFlags.dysphagiaWeightLoss");
    case "facialWeaknessParotid":
      return t("redFlags.facialWeaknessParotid");
    case "hoarsenessSmoker":
      return t("redFlags.hoarsenessSmoker");
    case "neckLumpAdult":
      return t("redFlags.neckLumpAdult");
    case "stridor":
      return t("redFlags.stridor");
    case "suddenHearingLoss":
      return t("redFlags.suddenHearingLoss");
    case "unilateralObstructionBleeding":
      return t("redFlags.unilateralObstructionBleeding");
    case "unilateralTinnitus":
      return t("redFlags.unilateralTinnitus");
    default: {
      const exhaustive: never = flag;
      return exhaustive;
    }
  }
}

export function planKindLabel(t: EncountersTranslator, kind: string): string {
  switch (kind) {
    case "advice":
      return t("plan.kinds.advice");
    case "certificate":
      return t("plan.kinds.certificate");
    case "follow_up":
      return t("plan.kinds.followUp");
    case "imaging_requested":
      return t("plan.kinds.imagingRequested");
    case "medication":
      return t("plan.kinds.medication");
    case "procedure_today":
      return t("plan.kinds.procedureToday");
    case "referral":
      return t("plan.kinds.referral");
    case "sick_leave":
      return t("plan.kinds.sickLeave");
    case "surgery_proposed":
      return t("plan.kinds.surgeryProposed");
    case "test_requested":
      return t("plan.kinds.testRequested");
    default:
      return t("suggestions.unknown");
  }
}

export function courseLabel(t: EncountersTranslator, value: string): string {
  switch (value) {
    case "constant":
      return t("history.courseOptions.constant");
    case "improving":
      return t("history.courseOptions.improving");
    case "intermittent":
      return t("history.courseOptions.intermittent");
    case "progressive":
      return t("history.courseOptions.progressive");
    default:
      return "";
  }
}

export function historyLateralityLabel(
  t: EncountersTranslator,
  value: string,
): string {
  switch (value) {
    case "alternating":
      return t("history.lateralityOptions.alternating");
    case "bilateral":
      return t("history.lateralityOptions.bilateral");
    case "left":
      return t("history.lateralityOptions.left");
    case "right":
      return t("history.lateralityOptions.right");
    default:
      return "";
  }
}

export function diagnosisSideLabel(
  t: EncountersTranslator,
  value: string,
): string {
  switch (value) {
    case "bilateral":
      return t("assessment.side.bilateral");
    case "left":
      return t("assessment.side.left");
    case "na":
      return t("assessment.side.na");
    case "right":
      return t("assessment.side.right");
    default:
      return t("assessment.side.na");
  }
}

export function diagnosisStatusLabel(
  t: EncountersTranslator,
  value: string,
): string {
  switch (value) {
    case "confirmed":
      return t("assessment.statusOptions.confirmed");
    case "ruled_out":
      return t("assessment.statusOptions.ruledOut");
    case "suspected":
      return t("assessment.statusOptions.suspected");
    default:
      return t("assessment.statusOptions.suspected");
  }
}

export function complaintRegionLabel(
  t: EncountersTranslator,
  region: string,
): string {
  switch (region) {
    case "balance":
      return t("complaints.regions.balance");
    case "ear":
      return t("complaints.regions.ear");
    case "nose":
      return t("complaints.regions.nose");
    case "other":
      return t("complaints.regions.other");
    case "throat":
      return t("complaints.regions.throat");
    case "voice":
      return t("complaints.regions.voice");
    default:
      return t("complaints.regions.other");
  }
}
