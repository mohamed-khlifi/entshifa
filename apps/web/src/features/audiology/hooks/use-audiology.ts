"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useLocale, useTranslations } from "next-intl";
import { useMemo, useState } from "react";
import { toast } from "sonner";

import {
  createAudiogram,
  createSpeechAudiometry,
  createTympanogram,
  createHearingDevice,
  createOmeEpisode,
  evaluateDeviceCandidacy,
  fetchAudiogram,
  fetchPatientAbrResults,
  fetchPatientAudiograms,
  fetchPatientHearingDevices,
  fetchPediatricAudiologySummary,
  fetchPatientOaeResults,
  fetchPatientSpeechAudiometry,
  fetchPatientTympanograms,
  finalizeAudiogram,
  interpretAudiogram,
  interpretTympanogram,
  updateAudiogram,
  updateAudiogramBaseline,
  updateNewbornScreening,
  updatePediatricMilestones,
  updateSpeechAudiometry,
  updateTympanogram,
} from "../api/audiology.api";
import type {
  AudiogramBaselineUpdate,
  AudiogramCreate,
  AudiogramFinalize,
  AudiogramInterpret,
  AudiogramRead,
  AudiogramUpdate,
  CandidacyEvaluationRead,
  HearingDeviceCreate,
  MilestonesUpdate,
  NewbornScreeningUpdate,
  OmeEpisodeCreate,
  SpeechAudiometryCreate,
  SpeechAudiometryRead,
  SpeechAudiometryUpdate,
  TympanometryCreate,
  TympanometryInterpret,
  TympanometryUpdate,
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

export function usePatientSpeechAudiometry(patientId: string) {
  const scope = useScope();
  return useQuery({
    queryKey: queryKeys.audiology.speechByPatient(patientId),
    queryFn: () =>
      fetchPatientSpeechAudiometry(patientId, {
        locale: scope.locale,
        clinicPublicId: scope.clinicPublicId,
      }),
    enabled: scope.enabled && patientId.length > 0,
    staleTime: RECORD_STALE_MS,
  });
}

export type SaveSpeechInput = {
  speechId: string | null;
  createBody: SpeechAudiometryCreate;
  updateBody: SpeechAudiometryUpdate;
  idempotencyKey: string;
};

export function useSaveSpeechAudiometry(patientId: string) {
  const scope = useScope();
  const t = useTranslations("audiology");
  const toastError = useAudiologyErrorToast();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: SaveSpeechInput) => {
      const requestScope = {
        locale: scope.locale,
        clinicPublicId: scope.clinicPublicId,
      };
      if (input.speechId) {
        return updateSpeechAudiometry(
          input.speechId,
          input.updateBody,
          requestScope,
        );
      }
      return createSpeechAudiometry(
        input.createBody,
        requestScope,
        input.idempotencyKey,
      );
    },
    onSuccess: async (exam: SpeechAudiometryRead) => {
      toast.success(t("speech.saved"));
      await queryClient.invalidateQueries({
        queryKey: queryKeys.audiology.speechByPatient(patientId),
      });
      await queryClient.invalidateQueries({
        queryKey: queryKeys.audiology.patient(patientId),
      });
      if (exam.audiogramPublicId) {
        await queryClient.invalidateQueries({
          queryKey: queryKeys.audiology.detail(exam.audiogramPublicId),
        });
      }
    },
    onError: toastError,
  });
}

export function usePatientTympanograms(patientId: string) {
  const scope = useScope();
  return useQuery({
    queryKey: queryKeys.audiology.tympanogramsByPatient(patientId),
    queryFn: () =>
      fetchPatientTympanograms(patientId, {
        locale: scope.locale,
        clinicPublicId: scope.clinicPublicId,
      }),
    enabled: scope.enabled && patientId.length > 0,
    staleTime: RECORD_STALE_MS,
  });
}

export type SaveTympanogramInput = {
  tympanogramId: string | null;
  createBody: TympanometryCreate;
  updateBody: TympanometryUpdate;
  idempotencyKey: string;
};

export function useSaveTympanogram(patientId: string) {
  const scope = useScope();
  const t = useTranslations("audiology");
  const toastError = useAudiologyErrorToast();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: SaveTympanogramInput) => {
      const requestScope = {
        locale: scope.locale,
        clinicPublicId: scope.clinicPublicId,
      };
      if (input.tympanogramId) {
        return updateTympanogram(
          input.tympanogramId,
          input.updateBody,
          requestScope,
        );
      }
      return createTympanogram(
        input.createBody,
        requestScope,
        input.idempotencyKey,
      );
    },
    onSuccess: async () => {
      toast.success(t("tympanometry.saved"));
      await queryClient.invalidateQueries({
        queryKey: queryKeys.audiology.tympanogramsByPatient(patientId),
      });
    },
    onError: toastError,
  });
}

export function useInterpretTympanogram(patientId: string) {
  const scope = useScope();
  const toastError = useAudiologyErrorToast();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: {
      tympanogramId: string;
      body: TympanometryInterpret;
    }) =>
      interpretTympanogram(input.tympanogramId, input.body, {
        locale: scope.locale,
        clinicPublicId: scope.clinicPublicId,
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: queryKeys.audiology.tympanogramsByPatient(patientId),
      });
    },
    onError: toastError,
  });
}

export function usePatientOaeResults(patientId: string) {
  const scope = useScope();
  return useQuery({
    queryKey: queryKeys.audiology.oaeByPatient(patientId),
    queryFn: () =>
      fetchPatientOaeResults(patientId, {
        locale: scope.locale,
        clinicPublicId: scope.clinicPublicId,
      }),
    enabled: scope.enabled && patientId.length > 0,
    staleTime: RECORD_STALE_MS,
  });
}

export function usePatientAbrResults(patientId: string) {
  const scope = useScope();
  return useQuery({
    queryKey: queryKeys.audiology.abrByPatient(patientId),
    queryFn: () =>
      fetchPatientAbrResults(patientId, {
        locale: scope.locale,
        clinicPublicId: scope.clinicPublicId,
      }),
    enabled: scope.enabled && patientId.length > 0,
    staleTime: RECORD_STALE_MS,
  });
}

export function usePatientHearingDevices(patientId: string) {
  const scope = useScope();
  return useQuery({
    queryKey: queryKeys.audiology.hearingDevicesByPatient(patientId),
    queryFn: () =>
      fetchPatientHearingDevices(patientId, {
        locale: scope.locale,
        clinicPublicId: scope.clinicPublicId,
      }),
    enabled: scope.enabled && patientId.length > 0,
    staleTime: RECORD_STALE_MS,
  });
}

export function useCreateHearingDevice(patientId: string) {
  const scope = useScope();
  const t = useTranslations("audiology");
  const toastError = useAudiologyErrorToast();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: HearingDeviceCreate) =>
      createHearingDevice(
        body,
        {
          locale: scope.locale,
          clinicPublicId: scope.clinicPublicId,
        },
        crypto.randomUUID(),
      ),
    onSuccess: async () => {
      toast.success(t("devices.saved"));
      await queryClient.invalidateQueries({
        queryKey: queryKeys.audiology.hearingDevicesByPatient(patientId),
      });
    },
    onError: toastError,
  });
}

export type EvaluateCandidacyInput = {
  audiogramPublicId: string | null;
  hearingAidTrialCompleted: boolean;
  imagingClearance: boolean;
  communicationImpactAssessed: boolean;
};

export function useEvaluateCandidacy(patientId: string) {
  const scope = useScope();
  const toastError = useAudiologyErrorToast();
  return useMutation({
    mutationFn: (input: EvaluateCandidacyInput) =>
      evaluateDeviceCandidacy(
        {
          patientPublicId: patientId,
          audiogramPublicId: input.audiogramPublicId,
          hearingAidTrialCompleted: input.hearingAidTrialCompleted,
          imagingClearance: input.imagingClearance,
          communicationImpactAssessed: input.communicationImpactAssessed,
        },
        {
          locale: scope.locale,
          clinicPublicId: scope.clinicPublicId,
        },
      ),
    onError: toastError,
  });
}

export function usePediatricAudiologySummary(patientId: string) {
  const scope = useScope();
  return useQuery({
    queryKey: queryKeys.audiology.pediatricByPatient(patientId),
    queryFn: () =>
      fetchPediatricAudiologySummary(patientId, {
        locale: scope.locale,
        clinicPublicId: scope.clinicPublicId,
      }),
    enabled: scope.enabled && patientId.length > 0,
    staleTime: RECORD_STALE_MS,
  });
}

export function useUpdateNewbornScreening(patientId: string) {
  const scope = useScope();
  const t = useTranslations("audiology");
  const toastError = useAudiologyErrorToast();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: NewbornScreeningUpdate) =>
      updateNewbornScreening(patientId, body, {
        locale: scope.locale,
        clinicPublicId: scope.clinicPublicId,
      }),
    onSuccess: async () => {
      toast.success(t("pediatric.screeningSaved"));
      await queryClient.invalidateQueries({
        queryKey: queryKeys.audiology.pediatricByPatient(patientId),
      });
    },
    onError: toastError,
  });
}

export function useUpdatePediatricMilestones(patientId: string) {
  const scope = useScope();
  const t = useTranslations("audiology");
  const toastError = useAudiologyErrorToast();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: MilestonesUpdate) =>
      updatePediatricMilestones(patientId, body, {
        locale: scope.locale,
        clinicPublicId: scope.clinicPublicId,
      }),
    onSuccess: async () => {
      toast.success(t("pediatric.milestonesSaved"));
      await queryClient.invalidateQueries({
        queryKey: queryKeys.audiology.pediatricByPatient(patientId),
      });
    },
    onError: toastError,
  });
}

export function useCreateOmeEpisode(patientId: string) {
  const scope = useScope();
  const t = useTranslations("audiology");
  const toastError = useAudiologyErrorToast();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: OmeEpisodeCreate) =>
      createOmeEpisode(
        body,
        {
          locale: scope.locale,
          clinicPublicId: scope.clinicPublicId,
        },
        crypto.randomUUID(),
      ),
    onSuccess: async () => {
      toast.success(t("pediatric.omeStarted"));
      await queryClient.invalidateQueries({
        queryKey: queryKeys.audiology.pediatricByPatient(patientId),
      });
    },
    onError: toastError,
  });
}

export type { AudiogramRead, CandidacyEvaluationRead };
