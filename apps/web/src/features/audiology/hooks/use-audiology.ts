"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useLocale, useTranslations } from "next-intl";
import { useMemo, useState } from "react";
import { toast } from "sonner";

import {
  createAudiogram,
  fetchAudiogram,
  fetchPatientAudiograms,
  finalizeAudiogram,
  interpretAudiogram,
  updateAudiogram,
  updateAudiogramBaseline,
} from "../api/audiology.api";
import type {
  AudiogramBaselineUpdate,
  AudiogramCreate,
  AudiogramFinalize,
  AudiogramInterpret,
  AudiogramRead,
  AudiogramUpdate,
} from "@/lib/api/generated";
import { ApiError, resolveErrorMessage } from "@/lib/api/errors";
import { queryKeys } from "@/lib/api/query-keys";
import { useSession } from "@/providers/session-provider";

const RECORD_STALE_MS = 30_000;

function useScope() {
  const locale = useLocale();
  const { session } = useSession();
  return {
    locale,
    clinicPublicId: session?.clinicPublicId ?? "",
    enabled: Boolean(session?.clinicPublicId),
  };
}

function useAudiologyErrorToast(): (error: unknown) => void {
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

export function usePatientAudiograms(patientId: string) {
  const scope = useScope();
  return useQuery({
    queryKey: queryKeys.audiology.patient(patientId),
    queryFn: () =>
      fetchPatientAudiograms(patientId, {
        locale: scope.locale,
        clinicPublicId: scope.clinicPublicId,
      }),
    enabled: scope.enabled && patientId.length > 0,
    staleTime: RECORD_STALE_MS,
  });
}

export function useAudiogramDetail(audiogramId: string | null) {
  const scope = useScope();
  return useQuery({
    queryKey: queryKeys.audiology.detail(audiogramId ?? ""),
    queryFn: () =>
      fetchAudiogram(audiogramId as string, {
        locale: scope.locale,
        clinicPublicId: scope.clinicPublicId,
      }),
    enabled: scope.enabled && Boolean(audiogramId),
    staleTime: RECORD_STALE_MS,
  });
}

export type SaveAudiogramInput = {
  audiogramId: string | null;
  createBody: AudiogramCreate;
  updateBody: AudiogramUpdate;
  idempotencyKey: string;
  silent?: boolean;
};

export function useSaveAudiogram(patientId: string) {
  const scope = useScope();
  const t = useTranslations("audiology");
  const toastError = useAudiologyErrorToast();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: SaveAudiogramInput) => {
      const requestScope = {
        locale: scope.locale,
        clinicPublicId: scope.clinicPublicId,
      };
      if (input.audiogramId) {
        return updateAudiogram(
          input.audiogramId,
          input.updateBody,
          requestScope,
        );
      }
      return createAudiogram(
        input.createBody,
        requestScope,
        input.idempotencyKey,
      );
    },
    onSuccess: async (exam, input) => {
      if (!input.silent) {
        toast.success(t("actions.saved"));
      }
      await queryClient.invalidateQueries({
        queryKey: queryKeys.audiology.patient(patientId),
      });
      await queryClient.invalidateQueries({
        queryKey: queryKeys.audiology.detail(exam.publicId),
      });
    },
    onError: (error, input) => {
      if (!input.silent) {
        toastError(error);
      }
    },
  });
}

export function useFinalizeAudiogram(patientId: string) {
  const scope = useScope();
  const t = useTranslations("audiology");
  const toastError = useAudiologyErrorToast();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: { audiogramId: string; body: AudiogramFinalize }) =>
      finalizeAudiogram(input.audiogramId, input.body, {
        locale: scope.locale,
        clinicPublicId: scope.clinicPublicId,
      }),
    onSuccess: async (exam) => {
      toast.success(t("actions.finalized"));
      await queryClient.invalidateQueries({
        queryKey: queryKeys.audiology.patient(patientId),
      });
      await queryClient.invalidateQueries({
        queryKey: queryKeys.audiology.detail(exam.publicId),
      });
    },
    onError: toastError,
  });
}

export function useInterpretAudiogram(patientId: string) {
  const scope = useScope();
  const toastError = useAudiologyErrorToast();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: { audiogramId: string; body: AudiogramInterpret }) =>
      interpretAudiogram(input.audiogramId, input.body, {
        locale: scope.locale,
        clinicPublicId: scope.clinicPublicId,
      }),
    onSuccess: async (exam) => {
      await queryClient.invalidateQueries({
        queryKey: queryKeys.audiology.patient(patientId),
      });
      await queryClient.invalidateQueries({
        queryKey: queryKeys.audiology.detail(exam.publicId),
      });
    },
    onError: toastError,
  });
}

export function useAudiogramBaseline(patientId: string) {
  const scope = useScope();
  const toastError = useAudiologyErrorToast();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: {
      audiogramId: string;
      body: AudiogramBaselineUpdate;
    }) =>
      updateAudiogramBaseline(input.audiogramId, input.body, {
        locale: scope.locale,
        clinicPublicId: scope.clinicPublicId,
      }),
    onSuccess: async (exam) => {
      await queryClient.invalidateQueries({
        queryKey: queryKeys.audiology.patient(patientId),
      });
      await queryClient.invalidateQueries({
        queryKey: queryKeys.audiology.detail(exam.publicId),
      });
    },
    onError: toastError,
  });
}

export function useAudiogramCompare(
  patientId: string,
  currentAudiogramId: string | null,
) {
  const list = usePatientAudiograms(patientId);
  const overlayCandidates = useMemo(() => {
    return (list.data?.items ?? []).filter(
      (row) => row.publicId !== currentAudiogramId,
    );
  }, [currentAudiogramId, list.data?.items]);
  const [idempotencyKey, setIdempotencyKey] = useState(() =>
    crypto.randomUUID(),
  );
  const resetIdempotencyKey = () => {
    setIdempotencyKey(crypto.randomUUID());
  };
  return {
    list,
    overlayCandidates,
    idempotencyKey,
    resetIdempotencyKey,
  };
}

export type { AudiogramRead };
