import { apiFetch } from '@/lib/api/client';
import type {
  AttachmentDownloadUrlResponse,
  AttachmentRead,
  AttachmentUploadUrlRequest,
  AttachmentUploadUrlResponse,
  AttachmentConfirmRequest,
} from '@/lib/api/generated';

export async function requestAttachmentUploadUrl(
  body: AttachmentUploadUrlRequest,
  locale: string,
  clinicPublicId: string,
): Promise<AttachmentUploadUrlResponse> {
  return apiFetch<AttachmentUploadUrlResponse>('/api/v1/attachments/upload-url', {
    method: 'POST',
    body: JSON.stringify(body),
    locale,
    clinicPublicId,
  });
}

export async function confirmAttachmentUpload(
  body: AttachmentConfirmRequest,
  locale: string,
  clinicPublicId: string,
): Promise<AttachmentRead> {
  return apiFetch<AttachmentRead>('/api/v1/attachments/confirm', {
    method: 'POST',
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
  const query = variant ? `?variant=${encodeURIComponent(variant)}` : '';
  return apiFetch<AttachmentDownloadUrlResponse>(
    `/api/v1/attachments/${publicId}/download-url${query}`,
    {
      locale,
      clinicPublicId,
    },
  );
}
