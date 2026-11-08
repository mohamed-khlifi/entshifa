"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useLocale } from "next-intl";

import { queryKeys } from "@/lib/api/query-keys";

import {
  createQuestionnaireInvitation,
  createStaffQuestionnaireResponse,
  fetchPublicQuestionnaireSession,
  fetchQuestionnaireResponseDetail,
  listInstruments,
  listQuestionnaireResponses,
  submitPublicQuestionnaire,
} from "../api/questionnaires.api";

export function usePublicQuestionnaireSession(token: string) {
  return useQuery({
    queryKey: queryKeys.questionnaires.publicSession(token),
    queryFn: () => fetchPublicQuestionnaireSession(token),
    retry: false,
  });
}

export function usePatientQuestionnaireResponses(
  patientId: string,
  filters?: { instrumentCode?: string },
) {
  const locale = useLocale();
  return useQuery({
    queryKey: queryKeys.questionnaires.patientResponses(patientId, {
      ...filters,
      locale,
    }),
    queryFn: () =>
      listQuestionnaireResponses(patientId, {
        instrumentCode: filters?.instrumentCode,
        locale,
        limit: 100,
        offset: 0,
      }),
    staleTime: 30_000,
  });
}

export function useQuestionnaireResponseDetail(
  responseId: string | null,
  locale?: string,
) {
  const activeLocale = useLocale();
  const resolved = locale ?? activeLocale;
  return useQuery({
    queryKey: queryKeys.questionnaires.responseDetail(
      responseId ?? "",
      resolved,
    ),
    queryFn: () => fetchQuestionnaireResponseDetail(responseId!, resolved),
    enabled: Boolean(responseId),
    staleTime: 30_000,
  });
}

export function useInstrumentsList() {
  const locale = useLocale();
  return useQuery({
    queryKey: queryKeys.questionnaires.instruments(locale),
    queryFn: () => listInstruments({ locale, limit: 100, offset: 0 }),
    staleTime: 3_600_000,
  });
}

export function useSubmitPublicQuestionnaire(token: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (answers: Record<string, number>) =>
      submitPublicQuestionnaire(token, answers),
    onSuccess: () => {
      void client.invalidateQueries({
        queryKey: queryKeys.questionnaires.publicSession(token),
      });
    },
  });
}

export function useCreateQuestionnaireInvitation(patientId: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (input: Parameters<typeof createQuestionnaireInvitation>[1]) =>
      createQuestionnaireInvitation(patientId, input),
    onSuccess: () => {
      void client.invalidateQueries({
        queryKey: queryKeys.questionnaires.patientInvitations(patientId),
      });
      void client.invalidateQueries({
        queryKey: queryKeys.questionnaires.patientResponses(patientId),
      });
    },
  });
}

export function useStaffQuestionnaireResponse(patientId: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (
      body: Parameters<typeof createStaffQuestionnaireResponse>[1],
    ) => createStaffQuestionnaireResponse(patientId, body),
    onSuccess: () => {
      void client.invalidateQueries({
        queryKey: queryKeys.questionnaires.patientResponses(patientId),
      });
    },
  });
}
