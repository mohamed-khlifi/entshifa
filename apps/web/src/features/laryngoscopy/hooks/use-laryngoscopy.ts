"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useLocale, useTranslations } from "next-intl";
import { toast } from "sonner";

import {
  createLaryngoscopyExam,
  fetchLaryngoscopyValueSet,
  fetchPatientLaryngoscopies,
  signLaryngoscopyProcedure,
  updateLaryngoscopyExam,
} from "../api/laryngoscopy.api";
import type {
  LaryngoscopyCreate,
  LaryngoscopyUpdate,
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

function useLaryngoscopyErrorToast(): (error: unknown) => void {
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

export function usePatientLaryngoscopies(patientId: string) {
  const scope = useScope();
  return useQuery({
    queryKey: queryKeys.laryngoscopy.patient(patientId),
    queryFn: () =>
      fetchPatientLaryngoscopies(patientId, {
        locale: scope.locale,
        clinicPublicId: scope.clinicPublicId,
      }),
    enabled: scope.enabled && patientId.length > 0,
    staleTime: RECORD_STALE_MS,
  });
}

export function useLaryngoscopyValueSet(code: string) {
  const scope = useScope();
  return useQuery({
    queryKey: queryKeys.examination.valueSet(code, scope.locale),
    queryFn: () =>
      fetchLaryngoscopyValueSet(code, {
        locale: scope.locale,
        clinicPublicId: scope.clinicPublicId,
      }),
    enabled: scope.enabled,
    staleTime: REFERENCE_STALE_MS,
  });
}

export type SaveLaryngoscopyInput = {
  examId: string | null;
  createBody: LaryngoscopyCreate;
  updateBody: LaryngoscopyUpdate;
  silent?: boolean;
};

export function useSaveLaryngoscopy(patientId: string) {
  const scope = useScope();
  const t = useTranslations("laryngoscopy");
  const toastError = useLaryngoscopyErrorToast();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: SaveLaryngoscopyInput) => {
      const requestScope = {
        locale: scope.locale,
        clinicPublicId: scope.clinicPublicId,
      };
      if (input.examId) {
        return updateLaryngoscopyExam(
          input.examId,
          input.updateBody,
          requestScope,
        );
      }
      return createLaryngoscopyExam(input.createBody, requestScope);
    },
    onSuccess: async (exam, input) => {
      if (!input.silent) {
        toast.success(t("actions.saved"));
      }
      await queryClient.invalidateQueries({
        queryKey: queryKeys.laryngoscopy.patient(patientId),
      });
      await queryClient.invalidateQueries({
        queryKey: queryKeys.laryngoscopy.detail(exam.publicId),
      });
    },
    onError: (error, input) => {
      if (!input.silent) {
        toastError(error);
      }
    },
  });
}

export function useSignLaryngoscopy(patientId: string) {
  const scope = useScope();
  const t = useTranslations("laryngoscopy");
  const toastError = useLaryngoscopyErrorToast();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (procedureId: string) =>
      signLaryngoscopyProcedure(
        procedureId,
        { role: "clinician" },
        { locale: scope.locale, clinicPublicId: scope.clinicPublicId },
      ),
    onSuccess: async () => {
      toast.success(t("actions.signed"));
      await queryClient.invalidateQueries({
        queryKey: queryKeys.laryngoscopy.patient(patientId),
      });
    },
    onError: toastError,
  });
}

export function findingMembers(valueSet: ValueSetRead | undefined) {
  return valueSet?.members ?? [];
}
