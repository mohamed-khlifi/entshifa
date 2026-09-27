import { apiFetch } from "@/lib/api/client";
import type {
  AttachmentConfirmRequest,
  AttachmentDownloadUrlResponse,
  AttachmentRead,
  AttachmentUploadUrlRequest,
  AttachmentUploadUrlResponse,
  ConceptSearchResponse,
  PageSchemaAttachmentRead,
} from "@/lib/api/generated";

type Scope = { locale: string; clinicPublicId: string };

export type AttachmentListParams = {
  patientPublicId: string;
  category?: string;
  laterality?: string;
  capturedFrom?: string;
  capturedTo?: string;
  limit?: number;
  offset?: number;
};

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

export function fetchAttachments(
  scope: Scope,
  params: AttachmentListParams,
): Promise<PageSchemaAttachmentRead> {
  return apiFetch<PageSchemaAttachmentRead>(
    `/api/v1/attachments${query({
      patientPublicId: params.patientPublicId,
      category: params.category,
      laterality: params.laterality,
      capturedFrom: params.capturedFrom,
      capturedTo: params.capturedTo,
      limit: params.limit,
      offset: params.offset,
    })}`,
    scope,
  );
}

export function searchAnatomyConcepts(
  scope: Scope,
  term: string,
): Promise<ConceptSearchResponse> {
  return apiFetch<ConceptSearchResponse>(
    `/api/v1/terminology/concepts/search${query({
      q: term,
      locale: scope.locale,
      kind: "anatomy",
    })}`,
    scope,
  );
}

export async function requestAttachmentUploadUrl(
  body: AttachmentUploadUrlRequest,
  locale: string,
  clinicPublicId: string,
): Promise<AttachmentUploadUrlResponse> {
  return apiFetch<AttachmentUploadUrlResponse>(
    "/api/v1/attachments/upload-url",
    {
      method: "POST",
      body: JSON.stringify(body),
      locale,
      clinicPublicId,
    },
  );
}

export async function confirmAttachmentUpload(
  body: AttachmentConfirmRequest,
  locale: string,
  clinicPublicId: string,
): Promise<AttachmentRead> {
  return apiFetch<AttachmentRead>("/api/v1/attachments/confirm", {
    method: "POST",
    body: JSON.stringify(body),
    locale,
    clinicPublicId,
  });
}

export async function fetchAttachment(
  publicId: string,
  locale: string,
  clinicPublicId: string,
): Promise<AttachmentRead> {
  return apiFetch<AttachmentRead>(`/api/v1/attachments/${publicId}`, {
    locale,
    clinicPublicId,
  });
}

export async function fetchAttachmentDownloadUrl(
  publicId: string,
  locale: string,
  clinicPublicId: string,
  variant?: string,
): Promise<AttachmentDownloadUrlResponse> {
  const query = variant ? `?variant=${encodeURIComponent(variant)}` : "";
  return apiFetch<AttachmentDownloadUrlResponse>(
    `/api/v1/attachments/${publicId}/download-url${query}`,
    {
      locale,
      clinicPublicId,
    },
  );
}
