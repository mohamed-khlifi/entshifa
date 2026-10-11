"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useLocale, useTranslations } from "next-intl";
import { toast } from "sonner";

import {
  createOtologyExam,
  fetchOtologyValueSet,
  fetchPatientEarDevices,
  fetchPatientOtologyExams,
  signOtologyProcedure,
  updateEarDeviceStatus,
  updateOtologyExam,
} from "../api/otology.api";
import type {
  EarDeviceStatusUpdate,
  OtologyCreate,
  OtologyUpdate,
  ValueSetRead,
} from "@/lib/api/generated";
import { ApiError, resolveErrorMessage } from "@/lib/api/errors";
import { queryKeys } from "@/lib/api/query-keys";
import { useSession } from "@/providers/session-provider";

const REFERENCE_STALE_MS = 24 * 60 * 60 * 1000;
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

function useOtologyErrorToast(): (error: unknown) => void {
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

export function usePatientOtologyExams(patientId: string) {
  const scope = useScope();
  return useQuery({
    queryKey: queryKeys.otology.patient(patientId),
    queryFn: () =>
      fetchPatientOtologyExams(patientId, {
        locale: scope.locale,
        clinicPublicId: scope.clinicPublicId,
      }),
    enabled: scope.enabled && patientId.length > 0,
    staleTime: RECORD_STALE_MS,
  });
}

export function usePatientEarDevices(patientId: string) {
  const scope = useScope();
  return useQuery({
    queryKey: queryKeys.otology.devices(patientId),
    queryFn: () =>
      fetchPatientEarDevices(patientId, {
        locale: scope.locale,
        clinicPublicId: scope.clinicPublicId,
      }),
    enabled: scope.enabled && patientId.length > 0,
    staleTime: RECORD_STALE_MS,
  });
}

export function useOtologyValueSet(code: string) {
  const scope = useScope();
  return useQuery({
    queryKey: queryKeys.examination.valueSet(code, scope.locale),
    queryFn: () =>
      fetchOtologyValueSet(code, {
        locale: scope.locale,
        clinicPublicId: scope.clinicPublicId,
      }),
    enabled: scope.enabled,
    staleTime: REFERENCE_STALE_MS,
  });
}

export type SaveOtologyInput = {
  examId: string | null;
  createBody: OtologyCreate;
  updateBody: OtologyUpdate;
  silent?: boolean;
};

export function useSaveOtology(patientId: string) {
  const scope = useScope();
  const t = useTranslations("otology");
  const toastError = useOtologyErrorToast();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: SaveOtologyInput) => {
      const requestScope = {
        locale: scope.locale,
        clinicPublicId: scope.clinicPublicId,
      };
      if (input.examId) {
        return updateOtologyExam(input.examId, input.updateBody, requestScope);
      }
      return createOtologyExam(input.createBody, requestScope);
    },
    onSuccess: async (exam, input) => {
      if (!input.silent) {
        toast.success(t("actions.saved"));
      }
      await queryClient.invalidateQueries({
        queryKey: queryKeys.otology.patient(patientId),
      });
      await queryClient.invalidateQueries({
        queryKey: queryKeys.otology.devices(patientId),
      });
      await queryClient.invalidateQueries({
        queryKey: queryKeys.patients.detail(patientId),
      });
      await queryClient.invalidateQueries({
        queryKey: queryKeys.otology.detail(exam.publicId),
      });
    },
    onError: (error, input) => {
      if (!input.silent) {
        toastError(error);
      }
    },
  });
}

export function useSignOtology(patientId: string) {
  const scope = useScope();
  const t = useTranslations("otology");
  const toastError = useOtologyErrorToast();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (procedureId: string) =>
      signOtologyProcedure(
        procedureId,
        { role: "clinician" },
        { locale: scope.locale, clinicPublicId: scope.clinicPublicId },
      ),
    onSuccess: async () => {
      toast.success(t("actions.signed"));
      await queryClient.invalidateQueries({
        queryKey: queryKeys.otology.patient(patientId),
      });
    },
    onError: toastError,
  });
}

export function useUpdateEarDevice(patientId: string) {
  const scope = useScope();
  const toastError = useOtologyErrorToast();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: { deviceId: string; body: EarDeviceStatusUpdate }) =>
      updateEarDeviceStatus(input.deviceId, input.body, {
        locale: scope.locale,
        clinicPublicId: scope.clinicPublicId,
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: queryKeys.otology.devices(patientId),
      });
      await queryClient.invalidateQueries({
        queryKey: queryKeys.patients.detail(patientId),
      });
    },
    onError: toastError,
  });
}

export function findingMembers(valueSet: ValueSetRead | undefined) {
  return valueSet?.members ?? [];
}
