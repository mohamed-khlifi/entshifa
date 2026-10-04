import { apiFetch } from "@/lib/api/client";
import type {
  ConceptSearchResponse,
  DiagnosisRead,
  PageSchemaDiagnosisFavoriteRead,
  EncounterAddendumCreate,
  EncounterCreate,
  EncounterPatch,
  EncounterRead,
  EncounterSign,
  EncounterTemplateRead,
  EncounterTemplateRouteRequest,
  NarrativeRenderRead,
  NarrativeRenderRequest,
  ObservationBatchCreate,
  ObservationRead,
  PageSchemaEncounterRead,
  PageSchemaSiteRead,
  PatientProblemCreate,
  PatientProblemRead,
  ValueSetRead,
} from "@/lib/api/generated";

type Scope = { locale: string; clinicPublicId: string };

export function fetchCockpitSites(scope: Scope): Promise<PageSchemaSiteRead> {
  return apiFetch<PageSchemaSiteRead>("/api/v1/sites?limit=20&offset=0", scope);
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

export function createEncounter(
  body: EncounterCreate,
  scope: Scope,
): Promise<EncounterRead> {
  return apiFetch<EncounterRead>("/api/v1/encounters", {
    ...scope,
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function patchEncounter(
  encounterId: string,
  body: EncounterPatch,
  scope: Scope,
): Promise<EncounterRead> {
  return apiFetch<EncounterRead>(`/api/v1/encounters/${encounterId}`, {
    ...scope,
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

export function signEncounter(
  encounterId: string,
  body: EncounterSign,
  scope: Scope,
): Promise<EncounterRead> {
  return apiFetch<EncounterRead>(`/api/v1/encounters/${encounterId}/sign`, {
    ...scope,
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function addEncounterAddendum(
  encounterId: string,
  body: EncounterAddendumCreate,
  scope: Scope,
): Promise<EncounterRead> {
  return apiFetch<EncounterRead>(`/api/v1/encounters/${encounterId}/addenda`, {
    ...scope,
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function routeEncounterTemplate(
  body: EncounterTemplateRouteRequest,
  scope: Scope,
): Promise<EncounterTemplateRead> {
  return apiFetch<EncounterTemplateRead>("/api/v1/encounter-templates/route", {
    ...scope,
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function fetchComplaintValueSet(scope: Scope): Promise<ValueSetRead> {
  const params = new URLSearchParams({ locale: scope.locale });
  return apiFetch<ValueSetRead>(
    `/api/v1/terminology/value-sets/${encodeURIComponent("complaints.ent")}?${params}`,
    scope,
  );
}

export function fetchExamValueSet(
  code: string,
  scope: Scope,
): Promise<ValueSetRead> {
  const params = new URLSearchParams({ locale: scope.locale });
  return apiFetch<ValueSetRead>(
    `/api/v1/terminology/value-sets/${encodeURIComponent(code)}?${params}`,
    scope,
  );
}

export function searchDiagnoses(
  query: string,
  scope: Scope,
): Promise<ConceptSearchResponse> {
  const params = new URLSearchParams({
    q: query,
    locale: scope.locale,
    kind: "diagnosis",
  });
  return apiFetch<ConceptSearchResponse>(
    `/api/v1/terminology/concepts/search?${params}`,
    scope,
  );
}

export function renderVisitNarrative(
  body: NarrativeRenderRequest,
  scope: Scope,
): Promise<NarrativeRenderRead> {
  return apiFetch<NarrativeRenderRead>("/api/v1/narrative/render", {
    ...scope,
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function recordVisitObservations(
  patientId: string,
  body: ObservationBatchCreate,
  scope: Scope,
): Promise<ObservationRead[]> {
  return apiFetch<ObservationRead[]>(
    `/api/v1/observations/patient/${patientId}/batch`,
    { ...scope, method: "POST", body: JSON.stringify(body) },
  );
}

export function promoteDiagnosis(
  encounterId: string,
  diagnosisId: string,
  scope: Scope,
): Promise<DiagnosisRead> {
  return apiFetch<DiagnosisRead>(
    `/api/v1/encounters/${encounterId}/diagnoses/${diagnosisId}/promote`,
    { ...scope, method: "POST" },
  );
}

export function listDiagnosisFavorites(
  scope: Scope,
): Promise<PageSchemaDiagnosisFavoriteRead> {
  return apiFetch<PageSchemaDiagnosisFavoriteRead>(
    "/api/v1/diagnoses/favorites",
    scope,
  );
}

export function replaceDiagnosisFavorites(
  conceptPublicIds: readonly string[],
  scope: Scope,
): Promise<PageSchemaDiagnosisFavoriteRead> {
  return apiFetch<PageSchemaDiagnosisFavoriteRead>(
    "/api/v1/diagnoses/favorites",
    {
      ...scope,
      method: "PUT",
      body: JSON.stringify({ conceptPublicIds }),
    },
  );
}

export function addProblem(
  patientId: string,
  body: PatientProblemCreate,
  scope: Scope,
  idempotencyKey: string,
): Promise<PatientProblemRead> {
  return apiFetch<PatientProblemRead>(
    `/api/v1/patients/${patientId}/problems`,
    {
      ...scope,
      method: "POST",
      body: JSON.stringify(body),
      headers: { "Idempotency-Key": idempotencyKey },
    },
  );
}
