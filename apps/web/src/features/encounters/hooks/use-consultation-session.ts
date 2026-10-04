"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useLocale } from "next-intl";
import { useEffect, useRef, useState } from "react";

import { loadCopyForwardChart, selectCopySource } from "@/features/examination";
import { usePatientQuery } from "@/features/patients";
import type {
  EncounterCopyForward,
  EncounterRead,
  NarrativeFindingIn,
} from "@/lib/api/generated";
import { queryKeys } from "@/lib/api/query-keys";
import { useSession } from "@/providers/session-provider";

import {
  createEncounter,
  fetchCockpitSites,
  fetchComplaintValueSet,
  fetchPatientEncounters,
  renderVisitNarrative,
  routeEncounterTemplate,
} from "../api/encounters.api";

function useScope() {
  const locale = useLocale();
  const { session } = useSession();
  return {
    locale,
    clinicPublicId: session?.clinicPublicId ?? "",
    enabled: Boolean(session?.clinicPublicId),
  };
}

export function useConsultationSession(
  patientId: string,
  encounterId?: string,
) {
  const scope = useScope();
  const queryClient = useQueryClient();
  const patient = usePatientQuery(patientId);
  const encounters = useQuery({
    queryKey: queryKeys.encounters.patient(patientId),
    queryFn: () =>
      fetchPatientEncounters(patientId, {
        locale: scope.locale,
        clinicPublicId: scope.clinicPublicId,
      }),
    enabled: scope.enabled && patientId.length > 0,
    staleTime: 30_000,
  });
  const sites = useQuery({
    queryKey: queryKeys.clinics.sites({ limit: 20 }),
    queryFn: () =>
      fetchCockpitSites({
        locale: scope.locale,
        clinicPublicId: scope.clinicPublicId,
      }),
    enabled: scope.enabled,
    staleTime: 300_000,
  });
  const complaints = useQuery({
    queryKey: queryKeys.terminology.valueSet("complaints.ent"),
    queryFn: () =>
      fetchComplaintValueSet({
        locale: scope.locale,
        clinicPublicId: scope.clinicPublicId,
      }),
    enabled: scope.enabled,
    staleTime: 3_600_000,
  });
  const create = useMutation({
    mutationFn: () => {
      const site =
        sites.data?.items.find((item) => item.isPrimary) ??
        sites.data?.items[0];
      if (!site) {
        throw new Error("site_missing");
      }
      return createEncounter(
        {
          patientPublicId: patientId,
          sitePublicId: site.publicId,
          encounterType: "consultation",
          startedAt: new Date().toISOString(),
        },
        {
          locale: scope.locale,
          clinicPublicId: scope.clinicPublicId,
        },
      );
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: queryKeys.encounters.patient(patientId),
      });
    },
  });
  const [createFailed, setCreateFailed] = useState(false);
  const started = useRef(false);
  const rows = encounters.data?.items ?? [];
  const requested =
    encounterId === undefined
      ? null
      : (rows.find((row) => row.publicId === encounterId) ?? null);
  const draft = rows.find((row) => row.status === "draft") ?? null;
  const active = requested ?? draft;
  const siteCount = sites.data?.items.length ?? 0;

  useEffect(() => {
    if (encounterId || active || createFailed || started.current) {
      return;
    }
    if (!encounters.isSuccess || !sites.isSuccess || !scope.enabled) {
      return;
    }
    if (siteCount === 0) {
      return;
    }
    started.current = true;
    void create.mutateAsync().catch(() => {
      started.current = false;
      setCreateFailed(true);
    });
  }, [
    active,
    create,
    createFailed,
    encounterId,
    encounters.isSuccess,
    scope.enabled,
    siteCount,
    sites.isSuccess,
  ]);

  const needsSite =
    encounters.isSuccess &&
    sites.isSuccess &&
    !active &&
    encounterId === undefined &&
    siteCount === 0;

  return {
    patient,
    encounters,
    complaints,
    active,
    needsSite,
    createFailed,
    loading:
      patient.isLoading ||
      encounters.isLoading ||
      sites.isLoading ||
      complaints.isLoading ||
      create.isPending,
    failed: patient.isError || encounters.isError || createFailed,
    scope,
    copySource: selectCopySource(rows, active?.publicId ?? null),
    recentVisits: [...rows]
      .filter((row) => row.publicId !== active?.publicId)
      .sort((left, right) => right.startedAt.localeCompare(left.startedAt))
      .slice(0, 3),
  };
}

export function useTemplateRoute(
  codes: readonly string[],
  primary: string | null,
) {
  const scope = useScope();
  return useQuery({
    queryKey: queryKeys.encounters.templateRoute(codes, primary),
    queryFn: () =>
      routeEncounterTemplate(
        {
          complaintCodes: [...codes],
          primaryComplaintCode: primary,
        },
        {
          locale: scope.locale,
          clinicPublicId: scope.clinicPublicId,
        },
      ),
    enabled: scope.enabled && codes.length > 0,
    staleTime: 60_000,
  });
}

export function useVisitNarrative(
  patientId: string,
  findings: readonly NarrativeFindingIn[],
) {
  const scope = useScope();
  const signature = JSON.stringify(findings);
  return useQuery({
    queryKey: queryKeys.encounters.narrative(patientId, signature),
    queryFn: () =>
      renderVisitNarrative(
        { findings: [...findings] },
        {
          locale: scope.locale,
          clinicPublicId: scope.clinicPublicId,
        },
      ),
    enabled: scope.enabled && findings.length > 0,
    staleTime: 10_000,
  });
}

export function useCopyVisit(patientId: string) {
  const scope = useScope();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: {
      sourceEncounterId: string;
      body: EncounterCopyForward;
    }) =>
      loadCopyForwardChart(patientId, input.sourceEncounterId, input.body, {
        locale: scope.locale,
        clinicPublicId: scope.clinicPublicId,
      }),
    onSuccess: async (result) => {
      queryClient.setQueryData(
        queryKeys.encounters.patient(patientId),
        (current: { items: EncounterRead[] } | undefined) => {
          if (!current) {
            return current;
          }
          return {
            ...current,
            items: [
              result.encounter,
              ...current.items.filter(
                (row) => row.publicId !== result.encounter.publicId,
              ),
            ],
          };
        },
      );
      await queryClient.invalidateQueries({
        queryKey: queryKeys.encounters.patient(patientId),
      });
    },
  });
}

export { useScope };
