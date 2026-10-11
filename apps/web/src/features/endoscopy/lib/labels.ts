import type { useTranslations } from "next-intl";

import type { DraftIssue, LkItem, StructureStatus } from "./draft";

export type EndoscopyTranslator = ReturnType<
  typeof useTranslations<"endoscopy">
>;

export function scopeLabel(t: EndoscopyTranslator, value: string): string {
  switch (value) {
    case "flexible":
      return t("scope.flexible");
    case "rigid_0":
      return t("scope.rigid0");
    case "rigid_30":
      return t("scope.rigid30");
    case "rigid_70":
      return t("scope.rigid70");
    default:
      return t("scope.flexible");
  }
}

export function anesthesiaLabel(t: EndoscopyTranslator, value: string): string {
  switch (value) {
    case "none":
      return t("anesthesia.none");
    case "topical_spray":
      return t("anesthesia.topicalSpray");
    case "local_infiltration":
      return t("anesthesia.localInfiltration");
    case "general":
      return t("anesthesia.general");
    default:
      return t("anesthesia.none");
  }
}

export function settingLabel(t: EndoscopyTranslator, value: string): string {
  switch (value) {
    case "office":
      return t("setting.office");
    case "ot":
      return t("setting.ot");
    default:
      return t("setting.office");
  }
}

export function toleranceLabel(t: EndoscopyTranslator, value: string): string {
  switch (value) {
    case "":
      return t("tolerance.unset");
    case "well_tolerated":
      return t("tolerance.wellTolerated");
    case "mild_discomfort":
      return t("tolerance.mildDiscomfort");
    case "moderate_discomfort":
      return t("tolerance.moderateDiscomfort");
    case "poorly_tolerated":
      return t("tolerance.poorlyTolerated");
    case "aborted":
      return t("tolerance.aborted");
    default:
      return t("tolerance.unset");
  }
}

export function lateralityLabel(t: EndoscopyTranslator, value: string): string {
  switch (value) {
    case "bilateral":
      return t("laterality.bilateral");
    case "right":
      return t("laterality.right");
    case "left":
      return t("laterality.left");
    case "midline":
      return t("laterality.midline");
    case "na":
      return t("laterality.na");
    default:
      return t("laterality.na");
  }
}

export function structureStatusLabel(
  t: EndoscopyTranslator,
  status: StructureStatus | string | null,
): string {
  switch (status) {
    case "unset":
    case null:
      return t("status.unset");
    case "normal":
      return t("status.normal");
    case "abnormal":
      return t("status.abnormal");
    case "not_examined":
      return t("status.notExamined");
    case "unknown":
      return t("status.unknown");
    default:
      return t("status.unset");
  }
}

export function lkItemLabel(t: EndoscopyTranslator, item: LkItem): string {
  switch (item) {
    case "polyps":
      return t("scores.items.polyps");
    case "edema":
      return t("scores.items.edema");
    case "discharge":
      return t("scores.items.discharge");
    case "scarring":
      return t("scores.items.scarring");
    case "crusting":
      return t("scores.items.crusting");
    default: {
      const _exhaustive: never = item;
      return _exhaustive;
    }
  }
}

export function polypScaleLabel(t: EndoscopyTranslator, scale: string): string {
  switch (scale) {
    case "meltzer":
      return t("scores.scales.meltzer");
    case "lildholdt":
      return t("scores.scales.lildholdt");
    default:
      return t("scores.scales.unknown");
  }
}

export function recordStatusLabel(
  t: EndoscopyTranslator,
  status: string,
): string {
  switch (status) {
    case "draft":
      return t("recordStatus.draft");
    case "signed":
      return t("recordStatus.signed");
    case "amended":
      return t("recordStatus.amended");
    default:
      return t("recordStatus.other");
  }
}

export function scoreCodeLabel(t: EndoscopyTranslator, code: string): string {
  switch (code) {
    case "endoscopy.lund_kennedy":
      return t("scores.lundKennedy");
    case "endoscopy.modified_lund_kennedy":
      return t("scores.modified");
    case "endoscopy.polyp_grade":
      return t("scores.polypGrade");
    case "endoscopy.adenoid_obstruction":
      return t("scores.adenoid");
    default:
      return t("scores.other");
  }
}

export function validationLabel(
  t: EndoscopyTranslator,
  issue: DraftIssue,
): string {
  switch (issue) {
    case "lk":
      return t("validation.lk");
    case "polyp":
      return t("validation.polyp");
    case "adenoid":
      return t("validation.adenoid");
    case "finding":
      return t("validation.finding");
    case "performedAt":
      return t("validation.performedAt");
    default: {
      const _exhaustive: never = issue;
      return _exhaustive;
    }
  }
}

export function comparisonChangeLabel(
  t: EndoscopyTranslator,
  change: "changed" | "unchanged" | "not_recorded",
): string {
  switch (change) {
    case "changed":
      return t("comparison.changed");
    case "unchanged":
      return t("comparison.unchanged");
    case "not_recorded":
      return t("comparison.notRecorded");
    default: {
      const _exhaustive: never = change;
      return _exhaustive;
    }
  }
}
