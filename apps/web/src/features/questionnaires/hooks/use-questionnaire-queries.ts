"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { queryKeys } from "@/lib/api/query-keys";

import {
  createQuestionnaireInvitation,
  createStaffQuestionnaireResponse,
  fetchPublicQuestionnaireSession,
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
  return useQuery({
    queryKey: queryKeys.questionnaires.patientResponses(patientId, filters),
    queryFn: () =>
      listQuestionnaireResponses(patientId, {
        instrumentCode: filters?.instrumentCode,
        limit: 25,
        offset: 0,
      }),
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
