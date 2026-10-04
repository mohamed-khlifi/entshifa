import type {
  EncounterComplaintWrite,
  EncounterPatch,
} from "@/lib/api/generated";

import { emptyToNull } from "./clinical-note";

const LATERALITIES = ["right", "left", "bilateral", "midline", "na"] as const;

type Laterality = (typeof LATERALITIES)[number];

export type ComplaintSnapshot = {
  conceptCode: string;
  isPrimary: boolean;
  laterality: string | null;
  durationText: string | null;
  sortOrder: number;
};

export type EncounterFieldSnapshot = {
  chiefComplaintSummary: string | null;
  historyText: string | null;
  assessmentText: string | null;
  planText: string | null;
  complaints: ComplaintSnapshot[];
};

export function asLaterality(value: string | null): Laterality | null {
  if (value && LATERALITIES.includes(value as Laterality)) {
    return value as Laterality;
  }
  return null;
}

function complaintKey(items: readonly ComplaintSnapshot[]): string {
  return JSON.stringify(
    items.map((item) => ({
      conceptCode: item.conceptCode,
      durationText: item.durationText,
      isPrimary: item.isPrimary,
      laterality: item.laterality,
      sortOrder: item.sortOrder,
    })),
  );
}

export function toComplaintWrites(
  items: readonly ComplaintSnapshot[],
): EncounterComplaintWrite[] {
  return items.map((item) => ({
    conceptCode: item.conceptCode,
    durationText: item.durationText,
    isPrimary: item.isPrimary,
    laterality: asLaterality(item.laterality),
    sortOrder: item.sortOrder,
  }));
}

export function diffEncounterPatch(
  version: number,
  baseline: EncounterFieldSnapshot,
  current: EncounterFieldSnapshot,
): EncounterPatch | null {
  const patch: EncounterPatch = { version };
  let dirty = false;
  if (
    emptyToNull(baseline.chiefComplaintSummary) !==
    emptyToNull(current.chiefComplaintSummary)
  ) {
    patch.chiefComplaintSummary = emptyToNull(current.chiefComplaintSummary);
    dirty = true;
  }
  if (emptyToNull(baseline.historyText) !== emptyToNull(current.historyText)) {
    patch.historyText = emptyToNull(current.historyText);
    dirty = true;
  }
  if (
    emptyToNull(baseline.assessmentText) !== emptyToNull(current.assessmentText)
  ) {
    patch.assessmentText = emptyToNull(current.assessmentText);
    dirty = true;
  }
  if (emptyToNull(baseline.planText) !== emptyToNull(current.planText)) {
    patch.planText = emptyToNull(current.planText);
    dirty = true;
  }
  if (complaintKey(baseline.complaints) !== complaintKey(current.complaints)) {
    patch.complaints = toComplaintWrites(current.complaints);
    dirty = true;
  }
  return dirty ? patch : null;
}
