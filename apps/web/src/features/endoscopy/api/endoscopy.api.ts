import { apiFetch } from "@/lib/api/client";
import type {
  EndoscopyCreate,
  EndoscopyExamRead,
  EndoscopyUpdate,
  PageSchemaEndoscopyExamRead,
  ProcedureSign,
  ValueSetRead,
} from "@/lib/api/generated";

type Scope = { locale: string; clinicPublicId: string };

export function fetchPatientEndoscopies(
  patientId: string,
  scope: Scope,
): Promise<PageSchemaEndoscopyExamRead> {
  return apiFetch<PageSchemaEndoscopyExamRead>(
    `/api/v1/patients/${patientId}/endoscopies?limit=50&offset=0`,
    scope,
  );
}

export function createEndoscopyExam(
  body: EndoscopyCreate,
  scope: Scope,
): Promise<EndoscopyExamRead> {
  return apiFetch<EndoscopyExamRead>("/api/v1/endoscopies", {
    ...scope,
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function updateEndoscopyExam(
  examId: string,
  body: EndoscopyUpdate,
  scope: Scope,
): Promise<EndoscopyExamRead> {
  return apiFetch<EndoscopyExamRead>(`/api/v1/endoscopies/${examId}`, {
    ...scope,
    method: "PUT",
    body: JSON.stringify(body),
  });
}

export function signProcedure(
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

export function fetchEndoscopyValueSet(
  code: string,
  scope: Scope,
): Promise<ValueSetRead> {
  const params = new URLSearchParams({ locale: scope.locale });
  return apiFetch<ValueSetRead>(
    `/api/v1/terminology/value-sets/${encodeURIComponent(code)}?${params}`,
    scope,
  );
}
