"use client";

import {
  useMutation,
  useQueries,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { useLocale, useTranslations } from "next-intl";
import { toast } from "sonner";

import {
  fetchExaminationValueSet,
  fetchPatientEncounters,
  recordExaminationSnapshot,
  recordObservations,
  renderNarrative,
} from "../api/examination.api";
import type {
  ExaminationSnapshotCreate,
  NarrativeRenderRequest,
  ObservationBatchCreate,
} from "@/lib/api/generated";
import { ApiError, resolveErrorMessage } from "@/lib/api/errors";
import { queryKeys } from "@/lib/api/query-keys";
import { useSession } from "@/providers/session-provider";

function useScope() {
  const locale = useLocale();
  const { session } = useSession();
  return {
    locale,
    clinicPublicId: session?.clinicPublicId ?? "",
    enabled: Boolean(session?.clinicPublicId),
  };
}

function useExaminationErrorToast(): (error: unknown) => void {
  const tErrors = useTranslations("errors");
  return (error: unknown) => {
    const message =
      error instanceof ApiError
        ? resolveErrorMessage(
            error,
            (key) => tErrors(key as Parameters<typeof tErrors>[0]),
            (key) => tErrors.has(key as Parameters<typeof tErrors.has>[0]),
          )
        : tErrors("generic");
    toast.error(message);
  };
}

export function usePatientEncounters(patientId: string) {
  const scope = useScope();
  return useQuery({
    queryKey: queryKeys.examination.encounters(patientId),
    queryFn: () =>
      fetchPatientEncounters(patientId, {
        locale: scope.locale,
        clinicPublicId: scope.clinicPublicId,
      }),
    enabled: scope.enabled && patientId.length > 0,
    staleTime: 30_000,
  });
}

export function useExaminationValueSets(codes: readonly string[]) {
  const scope = useScope();
  return useQueries({
    queries: codes.map((code) => ({
      queryKey: queryKeys.examination.valueSet(code, scope.locale),
      queryFn: () =>
        fetchExaminationValueSet(code, {
          locale: scope.locale,
          clinicPublicId: scope.clinicPublicId,
        }),
      enabled: scope.enabled && code.length > 0,
      staleTime: 3_600_000,
    })),
  });
}

export function useNarrativePreview(
  patientId: string,
  mapId: string,
  body: NarrativeRenderRequest | null,
) {
  const scope = useScope();
  const signature = JSON.stringify(body?.findings ?? []);
  return useQuery({
    queryKey: queryKeys.examination.narrative(patientId, mapId, signature),
    queryFn: () =>
      renderNarrative(body ?? { findings: [] }, {
        locale: scope.locale,
        clinicPublicId: scope.clinicPublicId,
      }),
    enabled: scope.enabled && body !== null && (body.findings?.length ?? 0) > 0,
    staleTime: 10_000,
  });
}

export function useRecordObservations(patientId: string) {
  const scope = useScope();
  const toastError = useExaminationErrorToast();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: ObservationBatchCreate) =>
      recordObservations(patientId, body, {
        locale: scope.locale,
        clinicPublicId: scope.clinicPublicId,
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: queryKeys.examination.encounters(patientId),
      });
    },
    onError: toastError,
  });
}

export function useRecordSnapshot(patientId: string) {
  const scope = useScope();
  const toastError = useExaminationErrorToast();
  return useMutation({
    mutationFn: (body: ExaminationSnapshotCreate) =>
      recordExaminationSnapshot(patientId, body, {
        locale: scope.locale,
        clinicPublicId: scope.clinicPublicId,
      }),
    onError: toastError,
  });
}
