import { ApiError, parseApiError } from '@/lib/api/errors';
import { getAccessToken } from '@/lib/auth/session-token';

export type ApiFetchOptions = RequestInit & {
  locale?: string;
  clinicPublicId?: string;
  auth?: boolean;
};

function apiBase(): string {
  if (typeof window !== 'undefined') {
    return '';
  }
  return process.env.API_URL ?? 'http://127.0.0.1:8000';
}

export async function apiFetch<T>(
  path: string,
  init: ApiFetchOptions = {},
): Promise<T> {
  const { locale, clinicPublicId, auth = true, headers, ...rest } = init;
  const token = auth ? getAccessToken() : null;
  const response = await fetch(`${apiBase()}${path}`, {
    ...rest,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      ...(locale ? { 'Accept-Language': locale } : {}),
      ...(clinicPublicId ? { 'X-Clinic-Id': clinicPublicId } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
  });

  if (response.status === 204) {
    return undefined as T;
  }

  if (!response.ok) {
    throw await parseApiError(response);
  }

  return (await response.json()) as T;
}

export { ApiError };
