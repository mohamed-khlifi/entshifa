import { apiFetch } from "@/lib/api/client";
import type {
  ActiveClinicRequest,
  ClinicMembershipList,
  InvitationAccept,
  LoginRequest,
  LoginResponse,
  MeResponse,
  MfaCode,
  MfaDisable,
  MfaEnrollResponse,
  MfaLogin,
  PasswordResetConfirm,
  PasswordResetRequest,
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

export async function completeMfaLogin(
  body: MfaLogin,
  locale: string,
): Promise<LoginResponse> {
  return apiFetch<LoginResponse>("/api/v1/auth/mfa", {
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

export async function fetchClinicMemberships(
  locale: string,
  clinicPublicId: string,
): Promise<ClinicMembershipList> {
  return apiFetch<ClinicMembershipList>("/api/v1/auth/clinics", {
    locale,
    clinicPublicId,
  });
}

export async function switchActiveClinic(
  body: ActiveClinicRequest,
  locale: string,
  clinicPublicId: string,
): Promise<LoginResponse> {
  return apiFetch<LoginResponse>("/api/v1/auth/active-clinic", {
    method: "POST",
    body: JSON.stringify(body),
    locale,
    clinicPublicId,
  });
}

export async function requestPasswordReset(
  body: PasswordResetRequest,
  locale: string,
): Promise<void> {
  await apiFetch<void>("/api/v1/auth/password-reset", {
    method: "POST",
    body: JSON.stringify(body),
    locale,
    auth: false,
  });
}

export async function confirmPasswordReset(
  body: PasswordResetConfirm,
  locale: string,
): Promise<void> {
  await apiFetch<void>("/api/v1/auth/password-reset/confirm", {
    method: "POST",
    body: JSON.stringify(body),
    locale,
    auth: false,
  });
}

export async function acceptInvitation(
  body: InvitationAccept,
  locale: string,
): Promise<void> {
  await apiFetch<void>("/api/v1/auth/invitations/accept", {
    method: "POST",
    body: JSON.stringify(body),
    locale,
    auth: false,
  });
}

export async function enrollMfa(
  locale: string,
  clinicPublicId: string,
): Promise<MfaEnrollResponse> {
  return apiFetch<MfaEnrollResponse>("/api/v1/auth/mfa/enroll", {
    method: "POST",
    locale,
    clinicPublicId,
  });
}

export async function confirmMfa(
  body: MfaCode,
  locale: string,
  clinicPublicId: string,
): Promise<void> {
  await apiFetch<void>("/api/v1/auth/mfa/confirm", {
    method: "POST",
    body: JSON.stringify(body),
    locale,
    clinicPublicId,
  });
}

export async function disableMfa(
  body: MfaDisable,
  locale: string,
  clinicPublicId: string,
): Promise<void> {
  await apiFetch<void>("/api/v1/auth/mfa/disable", {
    method: "POST",
    body: JSON.stringify(body),
    locale,
    clinicPublicId,
  });
}
