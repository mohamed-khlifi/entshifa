"use client";

import { useQuery } from "@tanstack/react-query";
import { useLocale } from "next-intl";

import { fetchClinicMemberships } from "@/features/auth/api/auth.api";
import { queryKeys } from "@/lib/api/query-keys";
import { useSession } from "@/providers/session-provider";

export function useClinicMembershipsQuery() {
  const locale = useLocale();
  const { session } = useSession();

  return useQuery({
    queryKey: queryKeys.auth.clinics(),
    queryFn: () => fetchClinicMemberships(locale, session!.clinicPublicId),
    enabled: Boolean(session?.clinicPublicId),
    staleTime: 60_000,
  });
}
