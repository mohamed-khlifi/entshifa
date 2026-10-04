import type { MapState } from "@/lib/anatomy/types";

import type { SelectedComplaint } from "./complaints";
import type { PlanItemDraft } from "./plan-items";
import type { RedFlagId } from "./red-flags";
import type { CockpitFormValues } from "../schemas/cockpit.schema";

export type DiagnosisLaterality = "right" | "left" | "bilateral" | "na";
export type DiagnosisStatus = "suspected" | "confirmed" | "ruled_out";

export type DiagnosisDraft = {
  conceptPublicId: string;
  display: string;
  laterality: DiagnosisLaterality;
  status: DiagnosisStatus;
  promoted: boolean;
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

export function problemStatusFor(
  status: DiagnosisStatus,
): "active" | "suspected" | "ruled_out" {
  if (status === "confirmed") {
    return "active";
  }
  return status;
}
