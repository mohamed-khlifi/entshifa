import { apiFetch } from "@/lib/api/client";
import type {
  EncounterCopyForward,
  EncounterCreate,
  EncounterRead,
  ExaminationSnapshotCreate,
  ExaminationSnapshotRead,
  NarrativeRenderRead,
  NarrativeRenderRequest,
  ObservationBatchCreate,
  ObservationRead,
  PageSchemaEncounterRead,
  PageSchemaExaminationSnapshotRead,
  PageSchemaObservationRead,
  PageSchemaPatientProblemRead,
  PageSchemaSiteRead,
  ValueSetRead,
} from "@/lib/api/generated";

type Scope = { locale: string; clinicPublicId: string };

export function fetchExaminationSites(
  scope: Scope,
): Promise<PageSchemaSiteRead> {
  return apiFetch<PageSchemaSiteRead>("/api/v1/sites?limit=20&offset=0", scope);
}

export function createExaminationEncounter(
  body: EncounterCreate,
  scope: Scope,
): Promise<EncounterRead> {
  return apiFetch<EncounterRead>("/api/v1/encounters", {
    ...scope,
    method: "POST",
    body: JSON.stringify(body),
  });
}

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

export function copyEncounterForward(
  encounterId: string,
  body: EncounterCopyForward,
  scope: Scope,
): Promise<EncounterRead> {
  return apiFetch<EncounterRead>(
    `/api/v1/encounters/${encounterId}/copy-forward`,
    { ...scope, method: "POST", body: JSON.stringify(body) },
  );
}

export function fetchEncounterObservations(
  encounterId: string,
  scope: Scope,
): Promise<PageSchemaObservationRead> {
  return apiFetch<PageSchemaObservationRead>(
    `/api/v1/observations/encounter/${encounterId}?limit=100&offset=0`,
    scope,
  );
}

export function fetchExaminationSnapshots(
  patientId: string,
  scope: Scope,
): Promise<PageSchemaExaminationSnapshotRead> {
  return apiFetch<PageSchemaExaminationSnapshotRead>(
    `/api/v1/observations/patient/${patientId}/snapshots?limit=100&offset=0`,
    scope,
  );
}

export function fetchExaminationProblems(
  patientId: string,
  scope: Scope,
): Promise<PageSchemaPatientProblemRead> {
  return apiFetch<PageSchemaPatientProblemRead>(
    `/api/v1/patients/${patientId}/problems?limit=100&offset=0`,
    scope,
  );
}

export type CopyForwardChart = {
  encounter: EncounterRead;
  observations: PageSchemaObservationRead;
  snapshots: PageSchemaExaminationSnapshotRead;
};

export async function loadCopyForwardChart(
  patientId: string,
  sourceEncounterId: string,
  body: EncounterCopyForward,
  scope: Scope,
): Promise<CopyForwardChart> {
  const encounter = await copyEncounterForward(sourceEncounterId, body, scope);
  const [observations, snapshots] = await Promise.all([
    fetchEncounterObservations(sourceEncounterId, scope),
    fetchExaminationSnapshots(patientId, scope),
  ]);
  return { encounter, observations, snapshots };
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
