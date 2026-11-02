import { apiFetch } from "@/lib/api/client";
import type {
  AudiogramBaselineUpdate,
  AudiogramCreate,
  AudiogramFinalize,
  AudiogramInterpret,
  AudiogramRead,
  AudiogramUpdate,
  PageSchemaAudiogramRead,
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
