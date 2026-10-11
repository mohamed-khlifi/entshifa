"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useLocale, useTranslations } from "next-intl";
import { toast } from "sonner";

import {
  createOfficeProcedure,
  fetchPatientOfficeProcedures,
  signOfficeProcedure,
  updateOfficeProcedure,
} from "../api/office-procedures.api";
import type {
  OfficeProcedureCreate,
  OfficeProcedureUpdate,
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

function useErrorToast(): (error: unknown) => void {
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

export function usePatientOfficeProcedures(patientId: string) {
  const scope = useScope();
  return useQuery({
    queryKey: queryKeys.officeProcedures.patient(patientId),
    queryFn: () =>
      fetchPatientOfficeProcedures(patientId, {
        locale: scope.locale,
        clinicPublicId: scope.clinicPublicId,
      }),
    enabled: scope.enabled && patientId.length > 0,
    staleTime: RECORD_STALE_MS,
  });
}

export type SaveOfficeProcedureInput = {
  procedureId: string | null;
  createBody: OfficeProcedureCreate;
  updateBody: OfficeProcedureUpdate;
  silent?: boolean;
};

export function useSaveOfficeProcedure(patientId: string) {
  const scope = useScope();
  const t = useTranslations("officeProcedures");
  const toastError = useErrorToast();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: SaveOfficeProcedureInput) => {
      const requestScope = {
        locale: scope.locale,
        clinicPublicId: scope.clinicPublicId,
      };
      if (input.procedureId) {
        return updateOfficeProcedure(
          input.procedureId,
          input.updateBody,
          requestScope,
        );
      }
      return createOfficeProcedure(input.createBody, requestScope);
    },
    onSuccess: async (_row, input) => {
      if (!input.silent) {
        toast.success(t("actions.saved"));
      }
      await queryClient.invalidateQueries({
        queryKey: queryKeys.officeProcedures.patient(patientId),
      });
      await queryClient.invalidateQueries({
        queryKey: queryKeys.recalls.all,
      });
    },
    onError: (error, input) => {
      if (!input.silent) {
        toastError(error);
      }
    },
  });
}

export function useSignOfficeProcedure(patientId: string) {
  const scope = useScope();
  const t = useTranslations("officeProcedures");
  const toastError = useErrorToast();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (procedureId: string) =>
      signOfficeProcedure(
        procedureId,
        { role: "clinician" },
        { locale: scope.locale, clinicPublicId: scope.clinicPublicId },
      ),
    onSuccess: async () => {
      toast.success(t("actions.signed"));
      await queryClient.invalidateQueries({
        queryKey: queryKeys.officeProcedures.patient(patientId),
      });
    },
    onError: toastError,
  });
}
