import { apiFetch } from "@/lib/api/client";
import type {
  CalculationRead,
  DrugRead,
  FormularyEntryRead,
  PageSchemaDrugRead,
  PageSchemaEncounterRead,
  PageSchemaFormularyEntryRead,
  PageSchemaPrescriptionRead,
  PageSchemaPrescriptionTemplateRead,
  PediatricDoseRequest,
  PrescriptionCreate,
  PrescriptionRead,
  PrescriptionTemplateCreate,
  PrescriptionTemplateRead,
  PrescriptionUpdate,
  SafetyAlertRead,
  SafetyCheckRequest,
  TaperRequest,
} from "@/lib/api/generated";

type Scope = { locale: string; clinicPublicId: string };

function pageQuery(q: string | undefined, limit: number): string {
  const search = new URLSearchParams({ limit: String(limit), offset: "0" });
  if (q && q.trim().length > 0) {
    search.set("q", q.trim());
  }
  return search.toString();
}

export function searchDrugs(
  scope: Scope,
  q: string,
): Promise<PageSchemaDrugRead> {
  return apiFetch<PageSchemaDrugRead>(
    `/api/v1/drugs?${pageQuery(q, 25)}`,
    scope,
  );
}

export function listFormulary(
  scope: Scope,
  q: string,
): Promise<PageSchemaFormularyEntryRead> {
  return apiFetch<PageSchemaFormularyEntryRead>(
    `/api/v1/formulary?${pageQuery(q, 25)}`,
    scope,
  );
}

export function listPrescriptionTemplates(
  scope: Scope,
): Promise<PageSchemaPrescriptionTemplateRead> {
  return apiFetch<PageSchemaPrescriptionTemplateRead>(
    "/api/v1/prescription-templates?limit=100&offset=0",
    scope,
  );
}

export function createPrescriptionTemplate(
  scope: Scope,
  body: PrescriptionTemplateCreate,
): Promise<PrescriptionTemplateRead> {
  return apiFetch<PrescriptionTemplateRead>("/api/v1/prescription-templates", {
    ...scope,
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function listPatientPrescriptions(
  scope: Scope,
  patientId: string,
): Promise<PageSchemaPrescriptionRead> {
  return apiFetch<PageSchemaPrescriptionRead>(
    `/api/v1/patients/${patientId}/prescriptions?limit=50&offset=0`,
    scope,
  );
}

export function createPrescription(
  scope: Scope,
  patientId: string,
  body: PrescriptionCreate,
  idempotencyKey: string,
): Promise<PrescriptionRead> {
  return apiFetch<PrescriptionRead>(
    `/api/v1/patients/${patientId}/prescriptions`,
    {
      ...scope,
      method: "POST",
      body: JSON.stringify(body),
      headers: { "Idempotency-Key": idempotencyKey },
    },
  );
}

export function updatePrescription(
  scope: Scope,
  prescriptionId: string,
  body: PrescriptionUpdate,
): Promise<PrescriptionRead> {
  return apiFetch<PrescriptionRead>(`/api/v1/prescriptions/${prescriptionId}`, {
    ...scope,
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

export function issuePrescription(
  scope: Scope,
  prescriptionId: string,
): Promise<PrescriptionRead> {
  return apiFetch<PrescriptionRead>(
    `/api/v1/prescriptions/${prescriptionId}/issue`,
    { ...scope, method: "POST" },
  );
}

export function cancelPrescription(
  scope: Scope,
  prescriptionId: string,
): Promise<PrescriptionRead> {
  return apiFetch<PrescriptionRead>(
    `/api/v1/prescriptions/${prescriptionId}/cancel`,
    { ...scope, method: "POST" },
  );
}

export function checkPrescriptionSafety(
  scope: Scope,
  patientId: string,
  body: SafetyCheckRequest,
): Promise<SafetyAlertRead[]> {
  return apiFetch<SafetyAlertRead[]>(
    `/api/v1/patients/${patientId}/prescriptions/check-safety`,
    { ...scope, method: "POST", body: JSON.stringify(body) },
  );
}

export function calculatePediatricDose(
  scope: Scope,
  patientId: string,
  body: PediatricDoseRequest,
): Promise<CalculationRead> {
  return apiFetch<CalculationRead>(
    `/api/v1/patients/${patientId}/prescriptions/calculate-dose`,
    { ...scope, method: "POST", body: JSON.stringify(body) },
  );
}

export function generatePrescriptionTaper(
  scope: Scope,
  patientId: string,
  body: TaperRequest,
): Promise<CalculationRead> {
  return apiFetch<CalculationRead>(
    `/api/v1/patients/${patientId}/prescriptions/generate-taper`,
    { ...scope, method: "POST", body: JSON.stringify(body) },
  );
}

export function listPatientEncounters(
  scope: Scope,
  patientId: string,
): Promise<PageSchemaEncounterRead> {
  return apiFetch<PageSchemaEncounterRead>(
    `/api/v1/patients/${patientId}/encounters?limit=25&offset=0`,
    scope,
  );
}

export type { DrugRead, FormularyEntryRead };
