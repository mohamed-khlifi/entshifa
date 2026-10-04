import { apiFetch } from "@/lib/api/client";
import type {
  EncounterRead,
  ExaminationSnapshotCreate,
  ExaminationSnapshotRead,
  NarrativeRenderRead,
  NarrativeRenderRequest,
  ObservationBatchCreate,
  ObservationRead,
  PageSchemaEncounterRead,
  ValueSetRead,
} from "@/lib/api/generated";

type Scope = { locale: string; clinicPublicId: string };

export function fetchPatientEncounters(
  patientId: string,
  scope: Scope,
): Promise<PageSchemaEncounterRead> {
  return apiFetch<PageSchemaEncounterRead>(
    `/api/v1/patients/${patientId}/encounters?limit=25&offset=0`,
    scope,
  );
}

export function recordObservations(
  patientId: string,
  body: ObservationBatchCreate,
  scope: Scope,
): Promise<ObservationRead[]> {
  return apiFetch<ObservationRead[]>(
    `/api/v1/observations/patient/${patientId}/batch`,
    { ...scope, method: "POST", body: JSON.stringify(body) },
  );
}

export function renderNarrative(
  body: NarrativeRenderRequest,
  scope: Scope,
): Promise<NarrativeRenderRead> {
  return apiFetch<NarrativeRenderRead>("/api/v1/narrative/render", {
    ...scope,
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function recordExaminationSnapshot(
  patientId: string,
  body: ExaminationSnapshotCreate,
  scope: Scope,
): Promise<ExaminationSnapshotRead> {
  return apiFetch<ExaminationSnapshotRead>(
    `/api/v1/observations/patient/${patientId}/snapshots`,
    { ...scope, method: "POST", body: JSON.stringify(body) },
  );
}

export function fetchExaminationValueSet(
  code: string,
  scope: Scope,
): Promise<ValueSetRead> {
  const params = new URLSearchParams({ locale: scope.locale });
  return apiFetch<ValueSetRead>(
    `/api/v1/terminology/value-sets/${encodeURIComponent(code)}?${params}`,
    scope,
  );
}

export type { EncounterRead };
