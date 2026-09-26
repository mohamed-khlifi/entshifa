/** In-memory access token; refresh token stays in HttpOnly cookie on /api. */

let accessToken: string | null = null;

export function getAccessToken(): string | null {
  return accessToken;
}

export function setAccessToken(token: string | null): void {
  accessToken = token;
}

export const SESSION_INDICATOR_COOKIE = "ent_has_session";

export function setSessionIndicatorCookie(): void {
  if (typeof document === "undefined") {
    return;
  }
  document.cookie = `${SESSION_INDICATOR_COOKIE}=1; path=/; SameSite=Lax`;
}

export function clearSessionIndicatorCookie(): void {
  if (typeof document === "undefined") {
    return;
  }
  document.cookie = `${SESSION_INDICATOR_COOKIE}=; path=/; Max-Age=0; SameSite=Lax`;
}
