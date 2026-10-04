import type {
  DiagnosisRead,
  DiagnosisWrite,
  EncounterComplaintWrite,
  EncounterPatch,
} from "@/lib/api/generated";

import type { DiagnosisDraft } from "./cockpit-state";

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
  diagnoses: DiagnosisDraft[];
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
  if (diagnosisKey(baseline.diagnoses) !== diagnosisKey(current.diagnoses)) {
    patch.diagnoses = toDiagnosisWrites(current.diagnoses);
    dirty = true;
  }
  return dirty ? patch : null;
}

function diagnosisKey(items: readonly DiagnosisDraft[] | undefined): string {
  return JSON.stringify(
    [...(items ?? [])]
      .map((item) => ({
        conceptPublicId: item.conceptPublicId,
        isPrimary: item.isPrimary,
        laterality: item.laterality,
        note: null,
        onsetDate: null,
        sortOrder: item.sortOrder,
        source: item.source,
        status: item.status,
      }))
      .sort((left, right) =>
        `${left.sortOrder}:${left.conceptPublicId}:${left.laterality}`.localeCompare(
          `${right.sortOrder}:${right.conceptPublicId}:${right.laterality}`,
        ),
      ),
  );
}

export function toDiagnosisWrites(
  items: readonly DiagnosisDraft[],
): DiagnosisWrite[] {
  const hasPrimary = items.some((item) => item.isPrimary);
  return items.map((item, index) => ({
    conceptPublicId: item.conceptPublicId,
    isPrimary: item.isPrimary || (!hasPrimary && index === 0),
    laterality: item.laterality,
    sortOrder: item.sortOrder,
    source: item.copied ? "copy_forward" : "clinician",
    status: item.status,
  }));
}

const DIAGNOSIS_SIDES = ["right", "left", "bilateral", "na"] as const;
const DIAGNOSIS_STATUSES = ["suspected", "confirmed", "ruled_out"] as const;

export function diagnosesFromRead(
  rows: readonly DiagnosisRead[] | undefined,
): DiagnosisDraft[] {
  return (rows ?? []).map((row, index) => {
    const laterality = DIAGNOSIS_SIDES.find((side) => side === row.laterality);
    const status = DIAGNOSIS_STATUSES.find((value) => value === row.status);
    const copied = row.source === "copy_forward";
    return {
      publicId: row.publicId,
      conceptPublicId: row.concept.conceptId,
      display: row.concept.display || row.concept.code || row.concept.conceptId,
      laterality: laterality ?? "na",
      status: status ?? "suspected",
      promoted: Boolean(row.promotedProblemPublicId),
      source: copied ? "copy_forward" : "clinician",
      copied,
      isPrimary: row.isPrimary,
      sortOrder: row.sortOrder ?? index,
    };
  });
}

export function mergeDiagnosisIdentity(
  local: readonly DiagnosisDraft[],
  remote: readonly DiagnosisRead[] | undefined,
): DiagnosisDraft[] {
  const saved = diagnosesFromRead(remote);
  return local.map((row) => {
    const match = saved.find(
      (item) =>
        item.conceptPublicId === row.conceptPublicId &&
        item.laterality === row.laterality,
    );
    if (!match) {
      return row;
    }
    return {
      ...row,
      publicId: match.publicId,
      promoted: row.promoted || match.promoted,
    };
  });
}
