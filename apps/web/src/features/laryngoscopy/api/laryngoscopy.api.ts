import { apiFetch } from "@/lib/api/client";
import type {
  LaryngoscopyCreate,
  LaryngoscopyExamRead,
  LaryngoscopyUpdate,
  PageSchemaLaryngoscopyExamRead,
  ProcedureSign,
  ValueSetRead,
} from "@/lib/api/generated";

type Scope = { locale: string; clinicPublicId: string };

export function fetchPatientLaryngoscopies(
  patientId: string,
  scope: Scope,
): Promise<PageSchemaLaryngoscopyExamRead> {
  return apiFetch<PageSchemaLaryngoscopyExamRead>(
    `/api/v1/patients/${patientId}/laryngoscopies?limit=50&offset=0`,
    scope,
  );
}

export function createLaryngoscopyExam(
  body: LaryngoscopyCreate,
  scope: Scope,
): Promise<LaryngoscopyExamRead> {
  return apiFetch<LaryngoscopyExamRead>("/api/v1/laryngoscopies", {
    ...scope,
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function updateLaryngoscopyExam(
  examId: string,
  body: LaryngoscopyUpdate,
  scope: Scope,
): Promise<LaryngoscopyExamRead> {
  return apiFetch<LaryngoscopyExamRead>(`/api/v1/laryngoscopies/${examId}`, {
    ...scope,
    method: "PUT",
    body: JSON.stringify(body),
  });
}

export function signLaryngoscopyProcedure(
  procedureId: string,
  body: ProcedureSign,
  scope: Scope,
): Promise<void> {
  return apiFetch<void>(`/api/v1/procedures/${procedureId}/sign`, {
    ...scope,
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function fetchLaryngoscopyValueSet(
  code: string,
  scope: Scope,
): Promise<ValueSetRead> {
  const params = new URLSearchParams({ locale: scope.locale });
  return apiFetch<ValueSetRead>(
    `/api/v1/terminology/value-sets/${encodeURIComponent(code)}?${params}`,
    scope,
  );
}
