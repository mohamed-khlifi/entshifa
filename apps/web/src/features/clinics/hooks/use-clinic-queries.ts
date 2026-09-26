"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useLocale } from "next-intl";
import { toast } from "sonner";
import { useTranslations } from "next-intl";

import {
  fetchClinicalSettings,
  fetchCurrentClinic,
  fetchSites,
  updateClinicalSettings,
  updateCurrentClinic,
  createSite,
} from "@/features/clinics/api/clinics.api";
import { queryKeys } from "@/lib/api/query-keys";
import type {
  ClinicalSettingsPut,
  ClinicUpdate,
  SiteCreate,
} from "@/lib/api/generated";
import { useSession } from "@/providers/session-provider";

export function useCurrentClinicQuery() {
  const locale = useLocale();
  const { session } = useSession();
  const clinicPublicId = session?.clinicPublicId;

  return useQuery({
    queryKey: queryKeys.clinics.current(),
    queryFn: () =>
      fetchCurrentClinic(locale, clinicPublicId!),
    enabled: Boolean(clinicPublicId),
    staleTime: 30_000,
  });
}

export function useUpdateClinicMutation() {
  const locale = useLocale();
  const { session } = useSession();
  const queryClient = useQueryClient();
  const t = useTranslations("clinics");

  return useMutation({
    mutationFn: (body: ClinicUpdate) =>
      updateCurrentClinic(body, locale, session!.clinicPublicId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: queryKeys.clinics.current(),
      });
      toast.success(t("profile.saved"));
    },
  });
}

export function useSitesQuery(params?: { limit?: number; offset?: number }) {
  const locale = useLocale();
  const { session } = useSession();

  return useQuery({
    queryKey: queryKeys.clinics.sites(params),
    queryFn: () =>
      fetchSites(locale, session!.clinicPublicId, params),
    enabled: Boolean(session?.clinicPublicId),
  });
}

export function useCreateSiteMutation() {
  const locale = useLocale();
  const { session } = useSession();
  const queryClient = useQueryClient();
  const t = useTranslations("clinics");

  return useMutation({
    mutationFn: (body: SiteCreate) =>
      createSite(body, locale, session!.clinicPublicId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: queryKeys.clinics.all,
      });
      toast.success(t("sites.created"));
    },
  });
}

export function useClinicalSettingsQuery() {
  const locale = useLocale();
  const { session } = useSession();

  return useQuery({
    queryKey: queryKeys.clinics.clinicalSettings(),
    queryFn: () => fetchClinicalSettings(locale, session!.clinicPublicId),
    enabled: Boolean(session?.clinicPublicId),
  });
}

export function useUpdateClinicalSettingsMutation() {
  const locale = useLocale();
  const { session } = useSession();
  const queryClient = useQueryClient();
  const t = useTranslations("clinics");

  return useMutation({
    mutationFn: (body: ClinicalSettingsPut) =>
      updateClinicalSettings(body, locale, session!.clinicPublicId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: queryKeys.clinics.clinicalSettings(),
      });
      toast.success(t("clinical.saved"));
    },
  });
}
