"use client";

import { useMemo } from "react";
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
  deletePatientAllergy,
  deletePatientHistory,
  deletePatientIdentifier,
  deletePatientMedication,
  deletePatientProblem,
  fetchConceptDictionary,
  fetchPatient,
  fetchPatientTimeline,
  fetchPatients,
  fetchValueSet,
  searchConcepts,
  updatePatientFlag,
  type PatientListParams,
} from "../api/patients.api";
import {
  conceptOptionsFromDictionary,
  filterConceptOptions,
  type ConceptOption,
} from "../lib/concept-picker-options";
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

type ApiScope = { locale: string; clinicPublicId: string };

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
    staleTime: 60_000,
    gcTime: 5 * 60_000,
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

export type ConceptPickerParams = {
  kind?: string;
  kinds?: string[];
  valueSetCode?: string;
};

export function useConceptPickerOptions(
  query: string,
  params: ConceptPickerParams = {},
) {
  const scope = useScope();
  const term = query.trim();
  const kinds =
    params.kinds?.join(",") ?? (params.kind ? params.kind : undefined);

  const browse = useQuery({
    queryKey: queryKeys.terminology.dictionary({
      locale: scope.locale,
      kinds,
      valueSet: params.valueSetCode,
    }),
    queryFn: async (): Promise<ConceptOption[]> => {
      const requestScope = {
        locale: scope.locale,
        clinicPublicId: scope.clinicPublicId,
      };
      if (params.valueSetCode) {
        const valueSet = await fetchValueSet(params.valueSetCode, requestScope);
        return valueSet.members.map((item) => ({
          publicId: item.publicId,
          display: item.display,
        }));
      }
      const dictionary = await fetchConceptDictionary(requestScope, kinds);
      return conceptOptionsFromDictionary(dictionary.concepts);
    },
    enabled: scope.enabled,
    staleTime: 300_000,
  });

  const search = useQuery({
    queryKey: queryKeys.terminology.search({
      q: term,
      locale: scope.locale,
      kind: params.kind,
    }),
    queryFn: () =>
      searchConcepts(
        { locale: scope.locale, clinicPublicId: scope.clinicPublicId },
        { q: term, kind: params.kind },
      ),
    enabled: scope.enabled && term.length >= 1,
    staleTime: 120_000,
    placeholderData: (previous) => previous,
  });

  return useMemo(() => {
    if (term.length >= 1) {
      const items = search.data?.items ?? [];
      return {
        items: items.map((item) => ({
          publicId: item.publicId,
          display: item.display,
        })),
        isFetching: search.isFetching,
        isLoading: search.isLoading,
      };
    }
    const browsed = browse.data ?? [];
    return {
      items: filterConceptOptions(browsed, term),
      isFetching: browse.isFetching,
      isLoading: browse.isLoading,
    };
  }, [
    browse.data,
    browse.isFetching,
    browse.isLoading,
    search.data,
    search.isFetching,
    search.isLoading,
    term,
  ]);
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

function useDeleteChartItemMutation(
  deleteFn: (patientId: string, itemId: string, scope: ApiScope) => Promise<void>,
) {
  const scope = useScope();
  const queryClient = useQueryClient();
  const t = useTranslations("patients");
  const onError = useChartErrorToast();
  return useMutation({
    mutationFn: (input: { patientId: string; itemId: string }) =>
      deleteFn(input.patientId, input.itemId, {
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

export function useDeleteIdentifierMutation() {
  return useDeleteChartItemMutation(deletePatientIdentifier);
}

export function useDeleteAllergyMutation() {
  return useDeleteChartItemMutation(deletePatientAllergy);
}

export function useDeleteMedicationMutation() {
  return useDeleteChartItemMutation(deletePatientMedication);
}

export function useDeleteProblemMutation() {
  return useDeleteChartItemMutation(deletePatientProblem);
}

export function useDeleteHistoryMutation() {
  return useDeleteChartItemMutation(deletePatientHistory);
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
