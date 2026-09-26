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
  fetchMe,
  loginRequest,
  logoutRequest,
  refreshSession,
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

type SessionContextValue = {
  session: SessionState | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
};

const SessionContext = createContext<SessionContextValue | null>(null);

function toSession(me: MeResponse): SessionState {
  return {
    userPublicId: me.userPublicId,
    clinicPublicId: me.clinicPublicId,
    permissions: me.permissions,
  };
}

export function SessionProvider({ children }: { children: ReactNode }) {
  const locale = useLocale();
  const queryClient = useQueryClient();
  const [session, setSession] = useState<SessionState | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const loadSession = useCallback(async () => {
    try {
      const refreshed = await refreshSession(locale);
      setAccessToken(refreshed.accessToken);
      setSessionIndicatorCookie();
      const me = await fetchMe(locale, refreshed.session.clinicPublicId);
      setSession(toSession(me));
      await queryClient.invalidateQueries({ queryKey: queryKeys.auth.me() });
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
    async (email: string, password: string) => {
      const response = await loginRequest({ email, password }, locale);
      setAccessToken(response.accessToken);
      setSessionIndicatorCookie();
      const me = await fetchMe(locale, response.session.clinicPublicId);
      setSession(toSession(me));
      await queryClient.invalidateQueries({ queryKey: queryKeys.auth.me() });
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
      await queryClient.invalidateQueries({ queryKey: queryKeys.auth.me() });
    }
  }, [queryClient]);

  const value = useMemo<SessionContextValue>(
    () => ({
      session,
      isLoading,
      login,
      logout,
      refresh: loadSession,
    }),
    [session, isLoading, login, logout, loadSession],
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
