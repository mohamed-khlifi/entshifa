import { apiFetch } from "@/lib/api/client";
import type {
  DocumentCreate,
  DocumentDownloadRead,
  DocumentFinalize,
  DocumentPreviewRead,
  DocumentRead,
  DocumentTemplateCreate,
  DocumentTemplateDetailRead,
  DocumentTemplatePreview,
  DocumentTemplateRead,
  DocumentTemplateVersionCreate,
  PageSchemaDocumentRead,
  PageSchemaDocumentTemplateRead,
} from "@/lib/api/generated";

type Scope = { locale: string; clinicPublicId: string };

export function fetchDocumentTemplates(
  scope: Scope,
): Promise<PageSchemaDocumentTemplateRead> {
  return apiFetch<PageSchemaDocumentTemplateRead>(
    "/api/v1/document-templates?limit=100",
    scope,
  );
}

export function fetchDocumentTemplate(
  scope: Scope,
  templateId: string,
): Promise<DocumentTemplateDetailRead> {
  return apiFetch<DocumentTemplateDetailRead>(
    `/api/v1/document-templates/${templateId}`,
    scope,
  );
}

export function createDocumentTemplate(
  scope: Scope,
  body: DocumentTemplateCreate,
): Promise<DocumentTemplateRead> {
  return apiFetch<DocumentTemplateRead>("/api/v1/document-templates", {
    ...scope,
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function publishTemplateVersion(
  scope: Scope,
  templateId: string,
  body: DocumentTemplateVersionCreate,
): Promise<DocumentTemplateRead> {
  return apiFetch<DocumentTemplateRead>(
    `/api/v1/document-templates/${templateId}/versions`,
    { ...scope, method: "POST", body: JSON.stringify(body) },
  );
}

export function previewTemplate(
  scope: Scope,
  body: DocumentTemplatePreview,
): Promise<DocumentPreviewRead> {
  return apiFetch<DocumentPreviewRead>("/api/v1/document-templates/preview", {
    ...scope,
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function fetchPatientDocuments(
  scope: Scope,
  patientPublicId: string,
): Promise<PageSchemaDocumentRead> {
  const search = new URLSearchParams({
    patientPublicId,
    limit: "50",
  });
  return apiFetch<PageSchemaDocumentRead>(`/api/v1/documents?${search}`, scope);
}

export function createDocument(
  scope: Scope,
  body: DocumentCreate,
): Promise<DocumentRead> {
  return apiFetch<DocumentRead>("/api/v1/documents", {
    ...scope,
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function previewDocument(
  scope: Scope,
  documentId: string,
): Promise<DocumentPreviewRead> {
  return apiFetch<DocumentPreviewRead>(
    `/api/v1/documents/${documentId}/preview`,
    scope,
  );
}

export function finalizeDocument(
  scope: Scope,
  documentId: string,
  body: DocumentFinalize,
): Promise<DocumentRead> {
  return apiFetch<DocumentRead>(`/api/v1/documents/${documentId}/finalize`, {
    ...scope,
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function documentDownloadUrl(
  scope: Scope,
  documentId: string,
): Promise<DocumentDownloadRead> {
  return apiFetch<DocumentDownloadRead>(
    `/api/v1/documents/${documentId}/download-url`,
    scope,
  );
}
