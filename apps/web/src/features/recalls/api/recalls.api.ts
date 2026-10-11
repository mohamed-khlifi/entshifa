import { apiFetch } from "@/lib/api/client";
import type {
  PageSchemaRecallRead,
  RecallActionCreate,
  RecallBook,
  RecallCancel,
  RecallCreate,
  RecallRead,
  RecallSummaryRead,
} from "@/lib/api/generated";

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

export function fetchRecallSummary(scope: Scope): Promise<RecallSummaryRead> {
  return apiFetch<RecallSummaryRead>("/api/v1/recalls/summary", scope);
}

export function fetchRecalls(
  scope: Scope,
  params: {
    bucket?: string;
    patientId?: string;
    limit?: number;
    offset?: number;
  },
): Promise<PageSchemaRecallRead> {
  return apiFetch<PageSchemaRecallRead>(
    `/api/v1/recalls${query({
      bucket: params.bucket,
      patient_id: params.patientId,
      limit: params.limit,
      offset: params.offset,
    })}`,
    scope,
  );
}

export function createRecall(
  scope: Scope,
  body: RecallCreate,
  idempotencyKey: string,
): Promise<RecallRead> {
  return apiFetch<RecallRead>("/api/v1/recalls", {
    ...scope,
    method: "POST",
    body: JSON.stringify(body),
    headers: { "Idempotency-Key": idempotencyKey },
  });
}

export function logRecallAction(
  scope: Scope,
  recallId: string,
  body: RecallActionCreate,
): Promise<RecallRead> {
  return apiFetch<RecallRead>(`/api/v1/recalls/${recallId}/actions`, {
    ...scope,
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function bookRecall(
  scope: Scope,
  recallId: string,
  body: RecallBook,
): Promise<RecallRead> {
  return apiFetch<RecallRead>(`/api/v1/recalls/${recallId}/book`, {
    ...scope,
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function cancelRecall(
  scope: Scope,
  recallId: string,
  body: RecallCancel,
): Promise<RecallRead> {
  return apiFetch<RecallRead>(`/api/v1/recalls/${recallId}/cancel`, {
    ...scope,
    method: "POST",
    body: JSON.stringify(body),
  });
}
