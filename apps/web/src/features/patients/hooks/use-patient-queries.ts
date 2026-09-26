"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useLocale, useTranslations } from "next-intl";
import { toast } from "sonner";

import {
  addPatientAllergy,
  addPatientFlag,
  addPatientHistory,
  addPatientIdentifier,
  addPatientMedication,
  addPatientProblem,
  fetchPatient,
  fetchPatientTimeline,
  fetchPatients,
  searchConcepts,
  updatePatientFlag,
  type PatientListParams,
} from "../api/patients.api";
import type {
  PatientAllergyCreate,
  PatientFlagCreate,
  PatientFlagUpdate,
  PatientHistoryCreate,
  PatientIdentifierCreate,
  PatientMedicationCreate,
  PatientProblemCreate,
} from "@/lib/api/generated";
import { ApiError, resolveErrorMessage } from "@/lib/api/errors";
import { queryKeys } from "@/lib/api/query-keys";
import { useSession } from "@/providers/session-provider";

function useChartErrorToast(): (error: unknown) => void {
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

function useScope() {
  const locale = useLocale();
  const { session } = useSession();
  return {
    locale,
    clinicPublicId: session?.clinicPublicId ?? "",
    enabled: Boolean(session?.clinicPublicId),
  };
}

export function usePatientsQuery(params: PatientListParams) {
  const scope = useScope();
  return useQuery({
    queryKey: queryKeys.patients.list(params),
    queryFn: () =>
      fetchPatients(
        { locale: scope.locale, clinicPublicId: scope.clinicPublicId },
        params,
      ),
    enabled: scope.enabled,
    staleTime: 30_000,
  });
}

export function usePatientQuery(patientId: string) {
  const scope = useScope();
  return useQuery({
    queryKey: queryKeys.patients.detail(patientId),
    queryFn: () =>
      fetchPatient(patientId, {
        locale: scope.locale,
        clinicPublicId: scope.clinicPublicId,
      }),
    enabled: scope.enabled && patientId.length > 0,
    staleTime: 30_000,
  });
}

export function usePatientTimelineQuery(patientId: string) {
  const scope = useScope();
  return useQuery({
    queryKey: queryKeys.patients.timeline(patientId),
    queryFn: () =>
      fetchPatientTimeline(patientId, {
        locale: scope.locale,
        clinicPublicId: scope.clinicPublicId,
      }),
    enabled: scope.enabled && patientId.length > 0,
    staleTime: 30_000,
  });
}

export function useConceptSearchQuery(q: string) {
  const scope = useScope();
  const term = q.trim();
  return useQuery({
    queryKey: queryKeys.terminology.search({
      q: term,
      locale: scope.locale,
    }),
    queryFn: () =>
      searchConcepts(
        { locale: scope.locale, clinicPublicId: scope.clinicPublicId },
        { q: term },
      ),
    enabled: scope.enabled && term.length >= 2,
    staleTime: 60_000,
  });
}

function useChartMutation<TBody>(
  mutate: (
    patientId: string,
    body: TBody,
    scope: { locale: string; clinicPublicId: string },
    idempotencyKey: string,
  ) => Promise<unknown>,
) {
  const scope = useScope();
  const queryClient = useQueryClient();
  const t = useTranslations("patients");
  const onError = useChartErrorToast();
  return useMutation({
    mutationFn: (input: { patientId: string; body: TBody }) =>
      mutate(
        input.patientId,
        input.body,
        { locale: scope.locale, clinicPublicId: scope.clinicPublicId },
        crypto.randomUUID(),
      ),
    onSuccess: async (_data, input) => {
      await queryClient.invalidateQueries({
        queryKey: queryKeys.patients.detail(input.patientId),
      });
      toast.success(t("chart.saved"));
    },
    onError,
  });
}

export function useAddIdentifierMutation() {
  return useChartMutation<PatientIdentifierCreate>(addPatientIdentifier);
}

export function useAddAllergyMutation() {
  return useChartMutation<PatientAllergyCreate>(addPatientAllergy);
}

export function useAddMedicationMutation() {
  return useChartMutation<PatientMedicationCreate>(addPatientMedication);
}

export function useAddFlagMutation() {
  return useChartMutation<PatientFlagCreate>(addPatientFlag);
}

export function useAddProblemMutation() {
  return useChartMutation<PatientProblemCreate>(addPatientProblem);
}

export function useAddHistoryMutation() {
  return useChartMutation<PatientHistoryCreate>(addPatientHistory);
}

export function useEndFlagMutation() {
  const scope = useScope();
  const queryClient = useQueryClient();
  const t = useTranslations("patients");
  const onError = useChartErrorToast();
  return useMutation({
    mutationFn: (input: {
      patientId: string;
      flagId: string;
      body: PatientFlagUpdate;
    }) =>
      updatePatientFlag(input.patientId, input.flagId, input.body, {
        locale: scope.locale,
        clinicPublicId: scope.clinicPublicId,
      }),
    onSuccess: async (_data, input) => {
      await queryClient.invalidateQueries({
        queryKey: queryKeys.patients.detail(input.patientId),
      });
      toast.success(t("chart.saved"));
    },
    onError,
  });
}
