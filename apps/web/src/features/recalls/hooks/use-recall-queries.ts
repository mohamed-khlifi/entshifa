"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useLocale, useTranslations } from "next-intl";
import { toast } from "sonner";

import {
  bookRecall,
  cancelRecall,
  createRecall,
  fetchRecallSummary,
  fetchRecalls,
  logRecallAction,
} from "../api/recalls.api";
import { recallErrorText } from "../lib/labels";
import { queryKeys } from "@/lib/api/query-keys";
import type {
  RecallActionCreate,
  RecallBook,
  RecallCancel,
  RecallCreate,
} from "@/lib/api/generated";
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

export function useRecallSummaryQuery() {
  const scope = useScope();
  return useQuery({
    queryKey: queryKeys.recalls.summary(),
    queryFn: () =>
      fetchRecallSummary({
        locale: scope.locale,
        clinicPublicId: scope.clinicPublicId,
      }),
    enabled: scope.enabled,
    staleTime: 15_000,
  });
}

export function useRecallListQuery(params: {
  bucket?: string;
  patientId?: string;
  limit: number;
  offset: number;
}) {
  const scope = useScope();
  return useQuery({
    queryKey: queryKeys.recalls.list(params),
    queryFn: () =>
      fetchRecalls(
        { locale: scope.locale, clinicPublicId: scope.clinicPublicId },
        params,
      ),
    enabled: scope.enabled,
    staleTime: 15_000,
  });
}

function useInvalidateRecalls() {
  const queryClient = useQueryClient();
  return async () => {
    await queryClient.invalidateQueries({ queryKey: queryKeys.recalls.all });
    await queryClient.invalidateQueries({ queryKey: queryKeys.patients.all });
  };
}

export function useCreateRecallMutation() {
  const scope = useScope();
  const t = useTranslations("recalls");
  const tErrors = useTranslations("errors");
  const invalidate = useInvalidateRecalls();
  return useMutation({
    mutationFn: (input: { body: RecallCreate; idempotencyKey: string }) =>
      createRecall(
        { locale: scope.locale, clinicPublicId: scope.clinicPublicId },
        input.body,
        input.idempotencyKey,
      ),
    onSuccess: async () => {
      toast.success(t("toast.created"));
      await invalidate();
    },
    onError: (error) => toast.error(recallErrorText(tErrors, error)),
  });
}

export function useLogRecallActionMutation() {
  const scope = useScope();
  const t = useTranslations("recalls");
  const tErrors = useTranslations("errors");
  const invalidate = useInvalidateRecalls();
  return useMutation({
    mutationFn: (input: { recallId: string; body: RecallActionCreate }) =>
      logRecallAction(
        { locale: scope.locale, clinicPublicId: scope.clinicPublicId },
        input.recallId,
        input.body,
      ),
    onSuccess: async () => {
      toast.success(t("toast.logged"));
      await invalidate();
    },
    onError: (error) => toast.error(recallErrorText(tErrors, error)),
  });
}

export function useBookRecallMutation() {
  const scope = useScope();
  const t = useTranslations("recalls");
  const tErrors = useTranslations("errors");
  const invalidate = useInvalidateRecalls();
  return useMutation({
    mutationFn: (input: { recallId: string; body: RecallBook }) =>
      bookRecall(
        { locale: scope.locale, clinicPublicId: scope.clinicPublicId },
        input.recallId,
        input.body,
      ),
    onSuccess: async () => {
      toast.success(t("toast.booked"));
      await invalidate();
    },
    onError: (error) => toast.error(recallErrorText(tErrors, error)),
  });
}

export function useCancelRecallMutation() {
  const scope = useScope();
  const tErrors = useTranslations("errors");
  const invalidate = useInvalidateRecalls();
  return useMutation({
    mutationFn: (input: { recallId: string; body: RecallCancel }) =>
      cancelRecall(
        { locale: scope.locale, clinicPublicId: scope.clinicPublicId },
        input.recallId,
        input.body,
      ),
    onSuccess: async () => {
      await invalidate();
    },
    onError: (error) => toast.error(recallErrorText(tErrors, error)),
  });
}
