import { apiFetch } from "@/lib/api/client";
import type {
  PageSchemaInstrumentSummaryRead,
  PageSchemaQuestionnaireResponseRead,
  PublicQuestionnaireSessionRead,
  QuestionnaireInvitationCreatedRead,
  QuestionnaireResponseDetailRead,
  QuestionnaireResponseRead,
} from "@/lib/api/generated";

type Scope = { auth: boolean };

export async function fetchPublicQuestionnaireSession(
  token: string,
): Promise<PublicQuestionnaireSessionRead> {
  return apiFetch<PublicQuestionnaireSessionRead>(
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
): Promise<QuestionnaireInvitationCreatedRead> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (idempotencyKey) {
    headers["Idempotency-Key"] = idempotencyKey;
  }
  return apiFetch<QuestionnaireInvitationCreatedRead>(
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
  params?: {
    instrumentCode?: string;
    locale?: string;
    limit?: number;
    offset?: number;
  },
): Promise<PageSchemaQuestionnaireResponseRead> {
  const search = new URLSearchParams();
  if (params?.instrumentCode) {
    search.set("instrument_code", params.instrumentCode);
  }
  if (params?.locale) {
    search.set("locale", params.locale);
  }
  if (params?.limit !== undefined) {
    search.set("limit", String(params.limit));
  }
  if (params?.offset !== undefined) {
    search.set("offset", String(params.offset));
  }
  const qs = search.toString();
  return apiFetch<PageSchemaQuestionnaireResponseRead>(
    `/api/v1/patients/${patientId}/questionnaire-responses${qs ? `?${qs}` : ""}`,
    {} as Scope,
  );
}

export async function fetchQuestionnaireResponseDetail(
  responseId: string,
  locale?: string,
): Promise<QuestionnaireResponseDetailRead> {
  const search = new URLSearchParams();
  if (locale) {
    search.set("locale", locale);
  }
  const qs = search.toString();
  return apiFetch<QuestionnaireResponseDetailRead>(
    `/api/v1/questionnaire-responses/${encodeURIComponent(responseId)}${qs ? `?${qs}` : ""}`,
    {} as Scope,
  );
}

export async function listInstruments(params?: {
  locale?: string;
  limit?: number;
  offset?: number;
}): Promise<PageSchemaInstrumentSummaryRead> {
  const search = new URLSearchParams();
  if (params?.locale) {
    search.set("locale", params.locale);
  }
  if (params?.limit !== undefined) {
    search.set("limit", String(params.limit));
  }
  if (params?.offset !== undefined) {
    search.set("offset", String(params.offset));
  }
  const qs = search.toString();
  return apiFetch<PageSchemaInstrumentSummaryRead>(
    `/api/v1/instruments${qs ? `?${qs}` : ""}`,
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
): Promise<QuestionnaireResponseRead> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (idempotencyKey) {
    headers["Idempotency-Key"] = idempotencyKey;
  }
  return apiFetch<QuestionnaireResponseRead>(
    `/api/v1/patients/${patientId}/questionnaire-responses`,
    {
      method: "POST",
      body: JSON.stringify(body),
      headers,
    },
  );
}
