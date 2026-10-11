"use client";

import { useInfiniteQuery, useQueryClient } from "@tanstack/react-query";
import { useLocale } from "next-intl";

import { fetchPatientTimeline } from "../api/patients.api";
import { queryKeys } from "@/lib/api/query-keys";
import { useSession } from "@/providers/session-provider";

export type TimelineFilters = {
  type?: string;
  laterality?: string;
  problemId?: string;
};

function scopeOf(locale: string, clinicPublicId: string) {
  return { locale, clinicPublicId };
}

export function usePatientTimelineInfinite(
  patientId: string,
  filters: TimelineFilters,
) {
  const locale = useLocale();
  const { session } = useSession();
  const clinicPublicId = session?.clinicPublicId ?? "";
  return useInfiniteQuery({
    queryKey: queryKeys.patients.timeline(patientId, {
      type: filters.type,
      laterality: filters.laterality,
      problemId: filters.problemId,
    }),
    initialPageParam: undefined as string | undefined,
    queryFn: ({ pageParam }) =>
      fetchPatientTimeline(patientId, scopeOf(locale, clinicPublicId), {
        types: filters.type || undefined,
        laterality: filters.laterality || undefined,
        problemId: filters.problemId || undefined,
        limit: 50,
        cursor: pageParam,
      }),
    getNextPageParam: (last) => last.page.nextCursor ?? undefined,
    enabled: Boolean(clinicPublicId) && patientId.length > 0,
    staleTime: 30_000,
  });
}

export function useTimelinePrint() {
  const locale = useLocale();
  const { session } = useSession();
  const queryClient = useQueryClient();
  return async (patientId: string, filters: TimelineFilters) => {
    if (!session?.clinicPublicId) {
      return null;
    }
    return queryClient.fetchQuery({
      queryKey: [...queryKeys.patients.timeline(patientId, filters), "summary"],
      queryFn: () =>
        fetchPatientTimeline(
          patientId,
          scopeOf(locale, session.clinicPublicId),
          {
            types: filters.type || undefined,
            laterality: filters.laterality || undefined,
            problemId: filters.problemId || undefined,
            summary: true,
            limit: 24,
          },
        ),
    });
  };
}
