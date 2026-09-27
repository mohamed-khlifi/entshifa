import { apiFetch } from "@/lib/api/client";
import type {
  ConceptDictionaryResponse,
  ConceptSearchResponse,
  PageSchemaPatientSummaryRead,
  ValueSetRead,
  PatientAllergyCreate,
  PatientCreate,
  PatientFlagCreate,
  PatientFlagUpdate,
  PatientHistoryCreate,
  PatientIdentifierCreate,
  PatientMedicationCreate,
  PatientProblemCreate,
  PatientRead,
  PatientUpdate,
} from "@/lib/api/generated";

export type PatientListParams = {
  search?: string;
  birthDate?: string;
  sex?: string;
  flagCode?: string;
  sort?: string;
  limit?: number;
  offset?: number;
};

type Scope = { locale: string; clinicPublicId: string };

function query(params: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === "") {
      continue;
    }
    search.set(key, String(value));
  }
  const text = search.toString();
  return text ? `?${text}` : "";
}

export function fetchPatients(
  scope: Scope,
  params: PatientListParams = {},
): Promise<PageSchemaPatientSummaryRead> {
  return apiFetch<PageSchemaPatientSummaryRead>(
    `/api/v1/patients${query({
      search: params.search,
      birth_date: params.birthDate,
      sex: params.sex,
      flag_code: params.flagCode,
      sort: params.sort,
      limit: params.limit,
      offset: params.offset,
    })}`,
    scope,
  );
}

export function fetchPatient(
  patientId: string,
  scope: Scope,
): Promise<PatientRead> {
  return apiFetch<PatientRead>(`/api/v1/patients/${patientId}`, scope);
}

export function fetchPatientTimeline(
  patientId: string,
  scope: Scope,
): Promise<PageSchemaPatientSummaryRead> {
  return apiFetch<PageSchemaPatientSummaryRead>(
    `/api/v1/patients/${patientId}/timeline`,
    scope,
  );
}

export function createPatient(
  body: PatientCreate,
  scope: Scope,
  idempotencyKey: string,
): Promise<PatientRead> {
  return apiFetch<PatientRead>("/api/v1/patients", {
    ...scope,
    method: "POST",
    body: JSON.stringify(body),
    headers: { "Idempotency-Key": idempotencyKey },
  });
}

export function updatePatient(
  patientId: string,
  body: PatientUpdate,
  scope: Scope,
): Promise<PatientRead> {
  return apiFetch<PatientRead>(`/api/v1/patients/${patientId}`, {
    ...scope,
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

export function addPatientIdentifier(
  patientId: string,
  body: PatientIdentifierCreate,
  scope: Scope,
  idempotencyKey: string,
): Promise<unknown> {
  return apiFetch(`/api/v1/patients/${patientId}/identifiers`, {
    ...scope,
    method: "POST",
    body: JSON.stringify(body),
    headers: { "Idempotency-Key": idempotencyKey },
  });
}

export function addPatientAllergy(
  patientId: string,
  body: PatientAllergyCreate,
  scope: Scope,
  idempotencyKey: string,
): Promise<unknown> {
  return apiFetch(`/api/v1/patients/${patientId}/allergies`, {
    ...scope,
    method: "POST",
    body: JSON.stringify(body),
    headers: { "Idempotency-Key": idempotencyKey },
  });
}

export function addPatientMedication(
  patientId: string,
  body: PatientMedicationCreate,
  scope: Scope,
  idempotencyKey: string,
): Promise<unknown> {
  return apiFetch(`/api/v1/patients/${patientId}/medications`, {
    ...scope,
    method: "POST",
    body: JSON.stringify(body),
    headers: { "Idempotency-Key": idempotencyKey },
  });
}

export function addPatientFlag(
  patientId: string,
  body: PatientFlagCreate,
  scope: Scope,
  idempotencyKey: string,
): Promise<unknown> {
  return apiFetch(`/api/v1/patients/${patientId}/flags`, {
    ...scope,
    method: "POST",
    body: JSON.stringify(body),
    headers: { "Idempotency-Key": idempotencyKey },
  });
}

export function updatePatientFlag(
  patientId: string,
  flagId: string,
  body: PatientFlagUpdate,
  scope: Scope,
): Promise<unknown> {
  return apiFetch(`/api/v1/patients/${patientId}/flags/${flagId}`, {
    ...scope,
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

export function addPatientProblem(
  patientId: string,
  body: PatientProblemCreate,
  scope: Scope,
  idempotencyKey: string,
): Promise<unknown> {
  return apiFetch(`/api/v1/patients/${patientId}/problems`, {
    ...scope,
    method: "POST",
    body: JSON.stringify(body),
    headers: { "Idempotency-Key": idempotencyKey },
  });
}

export function addPatientHistory(
  patientId: string,
  body: PatientHistoryCreate,
  scope: Scope,
  idempotencyKey: string,
): Promise<unknown> {
  return apiFetch(`/api/v1/patients/${patientId}/history`, {
    ...scope,
    method: "POST",
    body: JSON.stringify(body),
    headers: { "Idempotency-Key": idempotencyKey },
  });
}

export function searchConcepts(
  scope: Scope,
  params: { q: string; kind?: string },
): Promise<ConceptSearchResponse> {
  return apiFetch<ConceptSearchResponse>(
    `/api/v1/terminology/concepts/search${query({
      q: params.q,
      locale: scope.locale,
      kind: params.kind,
    })}`,
    scope,
  );
}

export function fetchConceptDictionary(
  scope: Scope,
  kinds?: string,
): Promise<ConceptDictionaryResponse> {
  return apiFetch<ConceptDictionaryResponse>(
    `/api/v1/terminology/dictionary${query({
      locale: scope.locale,
      kinds,
    })}`,
    scope,
  );
}

export function fetchValueSet(
  code: string,
  scope: Scope,
): Promise<ValueSetRead> {
  return apiFetch<ValueSetRead>(
    `/api/v1/terminology/value-sets/${encodeURIComponent(code)}${query({
      locale: scope.locale,
    })}`,
    scope,
  );
}

export function deletePatientIdentifier(
  patientId: string,
  identifierId: string,
  scope: Scope,
): Promise<void> {
  return apiFetch<void>(
    `/api/v1/patients/${patientId}/identifiers/${identifierId}`,
    { ...scope, method: "DELETE" },
  );
}

export function deletePatientAllergy(
  patientId: string,
  allergyId: string,
  scope: Scope,
): Promise<void> {
  return apiFetch<void>(
    `/api/v1/patients/${patientId}/allergies/${allergyId}`,
    { ...scope, method: "DELETE" },
  );
}

export function deletePatientMedication(
  patientId: string,
  medicationId: string,
  scope: Scope,
): Promise<void> {
  return apiFetch<void>(
    `/api/v1/patients/${patientId}/medications/${medicationId}`,
    { ...scope, method: "DELETE" },
  );
}

export function deletePatientProblem(
  patientId: string,
  problemId: string,
  scope: Scope,
): Promise<void> {
  return apiFetch<void>(
    `/api/v1/patients/${patientId}/problems/${problemId}`,
    { ...scope, method: "DELETE" },
  );
}

export function deletePatientHistory(
  patientId: string,
  historyId: string,
  scope: Scope,
): Promise<void> {
  return apiFetch<void>(
    `/api/v1/patients/${patientId}/history/${historyId}`,
    { ...scope, method: "DELETE" },
  );
}
