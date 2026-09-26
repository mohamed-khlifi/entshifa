import { apiFetch } from "@/lib/api/client";
import type {
  LoginRequest,
  LoginResponse,
  MeResponse,
} from "@/lib/api/generated";

export async function loginRequest(
  body: LoginRequest,
  locale: string,
): Promise<LoginResponse> {
  return apiFetch<LoginResponse>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify(body),
    locale,
    auth: false,
  });
}

export async function refreshSession(locale: string): Promise<LoginResponse> {
  return apiFetch<LoginResponse>("/api/v1/auth/refresh", {
    method: "POST",
    locale,
    auth: false,
  });
}

export async function logoutRequest(): Promise<void> {
  await apiFetch<void>("/api/v1/auth/logout", {
    method: "POST",
  });
}

export async function fetchMe(
  locale: string,
  clinicPublicId: string,
): Promise<MeResponse> {
  return apiFetch<MeResponse>("/api/v1/auth/me", {
    locale,
    clinicPublicId,
  });
}
