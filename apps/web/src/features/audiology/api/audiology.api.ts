import { apiFetch } from "@/lib/api/client";
import type {
  AudiogramBaselineUpdate,
  AudiogramCreate,
  AudiogramFinalize,
  AudiogramInterpret,
  AudiogramRead,
  AudiogramUpdate,
  PageSchemaAbrResultRead,
  PageSchemaAudiogramRead,
  PageSchemaHearingDeviceRead,
  PageSchemaOaeResultRead,
  PageSchemaSpeechAudiometryRead,
  PageSchemaTympanometryRead,
  CandidacyEvaluate,
  CandidacyEvaluationRead,
  HearingDeviceCreate,
  HearingDeviceRead,
  MilestonesUpdate,
  NewbornScreeningUpdate,
  OmeEpisodeCreate,
  OmeEpisodeRead,
  PediatricAudiologyRead,
  PediatricSummaryRead,
  SpeechAudiometryCreate,
  SpeechAudiometryRead,
  SpeechAudiometryUpdate,
  TympanometryCreate,
  TympanometryInterpret,
  TympanometryRead,
  TympanometryUpdate,
} from "@/lib/api/generated";

type Scope = { locale: string; clinicPublicId: string };

export function fetchPatientAudiograms(
  patientId: string,
  scope: Scope,
): Promise<PageSchemaAudiogramRead> {
  return apiFetch<PageSchemaAudiogramRead>(
    `/api/v1/patients/${patientId}/audiograms?limit=50&offset=0`,
    scope,
  );
}

export function fetchAudiogram(
  audiogramId: string,
  scope: Scope,
): Promise<AudiogramRead> {
  return apiFetch<AudiogramRead>(`/api/v1/audiograms/${audiogramId}`, scope);
}

export function createAudiogram(
  body: AudiogramCreate,
  scope: Scope,
  idempotencyKey: string,
): Promise<AudiogramRead> {
  return apiFetch<AudiogramRead>("/api/v1/audiograms", {
    ...scope,
    method: "POST",
    body: JSON.stringify(body),
    headers: { "Idempotency-Key": idempotencyKey },
  });
}

export function updateAudiogram(
  audiogramId: string,
  body: AudiogramUpdate,
  scope: Scope,
): Promise<AudiogramRead> {
  return apiFetch<AudiogramRead>(`/api/v1/audiograms/${audiogramId}`, {
    ...scope,
    method: "PUT",
    body: JSON.stringify(body),
  });
}

export function finalizeAudiogram(
  audiogramId: string,
  body: AudiogramFinalize,
  scope: Scope,
): Promise<AudiogramRead> {
  return apiFetch<AudiogramRead>(`/api/v1/audiograms/${audiogramId}/finalize`, {
    ...scope,
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function interpretAudiogram(
  audiogramId: string,
  body: AudiogramInterpret,
  scope: Scope,
): Promise<AudiogramRead> {
  return apiFetch<AudiogramRead>(
    `/api/v1/audiograms/${audiogramId}/interpret`,
    {
      ...scope,
      method: "POST",
      body: JSON.stringify(body),
    },
  );
}

export function updateAudiogramBaseline(
  audiogramId: string,
  body: AudiogramBaselineUpdate,
  scope: Scope,
): Promise<AudiogramRead> {
  return apiFetch<AudiogramRead>(`/api/v1/audiograms/${audiogramId}/baseline`, {
    ...scope,
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function fetchPatientSpeechAudiometry(
  patientId: string,
  scope: Scope,
): Promise<PageSchemaSpeechAudiometryRead> {
  return apiFetch<PageSchemaSpeechAudiometryRead>(
    `/api/v1/patients/${patientId}/speech-audiometry?limit=50&offset=0`,
    scope,
  );
}

export function createSpeechAudiometry(
  body: SpeechAudiometryCreate,
  scope: Scope,
  idempotencyKey: string,
): Promise<SpeechAudiometryRead> {
  return apiFetch<SpeechAudiometryRead>("/api/v1/speech-audiometry", {
    ...scope,
    method: "POST",
    body: JSON.stringify(body),
    headers: { "Idempotency-Key": idempotencyKey },
  });
}

export function updateSpeechAudiometry(
  speechId: string,
  body: SpeechAudiometryUpdate,
  scope: Scope,
): Promise<SpeechAudiometryRead> {
  return apiFetch<SpeechAudiometryRead>(
    `/api/v1/speech-audiometry/${speechId}`,
    {
      ...scope,
      method: "PUT",
      body: JSON.stringify(body),
    },
  );
}

export function fetchPatientTympanograms(
  patientId: string,
  scope: Scope,
): Promise<PageSchemaTympanometryRead> {
  return apiFetch<PageSchemaTympanometryRead>(
    `/api/v1/patients/${patientId}/tympanograms?limit=50&offset=0`,
    scope,
  );
}

export function createTympanogram(
  body: TympanometryCreate,
  scope: Scope,
  idempotencyKey: string,
): Promise<TympanometryRead> {
  return apiFetch<TympanometryRead>("/api/v1/tympanograms", {
    ...scope,
    method: "POST",
    body: JSON.stringify(body),
    headers: { "Idempotency-Key": idempotencyKey },
  });
}

export function updateTympanogram(
  tympanogramId: string,
  body: TympanometryUpdate,
  scope: Scope,
): Promise<TympanometryRead> {
  return apiFetch<TympanometryRead>(`/api/v1/tympanograms/${tympanogramId}`, {
    ...scope,
    method: "PUT",
    body: JSON.stringify(body),
  });
}

export function interpretTympanogram(
  tympanogramId: string,
  body: TympanometryInterpret,
  scope: Scope,
): Promise<TympanometryRead> {
  return apiFetch<TympanometryRead>(
    `/api/v1/tympanograms/${tympanogramId}/interpret`,
    {
      ...scope,
      method: "POST",
      body: JSON.stringify(body),
    },
  );
}

export function fetchPatientOaeResults(
  patientId: string,
  scope: Scope,
): Promise<PageSchemaOaeResultRead> {
  return apiFetch<PageSchemaOaeResultRead>(
    `/api/v1/patients/${patientId}/oae-results?limit=50&offset=0`,
    scope,
  );
}

export function fetchPatientAbrResults(
  patientId: string,
  scope: Scope,
): Promise<PageSchemaAbrResultRead> {
  return apiFetch<PageSchemaAbrResultRead>(
    `/api/v1/patients/${patientId}/abr-results?limit=50&offset=0`,
    scope,
  );
}

export function fetchPatientHearingDevices(
  patientId: string,
  scope: Scope,
): Promise<PageSchemaHearingDeviceRead> {
  return apiFetch<PageSchemaHearingDeviceRead>(
    `/api/v1/patients/${patientId}/hearing-devices?limit=50&offset=0`,
    scope,
  );
}

export function createHearingDevice(
  body: HearingDeviceCreate,
  scope: Scope,
  idempotencyKey: string,
): Promise<HearingDeviceRead> {
  return apiFetch<HearingDeviceRead>("/api/v1/hearing-devices", {
    ...scope,
    method: "POST",
    body: JSON.stringify(body),
    headers: { "Idempotency-Key": idempotencyKey },
  });
}

export function evaluateDeviceCandidacy(
  body: CandidacyEvaluate,
  scope: Scope,
): Promise<CandidacyEvaluationRead> {
  return apiFetch<CandidacyEvaluationRead>(
    "/api/v1/audiology/candidacy/evaluate",
    {
      ...scope,
      method: "POST",
      body: JSON.stringify(body),
    },
  );
}

export function fetchPediatricAudiologySummary(
  patientId: string,
  scope: Scope,
): Promise<PediatricSummaryRead> {
  return apiFetch<PediatricSummaryRead>(
    `/api/v1/patients/${patientId}/audiology/pediatric?limit=20&offset=0`,
    scope,
  );
}

export function updateNewbornScreening(
  patientId: string,
  body: NewbornScreeningUpdate,
  scope: Scope,
): Promise<PediatricAudiologyRead> {
  return apiFetch<PediatricAudiologyRead>(
    `/api/v1/patients/${patientId}/audiology/pediatric/screening`,
    {
      ...scope,
      method: "PUT",
      body: JSON.stringify(body),
    },
  );
}

export function updatePediatricMilestones(
  patientId: string,
  body: MilestonesUpdate,
  scope: Scope,
): Promise<PediatricAudiologyRead> {
  return apiFetch<PediatricAudiologyRead>(
    `/api/v1/patients/${patientId}/audiology/pediatric/milestones`,
    {
      ...scope,
      method: "PUT",
      body: JSON.stringify(body),
    },
  );
}

export function createOmeEpisode(
  body: OmeEpisodeCreate,
  scope: Scope,
  idempotencyKey: string,
): Promise<OmeEpisodeRead> {
  return apiFetch<OmeEpisodeRead>("/api/v1/ome-episodes", {
    ...scope,
    method: "POST",
    body: JSON.stringify(body),
    headers: { "Idempotency-Key": idempotencyKey },
  });
}
