import { apiFetch } from "@/lib/api/client";

import type {
  PageSchema,
  PublicQuestionnaireSession,
  QuestionnaireInvitationCreated,
  QuestionnaireResponseSummary,
} from "../types";

type Scope = { auth: boolean };

export async function fetchPublicQuestionnaireSession(
  token: string,
): Promise<PublicQuestionnaireSession> {
  return apiFetch<PublicQuestionnaireSession>(
    `/api/v1/public/questionnaires/${encodeURIComponent(token)}`,
    { auth: false },
  );
}

export async function submitPublicQuestionnaire(
  token: string,
  answers: Record<string, number>,
): Promise<{ completedAt: string; locale: string }> {
  return apiFetch(
    `/api/v1/public/questionnaires/${encodeURIComponent(token)}/submit`,
    {
      method: "POST",
      auth: false,
      body: JSON.stringify({ answers }),
      headers: { "Content-Type": "application/json" },
    },
  );
}

export async function createQuestionnaireInvitation(
  patientId: string,
  body: {
    instrumentCode: string;
    channel: "sms" | "whatsapp" | "email" | "tablet";
    context?: string;
    locale?: string;
    encounterId?: string;
  },
  idempotencyKey?: string,
): Promise<QuestionnaireInvitationCreated> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (idempotencyKey) {
    headers["Idempotency-Key"] = idempotencyKey;
  }
  return apiFetch<QuestionnaireInvitationCreated>(
    `/api/v1/patients/${patientId}/questionnaire-invitations`,
    {
      method: "POST",
      body: JSON.stringify(body),
      headers,
    },
  );
}

export async function listQuestionnaireResponses(
  patientId: string,
  params?: { instrumentCode?: string; limit?: number; offset?: number },
): Promise<PageSchema<QuestionnaireResponseSummary>> {
  const search = new URLSearchParams();
  if (params?.instrumentCode) {
    search.set("instrument_code", params.instrumentCode);
  }
  if (params?.limit !== undefined) {
    search.set("limit", String(params.limit));
  }
  if (params?.offset !== undefined) {
    search.set("offset", String(params.offset));
  }
  const qs = search.toString();
  return apiFetch<PageSchema<QuestionnaireResponseSummary>>(
    `/api/v1/patients/${patientId}/questionnaire-responses${qs ? `?${qs}` : ""}`,
    {} as Scope,
  );
}

export async function createStaffQuestionnaireResponse(
  patientId: string,
  body: {
    instrumentCode: string;
    locale: string;
    enteredBy: "staff" | "clinician";
    answers: Record<string, number>;
    encounterId?: string;
  },
  idempotencyKey?: string,
): Promise<QuestionnaireResponseSummary> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (idempotencyKey) {
    headers["Idempotency-Key"] = idempotencyKey;
  }
  return apiFetch<QuestionnaireResponseSummary>(
    `/api/v1/patients/${patientId}/questionnaire-responses`,
    {
      method: "POST",
      body: JSON.stringify(body),
      headers,
    },
  );
}
