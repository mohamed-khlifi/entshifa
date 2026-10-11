import type { useTranslations } from "next-intl";

import type { DraftIssue, GrbasItem, RfsItem, StructureStatus } from "./draft";

export type LaryngoscopyTranslator = ReturnType<
  typeof useTranslations<"laryngoscopy">
>;

export function scopeLabel(t: LaryngoscopyTranslator, value: string): string {
  switch (value) {
    case "flexible_fiberoptic":
      return t("scope.flexibleFiberoptic");
    case "flexible_distal_chip":
      return t("scope.flexibleDistalChip");
    case "rigid_70":
      return t("scope.rigid70");
    case "rigid_90":
      return t("scope.rigid90");
    default:
      return t("scope.flexibleFiberoptic");
  }
}

export function anesthesiaLabel(
  t: LaryngoscopyTranslator,
  value: string,
): string {
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

export function settingLabel(t: LaryngoscopyTranslator, value: string): string {
  switch (value) {
    case "office":
      return t("setting.office");
    case "ot":
      return t("setting.ot");
    default:
      return t("setting.office");
  }
}

export function toleranceLabel(
  t: LaryngoscopyTranslator,
  value: string,
): string {
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

export function lateralityLabel(
  t: LaryngoscopyTranslator,
  value: string,
): string {
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

export function mobilityLabel(
  t: LaryngoscopyTranslator,
  value: string,
): string {
  switch (value) {
    case "normal":
      return t("mobility.normal");
    case "hypomobile":
      return t("mobility.hypomobile");
    case "immobile":
      return t("mobility.immobile");
    case "paradoxical":
      return t("mobility.paradoxical");
    default:
      return t("mobility.normal");
  }
}

export function positionLabel(
  t: LaryngoscopyTranslator,
  value: string,
): string {
  switch (value) {
    case "":
      return t("position.unset");
    case "median":
      return t("position.median");
    case "paramedian":
      return t("position.paramedian");
    case "intermediate":
      return t("position.intermediate");
    case "lateral":
      return t("position.lateral");
    default:
      return t("position.unset");
  }
}

export function glotticLabel(t: LaryngoscopyTranslator, value: string): string {
  switch (value) {
    case "complete":
      return t("glottic.complete");
    case "anterior_gap":
      return t("glottic.anteriorGap");
    case "posterior_gap":
      return t("glottic.posteriorGap");
    case "spindle":
      return t("glottic.spindle");
    case "hourglass":
      return t("glottic.hourglass");
    case "irregular":
      return t("glottic.irregular");
    case "incomplete":
      return t("glottic.incomplete");
    default:
      return t("glottic.complete");
  }
}

export function supraglotticLabel(
  t: LaryngoscopyTranslator,
  value: string,
): string {
  switch (value) {
    case "":
      return t("supraglottic.unset");
    case "none":
      return t("supraglottic.none");
    case "anteroposterior":
      return t("supraglottic.anteroposterior");
    case "mediolateral":
      return t("supraglottic.mediolateral");
    case "sphincteric":
      return t("supraglottic.sphincteric");
    default:
      return t("supraglottic.unset");
  }
}

export function structureStatusLabel(
  t: LaryngoscopyTranslator,
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

export function recordStatusLabel(
  t: LaryngoscopyTranslator,
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

export function rfsItemLabel(t: LaryngoscopyTranslator, item: RfsItem): string {
  switch (item) {
    case "subglotticEdema":
      return t("scores.items.subglotticEdema");
    case "ventricularObliteration":
      return t("scores.items.ventricularObliteration");
    case "erythema":
      return t("scores.items.erythema");
    case "vocalFoldEdema":
      return t("scores.items.vocalFoldEdema");
    case "diffuseLaryngealEdema":
      return t("scores.items.diffuseLaryngealEdema");
    case "posteriorCommissureHypertrophy":
      return t("scores.items.posteriorCommissureHypertrophy");
    case "granuloma":
      return t("scores.items.granuloma");
    case "thickEndolaryngealMucus":
      return t("scores.items.thickEndolaryngealMucus");
    default: {
      const _exhaustive: never = item;
      return _exhaustive;
    }
  }
}

export function grbasItemLabel(
  t: LaryngoscopyTranslator,
  item: GrbasItem,
): string {
  switch (item) {
    case "grade":
      return t("scores.items.grade");
    case "roughness":
      return t("scores.items.roughness");
    case "breathiness":
      return t("scores.items.breathiness");
    case "asthenia":
      return t("scores.items.asthenia");
    case "strain":
      return t("scores.items.strain");
    default: {
      const _exhaustive: never = item;
      return _exhaustive;
    }
  }
}

export function scoreCodeLabel(
  t: LaryngoscopyTranslator,
  code: string,
): string {
  switch (code) {
    case "laryngoscopy.reflux_finding_score":
      return t("scores.rfs");
    case "laryngoscopy.grbas":
      return t("scores.grbas");
    case "laryngoscopy.penetration_aspiration":
      return t("scores.pas");
    default:
      return t("scores.other");
  }
}

export function validationLabel(
  t: LaryngoscopyTranslator,
  issue: DraftIssue,
): string {
  switch (issue) {
    case "finding":
      return t("validation.finding");
    case "performedAt":
      return t("validation.performedAt");
    case "position":
      return t("validation.position");
    case "reinke":
      return t("validation.reinke");
    case "rfs":
      return t("validation.rfs");
    case "grbas":
      return t("validation.grbas");
    case "fees":
      return t("validation.fees");
    case "strobe":
      return t("validation.strobe");
    default: {
      const _exhaustive: never = issue;
      return _exhaustive;
    }
  }
}

export function comparisonChangeLabel(
  t: LaryngoscopyTranslator,
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

export function strobeChoiceLabel(
  t: LaryngoscopyTranslator,
  field: string,
  value: string,
): string {
  if (value === "") {
    return t("strobe.optionalUnset");
  }
  switch (value) {
    case "symmetric":
      return t("strobe.symmetric");
    case "asymmetric":
      return t("strobe.asymmetric");
    case "regular":
      return t("strobe.regular");
    case "irregular":
      return t("strobe.irregular");
    case "normal":
      return field === "phaseClosure"
        ? t("strobe.phaseNormal")
        : t("strobe.normal");
    case "reduced":
      return t("strobe.reduced");
    case "absent":
      return t("strobe.absent");
    case "predominantly_open":
      return t("strobe.predominantlyOpen");
    case "predominantly_closed":
      return t("strobe.predominantlyClosed");
    case "always_open":
      return t("strobe.alwaysOpen");
    case "on_plane":
      return t("strobe.onPlane");
    case "off_plane_right_lower":
      return t("strobe.offPlaneRight");
    case "off_plane_left_lower":
      return t("strobe.offPlaneLeft");
    case "none":
      return t("strobe.none");
    case "right":
      return t("strobe.right");
    case "left":
      return t("strobe.left");
    case "bilateral":
      return t("strobe.bilateral");
    default:
      return t("strobe.optionalUnset");
  }
}
