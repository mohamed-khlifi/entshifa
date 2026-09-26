"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useLocale } from "next-intl";
import { useQueryClient } from "@tanstack/react-query";

import {
  completeMfaLogin,
  fetchMe,
  loginRequest,
  logoutRequest,
  refreshSession,
  switchActiveClinic,
} from "@/features/auth";
import { queryKeys } from "@/lib/api/query-keys";
import type { MeResponse } from "@/lib/api/generated";
import {
  clearSessionIndicatorCookie,
  setAccessToken,
  setSessionIndicatorCookie,
} from "@/lib/auth/session-token";

type SessionState = {
  userPublicId: string;
  clinicPublicId: string;
  permissions: string[];
};

type LoginResult =
  { status: "ok" } | { status: "mfa_required"; mfaToken: string };

type SessionContextValue = {
  session: SessionState | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<LoginResult>;
  completeMfa: (mfaToken: string, code: string) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
  switchClinic: (clinicPublicId: string) => Promise<void>;
};

const SessionContext = createContext<SessionContextValue | null>(null);

function toSession(me: MeResponse): SessionState {
  return {
    userPublicId: me.userPublicId,
    clinicPublicId: me.clinicPublicId,
    permissions: me.permissions,
  };
}

async function applyLoginResponse(
  response: {
    accessToken?: string | null;
    session?: { clinicPublicId: string } | null;
  },
  locale: string,
  queryClient: ReturnType<typeof useQueryClient>,
  setSession: (s: SessionState | null) => void,
) {
  if (!response.accessToken || !response.session) {
    return;
  }
  setAccessToken(response.accessToken);
  setSessionIndicatorCookie();
  const me = await fetchMe(locale, response.session.clinicPublicId);
  setSession(toSession(me));
  await queryClient.invalidateQueries({ queryKey: queryKeys.auth.all });
}

export function SessionProvider({ children }: { children: ReactNode }) {
  const locale = useLocale();
  const queryClient = useQueryClient();
  const [session, setSession] = useState<SessionState | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const loadSession = useCallback(async () => {
    try {
      const refreshed = await refreshSession(locale);
      await applyLoginResponse(
        {
          accessToken: refreshed.accessToken,
          session: refreshed.session,
        },
        locale,
        queryClient,
        setSession,
      );
    } catch {
      setAccessToken(null);
      clearSessionIndicatorCookie();
      setSession(null);
    } finally {
      setIsLoading(false);
    }
  }, [locale, queryClient]);

  useEffect(() => {
    void loadSession();
  }, [loadSession]);

  const login = useCallback(
    async (email: string, password: string): Promise<LoginResult> => {
      const response = await loginRequest({ email, password }, locale);
      if (response.mfaRequired && response.mfaToken) {
        return { status: "mfa_required", mfaToken: response.mfaToken };
      }
      await applyLoginResponse(
        {
          accessToken: response.accessToken,
          session: response.session,
        },
        locale,
        queryClient,
        setSession,
      );
      return { status: "ok" };
    },
    [locale, queryClient],
  );

  const completeMfa = useCallback(
    async (mfaToken: string, code: string) => {
      const response = await completeMfaLogin({ mfaToken, code }, locale);
      await applyLoginResponse(
        {
          accessToken: response.accessToken,
          session: response.session,
        },
        locale,
        queryClient,
        setSession,
      );
    },
    [locale, queryClient],
  );

  const logout = useCallback(async () => {
    try {
      await logoutRequest();
    } finally {
      setAccessToken(null);
      clearSessionIndicatorCookie();
      setSession(null);
      await queryClient.invalidateQueries({ queryKey: queryKeys.auth.all });
    }
  }, [queryClient]);

  const switchClinic = useCallback(
    async (clinicPublicId: string) => {
      if (!session) {
        return;
      }
      const response = await switchActiveClinic(
        { clinicPublicId },
        locale,
        session.clinicPublicId,
      );
      await applyLoginResponse(
        {
          accessToken: response.accessToken,
          session: response.session,
        },
        locale,
        queryClient,
        setSession,
      );
    },
    [locale, queryClient, session],
  );

  const value = useMemo<SessionContextValue>(
    () => ({
      session,
      isLoading,
      login,
      completeMfa,
      logout,
      refresh: loadSession,
      switchClinic,
    }),
    [session, isLoading, login, completeMfa, logout, loadSession, switchClinic],
  );

  return (
    <SessionContext.Provider value={value}>{children}</SessionContext.Provider>
  );
}

export function useSession(): SessionContextValue {
  const context = useContext(SessionContext);
  if (context === null) {
    throw new Error("useSession requires SessionProvider");
  }
  return context;
}
