import { apiFetch } from "@/lib/api/client";
import type {
  OfficeProcedureCreate,
  OfficeProcedureRead,
  OfficeProcedureUpdate,
  PageSchemaOfficeProcedureRead,
  ProcedureSign,
} from "@/lib/api/generated";

type Scope = { locale: string; clinicPublicId: string };

export function fetchPatientOfficeProcedures(
  patientId: string,
  scope: Scope,
): Promise<PageSchemaOfficeProcedureRead> {
  return apiFetch<PageSchemaOfficeProcedureRead>(
    `/api/v1/patients/${patientId}/office-procedures?limit=50&offset=0`,
    scope,
  );
}

export function createOfficeProcedure(
  body: OfficeProcedureCreate,
  scope: Scope,
): Promise<OfficeProcedureRead> {
  return apiFetch<OfficeProcedureRead>("/api/v1/office-procedures", {
    ...scope,
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function updateOfficeProcedure(
  procedureId: string,
  body: OfficeProcedureUpdate,
  scope: Scope,
): Promise<OfficeProcedureRead> {
  return apiFetch<OfficeProcedureRead>(
    `/api/v1/office-procedures/${procedureId}`,
    {
      ...scope,
      method: "PUT",
      body: JSON.stringify(body),
    },
  );
}

export function signOfficeProcedure(
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
