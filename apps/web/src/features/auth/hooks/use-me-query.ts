"use client";

import { useQuery } from "@tanstack/react-query";
import { useLocale } from "next-intl";

import { fetchMe } from "@/features/auth/api/auth.api";
import { queryKeys } from "@/lib/api/query-keys";
import { useSession } from "@/providers/session-provider";

export function useMeQuery() {
  const locale = useLocale();
  const { session } = useSession();

  return useQuery({
    queryKey: queryKeys.auth.me(),
    queryFn: () => fetchMe(locale, session!.clinicPublicId),
    enabled: Boolean(session?.clinicPublicId),
    staleTime: 30_000,
  });
}
