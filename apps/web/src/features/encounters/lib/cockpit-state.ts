import type { MapState } from "@/lib/anatomy/types";

import type { SelectedComplaint } from "./complaints";
import type { PlanItemDraft } from "./plan-items";
import type { RedFlagId } from "./red-flags";
import type { CockpitFormValues } from "../schemas/cockpit.schema";

export type DiagnosisLaterality = "right" | "left" | "bilateral" | "na";
export type DiagnosisStatus = "suspected" | "confirmed" | "ruled_out";

export type DiagnosisDraft = {
  publicId: string | null;
  conceptPublicId: string;
  display: string;
  laterality: DiagnosisLaterality;
  status: DiagnosisStatus;
  promoted: boolean;
  source: "clinician" | "copy_forward";
  copied: boolean;
  isPrimary: boolean;
  sortOrder: number;
};

export type CockpitLocalState = {
  complaints: SelectedComplaint[];
  redFlags: RedFlagId[];
  diagnoses: DiagnosisDraft[];
  planItems: PlanItemDraft[];
  form: CockpitFormValues;
  examByMap: Record<string, MapState>;
  expandedMaps: string[];
};

const DIAGNOSIS_SIDES: readonly DiagnosisLaterality[] = [
  "right",
  "left",
  "bilateral",
  "na",
];
const DIAGNOSIS_STATUSES: readonly DiagnosisStatus[] = [
  "suspected",
  "confirmed",
  "ruled_out",
];

export function problemStatusFor(
  status: DiagnosisStatus,
): "active" | "suspected" | "ruled_out" {
  if (status === "confirmed") {
    return "active";
  }
  return status;
}

export function diagnosisIdentity(
  row: Pick<DiagnosisDraft, "conceptPublicId" | "laterality">,
): string {
  return `${row.conceptPublicId}:${row.laterality}`;
}

export function clinicianDiagnosis(
  conceptPublicId: string,
  display: string,
): DiagnosisDraft {
  return {
    publicId: null,
    conceptPublicId,
    display,
    laterality: "na",
    status: "suspected",
    promoted: false,
    source: "clinician",
    copied: false,
    isPrimary: false,
    sortOrder: 0,
  };
}

export function normalizeStoredDiagnoses(
  rows: readonly Partial<DiagnosisDraft>[] | undefined,
): DiagnosisDraft[] {
  return (rows ?? []).flatMap((row, index) => {
    if (!row.conceptPublicId || !row.display) {
      return [];
    }
    const laterality =
      DIAGNOSIS_SIDES.find((side) => side === row.laterality) ?? "na";
    const status =
      DIAGNOSIS_STATUSES.find((value) => value === row.status) ?? "suspected";
    const copied = row.source === "copy_forward" || row.copied === true;
    return [
      {
        publicId: row.publicId ?? null,
        conceptPublicId: row.conceptPublicId,
        display: row.display,
        laterality,
        status,
        promoted: row.promoted === true,
        source: copied ? "copy_forward" : "clinician",
        copied,
        isPrimary: row.isPrimary === true,
        sortOrder: typeof row.sortOrder === "number" ? row.sortOrder : index,
      },
    ];
  });
}

export function appendDiagnosis(
  rows: readonly DiagnosisDraft[],
  row: DiagnosisDraft,
): DiagnosisDraft[] {
  if (rows.some((item) => diagnosisIdentity(item) === diagnosisIdentity(row))) {
    return [...rows];
  }
  return [
    ...rows,
    {
      ...row,
      isPrimary: rows.length === 0,
      sortOrder: rows.length,
    },
  ];
}

export function changeDiagnosis(
  rows: readonly DiagnosisDraft[],
  conceptPublicId: string,
  laterality: DiagnosisLaterality,
  patch: Partial<Pick<DiagnosisDraft, "laterality" | "status">>,
): DiagnosisDraft[] | null {
  const currentKey = `${conceptPublicId}:${laterality}`;
  const current = rows.find((row) => diagnosisIdentity(row) === currentKey);
  if (!current) {
    return [...rows];
  }
  const nextLaterality = patch.laterality ?? laterality;
  const nextStatus = patch.status ?? current.status;
  if (nextLaterality === current.laterality && nextStatus === current.status) {
    return [...rows];
  }
  if (
    nextLaterality !== laterality &&
    rows.some(
      (item) =>
        item.conceptPublicId === conceptPublicId &&
        item.laterality === nextLaterality,
    )
  ) {
    return null;
  }
  return rows.map((row) => {
    if (diagnosisIdentity(row) !== currentKey) {
      return row;
    }
    return {
      ...row,
      laterality: nextLaterality,
      status: nextStatus,
      source: "clinician",
      copied: false,
    };
  });
}

export function removeDiagnosis(
  rows: readonly DiagnosisDraft[],
  conceptPublicId: string,
  laterality: DiagnosisLaterality,
): DiagnosisDraft[] {
  const key = `${conceptPublicId}:${laterality}`;
  const remaining = rows.filter((row) => diagnosisIdentity(row) !== key);
  const hasPrimary = remaining.some((row) => row.isPrimary);
  return remaining.map((row, index) => ({
    ...row,
    sortOrder: index,
    isPrimary: hasPrimary ? row.isPrimary : index === 0,
  }));
}
