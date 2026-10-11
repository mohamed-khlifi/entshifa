import { apiFetch } from "@/lib/api/client";
import type {
  EarDeviceRead,
  EarDeviceStatusUpdate,
  OtologyCreate,
  OtologyExamRead,
  OtologyUpdate,
  PageSchemaEarDeviceRead,
  PageSchemaOtologyExamRead,
  ProcedureSign,
  ValueSetRead,
} from "@/lib/api/generated";

type Scope = { locale: string; clinicPublicId: string };

export function fetchPatientOtologyExams(
  patientId: string,
  scope: Scope,
): Promise<PageSchemaOtologyExamRead> {
  return apiFetch<PageSchemaOtologyExamRead>(
    `/api/v1/patients/${patientId}/otology-exams?limit=50&offset=0`,
    scope,
  );
}

export function createOtologyExam(
  body: OtologyCreate,
  scope: Scope,
): Promise<OtologyExamRead> {
  return apiFetch<OtologyExamRead>("/api/v1/otology-exams", {
    ...scope,
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function updateOtologyExam(
  examId: string,
  body: OtologyUpdate,
  scope: Scope,
): Promise<OtologyExamRead> {
  return apiFetch<OtologyExamRead>(`/api/v1/otology-exams/${examId}`, {
    ...scope,
    method: "PUT",
    body: JSON.stringify(body),
  });
}

export function fetchPatientEarDevices(
  patientId: string,
  scope: Scope,
): Promise<PageSchemaEarDeviceRead> {
  return apiFetch<PageSchemaEarDeviceRead>(
    `/api/v1/patients/${patientId}/ear-devices?limit=50&offset=0`,
    scope,
  );
}

export function updateEarDeviceStatus(
  deviceId: string,
  body: EarDeviceStatusUpdate,
  scope: Scope,
): Promise<EarDeviceRead> {
  return apiFetch<EarDeviceRead>(`/api/v1/ear-devices/${deviceId}`, {
    ...scope,
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

export function signOtologyProcedure(
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

export function fetchOtologyValueSet(
  code: string,
  scope: Scope,
): Promise<ValueSetRead> {
  const params = new URLSearchParams({ locale: scope.locale });
  return apiFetch<ValueSetRead>(
    `/api/v1/terminology/value-sets/${encodeURIComponent(code)}?${params}`,
    scope,
  );
}
